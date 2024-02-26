import discord
import asyncio
import spotipy
import os
import json
import subprocess
import datetime
import yt_dlp as youtube_dl
from .config import *
from discord.ext import commands, tasks
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv
from googleapiclient.discovery import build
from urllib.parse import urlparse, parse_qs

load_dotenv(dotenv_path= r"C:\Users\absol\Desktop\python\DIABETESBOT\res\.env")

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)
bot = commands.Bot(command_prefix='-', intents=intents)
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=os.getenv('SPOTIFY_CLIENT_ID'), client_secret=os.getenv('SPOTIFY_CLIENT_SECRET')))

queue = []
top_songs = []
now_playing = ""

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')

    @classmethod
    async def from_url(self, url, *, loop, stream=False, spotify_url=None):
        cached_path = self.check_url_in_cache(url)
        if cached_path:
            filename, title = cached_path
            data = {'title': title}
            return self(discord.FFmpegPCMAudio(filename), data=data)
        elif stream:
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))
            if data is None:
                return None
            filename = data['url']
            return self(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)
        else:
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=True))
            if data is None:
                return None
            filename = ytdl.prepare_filename(data)
            print(filename)
            if spotify_url:
                await self.update_json_cache(spotify_url, filename, data.get('title'))
            else:
                await self.update_json_cache(url, filename, data.get('title'))
            return self(discord.FFmpegPCMAudio(filename), data=data)
    
    @staticmethod
    def check_url_in_cache(url):
        try:
            with open(rf'{jsons_path}\cache.json', 'r') as r:
                cache = json.load(r)
        except (FileNotFoundError, json.JSONDecodeError):
            cache = {}
        if url in cache:
            cache[url][2] = datetime.datetime.now().strftime("%Y-%m-%d")
            with open(rf'{jsons_path}\cache.json', "w") as w:
                json.dump(cache, w, indent=4)
            return (cache[url][0], cache[url][1])
        return None

    
    @staticmethod
    async def update_json_cache(url, path, title):
        with open(rf'{jsons_path}\cache.json', 'r') as f:
            cache = json.load(f)
        # print(f"cache is: {cache}")
        # print(f"url: {url}, path: {path}")
        cache[url] = [path, title, datetime.datetime.now().strftime("%Y-%m-%d")]

        with open(rf'{jsons_path}\cache.json', 'w') as f:
            json.dump(cache, f, indent=4)


from . import bot_commands