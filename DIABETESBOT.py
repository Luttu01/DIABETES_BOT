from . import bot, os, top_songs
from .helper_functions import fetch_top_songs

if __name__ == "__main__":
    bot.run(os.getenv('DISCORD_BOT_TOKEN'))