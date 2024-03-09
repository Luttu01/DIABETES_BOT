from . import discord, os, Path

jsons_path = r'C:\Users\absol\Desktop\python\DIABETESBOT\res'
cache_path = r'C:\Users\absol\Desktop\python\DIABETESBOT\cache'
json_cache_file = os.path.join(cache_path, r'C:\Users\absol\Desktop\python\DIABETESBOT\res\cache.json')

PATH = 0
TITLE = 1
LAST_ACCESSED = 2

ytdl_format_options = {
    'format': 'bestaudio/best',
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
    'audioformat': 'mp3',
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

log_file_path = Path(r"C:\Users\absol\Desktop\python\DIABETESBOT\logs\bot.log")