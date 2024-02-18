import discord
import asyncio
import spotipy
import os
import json
import yt_dlp as youtube_dl
from .config import *
from discord.ext import commands, tasks
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv
from googleapiclient.discovery import build
from urllib.parse import urlparse, parse_qs

load_dotenv(dotenv_path= r"C:\Users\absol\Desktop\python\DIABETESBOT\.env")

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
    async def from_url(cls, url, *, loop, stream=False):
        ytdl_format_options['playlist_items'] = '1'
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if data is None:
            return None
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


from . import bot_commands