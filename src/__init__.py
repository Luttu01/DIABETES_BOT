import discord
import asyncio
import spotipy
import os
import json
import subprocess
import datetime
import logging
import random
import isodate
import yt_dlp as youtube_dl
from .config import *
from discord.ext import commands, tasks
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv
from googleapiclient.discovery import build
from urllib.parse import urlparse, parse_qs, urlunparse

load_dotenv(dotenv_path=denv_path)

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)
bot = commands.Bot(command_prefix='-', intents=intents, case_insensitive=True)
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=os.getenv('SPOTIFY_CLIENT_ID'), client_secret=os.getenv('SPOTIFY_CLIENT_SECRET')))

queue = []
song_duration = 0
now_playing = None
current_player = None
silence_bool = True
idle_count = 0

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, url, volume=0.5, duration=None):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = url
        self.duration = duration

    @classmethod
    async def from_url(self, url, *, loop, stream=False, spotify_url=None, duration=None):
        cached_path = self.check_url_in_cache(url)
        if cached_path:
            filename, title, volume, duration = cached_path
            if not duration:
                pass

            if spotify_url:
                return self(discord.FFmpegPCMAudio(filename), data={'title': title}, url=spotify_url, volume=volume, duration=duration)
            else:
                return self(discord.FFmpegPCMAudio(filename), data={'title': title}, url=url, volume=volume, duration=duration)
        elif stream:
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))
            # data = ytdl.extract_info(url, download=False)
            logging.debug(f"data is {data!r}")
            if data is None:
                return None
            # filename = data['formats'][0]['url']
            filename = data['original_url']
            logging.debug(data)
            return self(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data, url=url)
        else:
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=True))
            if data is None:
                return None
            filename = ytdl.prepare_filename(data)
            # logging.debug(data)
            logging.debug(data['duration'])
            if spotify_url:
                await self.update_json_cache(spotify_url, filename, data.get('title'), duration=data['duration'])
                return self(discord.FFmpegPCMAudio(filename), data=data, url=spotify_url, duration=data['duration'])
            else:
                await self.update_json_cache(url, filename, data.get('title'), duration=data['duration'])
                return self(discord.FFmpegPCMAudio(filename), data=data, url=url, duration=data['duration'])
    
    @staticmethod
    def check_url_in_cache(url):
        try:
            with open(rf'{res_path}\cache.json', 'r') as r:
                cache = json.load(r)
        except (FileNotFoundError, json.JSONDecodeError):
            cache = {}
        if url in cache.keys():
            cache[url]['last_accessed'] = datetime.datetime.now().strftime("%Y-%m-%d")
            with open(rf'{res_path}\cache.json', "w") as w:
                json.dump(cache, w, indent=4)
            return (cache[url]['path'], cache[url]['title'], cache[url]['volume'], None) if not 'duration' in cache[url] else \
                   (cache[url]['path'], cache[url]['title'], cache[url]['volume'], cache[url]['duration'])
        return None

    @staticmethod
    async def update_json_cache(url, path, title, duration):
        with open(rf'{res_path}\cache.json', 'r') as f:
            cache = json.load(f)

        def _new_cache_entry(path, title, last_accessed, duration):
            return {
                'path': path,
                'title': title,
                'last_accessed': last_accessed,
                'weight': 1,
                'volume': 0.5,
                'duration': duration
            }
        
        cache[url] = _new_cache_entry(path, title, datetime.datetime.now().strftime("%Y-%m-%d"), duration)

        with open(rf'{res_path}\cache.json', 'w') as f:
            json.dump(cache, f, indent=4)
    
    @staticmethod
    async def get_video_duration(url):
        if 'spotify' in url:
            url = get_youtube_link(url)
        



from . import bot_commands