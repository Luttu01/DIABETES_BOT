from . import bot, os

if __name__ == "__main__":
    bot.run(os.getenv('DISCORD_BOT_TOKEN'))