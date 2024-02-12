import random
from .helper_functions import *


@bot.command(name='join', help='Tells the bot to join the voice channel')
async def join(ctx):
    if not ctx.message.author.voice:
        await ctx.send("You are not connected to a voice channel")
        return
    
    sort_counter()
    # top_songs = await fetch_top_songs(ctx)

    channel = ctx.message.author.voice.channel
    await channel.connect()

    if not play_next_song.is_running():
        play_next_song.start(ctx)


@bot.command(name='play', help='Plays a song from YouTube')
@is_author_in_voice_channel()
async def play(ctx, query, flag=None):
    if not ctx.voice_client:
        await join(ctx)
    
    if not assert_url(query) and not assert_alias(query):
        await ctx.send("Not a valid url.")
        return

    async with ctx.typing():
        if query in get_aliases():
            url = get_url_from_alias(query)

        elif 'playlist' in query and "spotify" in query:
            try:
                tracks = get_spotify_playlist_tracks(query)
                playlist_name = get_spotify_playlist_name(query)
                for track in tracks:
                    url = await get_youtube_link(track)
                    player = await get_player(ctx, url)
                    queue.append(player)
                await ctx.send(f"added to queue: {playlist_name}")
                return
            except youtube_dl.DownloadError as e:
                await ctx.send("There was an error processing your request. Please try a different URL or check the URL format.")
                print(e)
        else:
            url = query
        
        try:
            player = await get_player(ctx, url)
            if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
                queue.append(player)
                await ctx.send(f'Added to queue: {player.title}, at position {len(queue)}')
            else:
                ctx.voice_client.play(player, after=lambda e: None)
                await ctx.send(f'Now playing: {player.title}')
            
            if flag != '-t':
                update_url_counter(url, player.title)
                update_request_counter(ctx.author.name)
            
        except youtube_dl.DownloadError as e:
            await ctx.send("There was an error processing your request. Please try a different URL or check the URL format.")
            print(e)


@bot.command(name='skip', help='Skips the currently playing song')
@is_author_in_voice_channel()
async def skip(ctx):
    if not ctx.voice_client or not ctx.voice_client.is_playing():
        await ctx.send("No song is currently playing.")
        return

    ctx.voice_client.stop()
    await ctx.send("Skipped the song.")

    await check_queue(ctx)


@bot.command(name='leave', help='To make the bot leave the voice channel')
@is_author_in_voice_channel()
async def leave(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_connected():
        queue.clear()
        await voice_client.disconnect()
        play_next_song.stop()
    else:
        await ctx.send("The bot is not connected to a voice channel.")


@bot.command(name='shuffle', help='Shuffles the current playlist')
@is_author_in_voice_channel()
async def shuffle(ctx):
    if len(queue) > 1:

        random.shuffle(queue)

        await ctx.send("Queue has been shuffled.")
    else:
        await ctx.send("Not enough songs in the queue to shuffle.")


@bot.command(name='remove', help='Remove first, or given song from queue')
@is_author_in_voice_channel()
async def remove(ctx, position: int = 1):
    if len(queue) > 0:
        # Validate position
        if 1 <= position <= len(queue):
            # Remove song at the given position (adjust for 0-based index)
            removed_song = queue.pop(position - 1)
            print(queue)
            await ctx.send(f"Removed song number {position}: {removed_song.title}")
        else:
            await ctx.send(f"Invalid position: {position}. Queue size is {len(queue)}.")
    else:
        await ctx.send("The queue is currently empty.")


@bot.command(name='queue', help='Displays the next 5 songs in the queue')
@is_author_in_voice_channel()
async def show_queue(ctx):
    if len(queue) == 0:
        await ctx.send("The queue is currently empty.")
        return

    # Display message for the next 5 songs or total songs if less than 5
    next_songs_count = min(5, len(queue))
    message = f"These are the next {next_songs_count} songs, of {len(queue)} total:\n"
    for i, song in enumerate(queue[:5], 1):
        message += f"{i}. {song.title}\n"

    await ctx.send(message)


@bot.command(name='move', help='Move a song in the queue to a new position')
@is_author_in_voice_channel()
async def move(ctx, from_position: int, to_position: int = 1):
    if len(queue) >= from_position > 0:
        # Adjust for 0-based indexing
        from_index = from_position - 1
        to_index = to_position - 1 if to_position > 0 else 0

        # Ensure the to_index is within bounds
        to_index = min(to_index, len(queue) - 1)

        # Perform the move operation
        song = queue.pop(from_index)
        queue.insert(to_index, song)

        if from_position != to_position:
            await ctx.send(f"Moved song from position {from_position} to {to_position}.")
        else:
            await ctx.send(f"Moved song to the front of the queue.")
    else:
        await ctx.send("Invalid position. Please check the queue and try again.")


@bot.command(name="die", help='Terminates the bot')
async def die(ctx):
    if str(ctx.author.id) == os.getenv("DISCORD_LUTTU_TOKEN"):
        await ctx.send("Hörs på byn")
        await bot.close()
    else:
        await ctx.send("You lack permission, try -leave instead if you want me gone.")


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')


@bot.command(name="topsongs", help="Prints top 10 requested songs")
@is_author_in_voice_channel()
async def topsongs(ctx):
    try:
        top_songs = await fetch_top_songs(ctx)
        if not top_songs:
            await ctx.send("no songs to display")
            return
        await ctx.send("Top 10 requested songs are: ")
        for title, count in top_songs:
            await ctx.send(f"Song: {title}, requested: {count} times.")
    except Exception as e:
        print(f"Error in topsongs command: {e}")
        await ctx.send("An error occurred while fetching the top songs.")


@bot.command(name="alias", help="Sets given url to given alias")
@is_author_in_voice_channel()
async def alias(ctx, url, new_name):
    if not assert_url(url):
        await ctx.send("Invalid url; make sure to send a valid youtube, spotify, or soundcloud link.")
        return
    success = add_alias(url, new_name)
    if not success:
        existing_alias = get_alias_from_url(url)
        await ctx.send(f"That song already exists with alias: {existing_alias}")
    else:
        await ctx.send(f"Successfully added alias: {new_name}")
    

@bot.command(name="rmalias", help="remove given alias")
@is_author_in_voice_channel()
async def rmalias(ctx, alias):
    print(alias)
    if not assert_alias(alias):
        await ctx.send("Not an existing alias")
        return
    success = remove_alias(alias)
    if success:
        await ctx.send(f"Successfully removed alias: {alias}")


@bot.command(name="aliases", help="Shows existing aliases")
@is_author_in_voice_channel()
async def aliases(ctx):
    aliases_list = get_aliases()
    items_per_page = 10  # Adjust the number of items per page as needed
    pages = [aliases_list[i:i + items_per_page] for i in range(0, len(aliases_list), items_per_page)]
    current_page = 0

    if not pages:  # If there are no aliases to display
        await ctx.send("No aliases found.")
        return

    # Send the initial message with the first page of aliases
    message = await ctx.send(f"**Aliases (Page {current_page + 1}/{len(pages)}):**\n" + '\n'.join(pages[current_page]))

    # Add navigation reactions
    await message.add_reaction('⬅️')
    await message.add_reaction('➡️')

    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in ['⬅️', '➡️'] and reaction.message.id == message.id

    while True:
        try:
            reaction, user = await bot.wait_for('reaction_add', timeout=60.0, check=check)

            # Navigate pages
            if str(reaction.emoji) == '➡️' and current_page < len(pages) - 1:
                current_page += 1
            elif str(reaction.emoji) == '⬅️' and current_page > 0:
                current_page -= 1
            else:
                await message.remove_reaction(reaction, user)
                continue

            # Edit the message for the new page
            await message.edit(content=f"**Aliases (Page {current_page + 1}/{len(pages)}):**\n" + '\n'.join(pages[current_page]))
            await message.remove_reaction(reaction, user)
        except asyncio.TimeoutError:
            await message.clear_reactions()
            break