import discord
import asyncio
import spotipy
import os
import json
import subprocess
import datetime
import logging
import random
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
top_songs = []
now_playing = None
current_player = None
silence_bool = True
idle_count = 0

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, url, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = url

    @classmethod
    async def from_url(self, url, *, loop, stream=False, spotify_url=None):
        cached_path = self.check_url_in_cache(url)
        if cached_path:
            filename, title, volume = cached_path
            if spotify_url:
                return self(discord.FFmpegPCMAudio(filename), data={'title': title}, url=spotify_url, volume=volume)
            else:
                return self(discord.FFmpegPCMAudio(filename), data={'title': title}, url=url, volume=volume)
        elif stream:
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))
            if data is None:
                return None
            filename = data['url']
            return self(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data, url=url)
        else:
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=True))
            if data is None:
                return None
            filename = ytdl.prepare_filename(data)
            if spotify_url:
                await self.update_json_cache(spotify_url, filename, data.get('title'))
                return self(discord.FFmpegPCMAudio(filename), data=data, url=spotify_url)
            else:
                await self.update_json_cache(url, filename, data.get('title'))
                return self(discord.FFmpegPCMAudio(filename), data=data, url=url)
    
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
            return (cache[url]['path'], cache[url]['title'], cache[url]['volume'])
        return None

    @staticmethod
    async def update_json_cache(url, path, title):
        with open(rf'{res_path}\cache.json', 'r') as f:
            cache = json.load(f)

        def _new_cache_entry(path, title, last_accessed):
            return {
                'path': path,
                'title': title,
                'last_accessed': last_accessed,
                'weight': 1,
                'volume': 0.5
            }
        
        cache[url] = _new_cache_entry(path, title, datetime.datetime.now().strftime("%Y-%m-%d"))

        with open(rf'{res_path}\cache.json', 'w') as f:
            json.dump(cache, f, indent=4)
    



from . import bot_commands