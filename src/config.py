from . import discord, os

jsons_path = r'C:\Users\absol\Desktop\python\DIABETESBOT\res'
cache_path = r'C:\Users\absol\Desktop\python\DIABETESBOT\cache'
json_cache_file = os.path.join(cache_path, r'C:\Users\absol\Desktop\python\DIABETESBOT\res\cache.json')

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

current_commands = ["join", "play", "skip", "leave", "shuffle", "remove", "queue", "move", "die", "topsongs", "alias", "rmalias", "aliases", "np", "commands"]

