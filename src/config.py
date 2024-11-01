from . import discord, os
import logging

# Paths
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

res_path   = os.path.join(parent_dir, "res")
cache_path = os.path.join(parent_dir, "cache")
logs_path  = os.path.join(parent_dir, "logs", "bot.log")

json_cache_file     = os.path.join(res_path, "cache.json")
json_tags_path      = os.path.join(res_path, "tags.json")
json_to_remove_path = os.path.join(res_path, "to_remove.json")
json_blacklist_path = os.path.join(res_path, "blacklist.json")

denv_path = os.path.join(parent_dir, "res", ".env")

# Logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - [%(funcName)s] - %(levelname)s - %(message)s', filename=logs_path)

ytdl_format_options = {
    'outtmpl': cache_path + r'\%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'verbose': True,
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': True,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',  # bind to ipv4 since ipv6 addresses cause issues sometimes
    # 'audioformat': 'mp3',
    # 'postprocessors': [{
    #     'key': 'FFmpegExtractAudio',
    #     'preferredcodec': 'mp3',
    #     'preferredquality': '192',
    # }],
    'extractaudio': True
}

ffmpeg_options = {
    'options': '-vn',
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
}

# Define intents
intents = discord.Intents.default()
intents.guilds = True
intents.voice_states = True
intents.message_content = True
