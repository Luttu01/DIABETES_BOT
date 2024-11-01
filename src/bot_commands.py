import time
import rapidfuzz
from .helper_functions import *


@bot.event
async def on_ready():

    clear_logs()
    reset_weighting()
    set_silence(True)
    # reformat_cache()

    logging.info('Starting bot...')

    # logging.debug('Sorting cache.')
    # cache_start_time = time.time()
    # print("sorting cache", end="", flush=True)
    # sort_cache()
    # print(f"\rsorting cache took: {time.time()-cache_start_time} seconds", flush=True)
    # logging.debug('Finished sorting cache.')

    logging.debug('Sorting url counter.')
    counter_start_time = time.time()
    print("sorting counter", end="", flush=True)
    sort_counter()
    print(f"\rsorting counters took: {time.time()-counter_start_time} seconds", flush=True )
    logging.debug('Finished sorting url counter.')

    logging.debug('Removing doomed urls.')
    remove_doomed_urls()
    logging.debug('Finished removing doomed urls.')

    print(f'Logged in as {bot.user.name}')

    logging.info('Bot launched.')

@bot.command(name='join', help='Tells the bot to join the voice channel')
async def join(ctx):
    if not ctx.message.author.voice:
        await ctx.send("You are not connected to a voice channel")
        return

    channel = ctx.message.author.voice.channel
    await channel.connect()

    if not play_next_song.is_running():
        play_next_song.start(ctx)


@tasks.loop(seconds=1.0)
async def play_next_song(ctx):
    duration_seek()
    if ctx.voice_client:
        if not ctx.voice_client.is_playing() and not ctx.voice_client.is_paused():
            if queue:
                next_song = queue.pop(0)
                if next_song is None:
                    await ctx.send("Problem with this song, skipping to next one")
                    await play_next_song(ctx)
                else:
                    ctx.voice_client.play(next_song)
                    set_current_player(next_song)
                    set_np(next_song.title)
                    set_duration(0)
                    await ctx.send(f'--- Now playing: {next_song.title} ---')
            else:
                if not get_silence_bool():
                    await play_random(ctx)
    # logging.debug(f"get duration: {get_duration()}")


@bot.command(name='play', aliases=['p', "pl", "pla", "spela"], help='Plays a given url (youtube, spotify, soundcloud) or alias')
async def play(ctx, query: str, *flags, **kw):
    try:
        assert ctx != None
    except AssertionError:
        print("Context is none, aborting play request\n"*10)
        return

    if not ctx.voice_client:
        await join(ctx)

    if ctx.author.name not in get_spoofed_users():
        spoof_user(ctx.author.name, ctx.author.id)

    if ctx.author.id == os.getenv("DISCORD_ZIGENARE_TOKEN"):
        await ctx.send("lol bög du får inte spela låtar")
        return

    logging.debug(f"flags: {flags}")
    
    mtag = extract_mtag(flags)
    print(f"extracted mtag: {mtag}")
    
    query_lower = query.lower()
    start_time  = time.time()
    finished    = lambda: time.time() - start_time  

    if not assert_url(query) and not assert_alias(query_lower):
        best_match, score = rapidfuzz.process.extractOne(query_lower, get_aliases(), scorer=rapidfuzz.fuzz.WRatio)[:2]
        print(best_match)
        print(score)
        if score >= 80:
            print(f"best alias match: {best_match}")
            await ctx.send(f"Your query matched '{best_match}' by {float(score):.1f}%")
            query = best_match
        else:
            await ctx.send("Invalid url.")
            return

    async with ctx.typing():
        if query in get_aliases():
            url = get_url_from_alias(query)

        elif 'playlist' in query and "spotify" in query:
            try:
                await ctx.send("Processing playlist, you can queue other songs meanwhile.")
                playlist_name, failures = await process_spotify_playlist(query)
                await ctx.send(f"**Added {playlist_name!r} to the queue. Failed to load {failures} songs.**")
                print(f"time: {finished()}")
                return
            except youtube_dl.DownloadError as e:
                await ctx.send("There was an error processing your request. Please try a different URL or check the URL format.")
                print(e)

        elif 'album' in query and 'spotify' in query:
            await ctx.send("Processing album, you can queue other songs meanwhile.")
            album_name, failures = await process_spotify_album(query)
            await ctx.send(f"**Added {album_name!r} to the queue. Failed to load {failures} songs.**")
            print(f"time: {finished()}")
            return
        
        elif 'playlist' in query and "youtube" in query:
            try:
                if '-d' in flags and mtag:
                    stream = False
                else:
                    stream = True
                await ctx.send("Processing playlist, you can queue other songs meanwhile.")
                logging.debug(f"query is {query!r}"); logging.debug(f"stream is {stream!r}"); logging.debug(f"mtag is {mtag!r}")
                playlist_name, failures = await process_yt_playlist(query, stream, mtag)
                await ctx.send(f"**Added {playlist_name!r} to the queue. Failed to load {failures} songs.**")
                print(f"time: {finished()}")
                return
            except youtube_dl.DownloadError as e:
                await ctx.send("There was an error processing your request. Please try a different URL or check the URL format.")
                print(e)

        else:
            url = query
        
        try:
            player = await get_player(url)
            # logging.debug(f"player is: {player!r}")

            if player is None:
                await ctx.send("Problem downloading the song, assert the url is valid.")
                return
            if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
                add_to_q(player)
                await ctx.send(f'**Added to queue: {player.title!r}, at position {len(queue)}**')
            else:
                ctx.voice_client.play(player, after=lambda e: None)
                await ctx.send(f'--- Now playing: {player.title} ---')
                
                set_current_player(player)
                set_np(player.title)
                set_duration(0)
                logging.debug(get_duration())
                print(f"np is now: {player.title}")

        except youtube_dl.DownloadError as e:
            await ctx.send("There was an error processing your request. Please try a different URL or check the URL format.")
            print(e)

        if '-t' not in flags:
            print("updating counters.")
            logging.info('Updating counters.')
            update_url_counter(url, player.title)
            update_request_counter(ctx.author.name)
        
        if mtag:
            existing_tag = add_tag(player.url, mtag)
            if existing_tag:
                await ctx.send(f"That song already has the tag: {existing_tag}")
            else:
                await ctx.send(f"Successfully added the tag: {mtag!r}")

        if flags and not mtag and '-t' not in flags:
            await ctx.send("That tag doesn't exist.")
            return

        print(f"time: {finished()}")
            
        

@bot.command(name='skip', aliases=["s", "sk", "ski", "nästa", "hoppa"], help='Skips the currently playing song')
@is_author_in_voice_channel()
async def skip(ctx):
    if not ctx.voice_client or not ctx.voice_client.is_playing():
        await ctx.send("No song is currently playing.")
        return
    
    if who := str(ctx.author.id) == os.getenv('DISCORD_VICTOR_TOKEN'):
        if check_allowed_to_skip(who, get_current_player_url()):
            pass
        else:
            await ctx.send("You lack privilege to skip this song.")
            return
        

    ctx.voice_client.stop()
    await ctx.send(f"Skipped the song: {get_np()}.")

    await check_queue(ctx)


@bot.command(name='leave', aliases=["lämna"], help='To make the bot leave the voice channel')
async def leave(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client.is_connected():
        queue.clear()
        await voice_client.disconnect()
        play_next_song.stop()
    else:
        await ctx.send("The bot is not connected to a voice channel.")


@bot.command(name='shuffle', aliases=["sh", "shu", "shuf", "shuff", "shuffl", "blanda"], help='Shuffles the current playlist')
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


@bot.command(name='queue', aliases=['q', "qu", "que", "queu", "kö"], help='Displays the next 5 songs in the queue')
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


@bot.command(name='move', aliases=["m", "mo", "mov", "flytta"], help='Move a song in the queue to a new position')
@is_author_in_voice_channel()
async def move(ctx, from_position: int, to_position: int = 1):
    if from_position == 1:
        await ctx.send("trying to move the first song to position 1 in queue?? retard")
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
            await ctx.send(f"Moved {song.title} from position {from_position} to {to_position}.")
        else:
            await ctx.send(f"Moved song to the front of the queue.")
    else:
        await ctx.send("Invalid position. Please check the queue and try again.")


@bot.command(name="die", help='Terminates the bot ()')
async def die(ctx):
    if str(ctx.author.id) == os.getenv("DISCORD_LUTTU_TOKEN"):
        await ctx.send("Hörs på byn.")
        await bot.close()
    else:
        await ctx.send("You lack permission, try -leave instead if you want me gone.")


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


@bot.command(name="alias", help="Sets given URL to given alias")
@is_author_in_voice_channel()
async def alias(ctx, url, new_alias):
    if url == 'np':
        if (np_url := get_current_player_url()):
            await alias(ctx, np_url, new_alias)
        else:
            await ctx.send("Nothing valid is playing to add as alias right now.")
        return
    if not assert_url(url):
        await ctx.send("Invalid url; make sure to send a valid youtube, spotify, or soundcloud link.")
        return
    if assert_alias(new_alias):
        await ctx.send("That alias already exists.")
        return
    if url in get_alias_urls():
        await ctx.send(f"That song already has the alias: {get_alias_from_url(url)}")
        return
    success = add_alias(url, new_alias)
    if success:
        await ctx.send(f"Successfully added alias: {new_alias}")
    

@bot.command(name="rmalias", help="remove given alias")
@is_author_in_voice_channel()
async def rmalias(ctx, alias):
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


@bot.command(name="np", help="Displays currently playing song")
@is_author_in_voice_channel()
async def nowplaying(ctx):
    if ctx.voice_client.is_playing():
        if (np := get_current_player_title()):
            await ctx.send(f"Currently playing: {np}.")
    else:
        await ctx.send("Not playing anything right now.")


@bot.command(name="random", aliases=["r", "ra", "ran", "rand", "rando", "slumpa"], help="Play a randomly selected song that has been requested within the last 6 months.")
async def play_random(ctx, *flags):
    mtag = None
    n = 1
    for flag in flags:
        if str.isdigit(flag):
           n = flag
        else:
            mtag = flag
            if not assert_tag(mtag):
                await ctx.send("That's not a valid tag.")
                return

    random_urls = get_random_cached_urls(n, mtag)

    for url in random_urls:
        await play(ctx, url, "-t")


@bot.command(name="silence", help="Toggle silence mode.")
@is_author_in_voice_channel()
async def silence(ctx):
    is_silenced = toggle_silence()
    if(is_silenced):
        await ctx.send("Silence has been turned on.")
    else:
        await ctx.send("Silence has been turned off.")


@bot.command(name="replace", help="Replace current song in cache with given url")
async def replace(ctx, url):
    async with ctx.typing():
        logging.debug(f"url to replace WITH: {url}")
        url_to_work_with = get_current_player_url()
        logging.debug(f"url to work with: {url_to_work_with}")
        player = await get_player(url)
        logging.debug(f"cleaned up url: {player.url}")
        # await skip(ctx)
        new_path = get_path_from_url(player.url)
        # remove_cached_audio(url_to_work_with)
        set_path_for_url(new_path, url_to_work_with)
        remove_cache_entry(player.url)
        add_to_q(player)
        if get_current_player_url() == url_to_work_with:
            await skip(ctx)
        await ctx.send('Successfully replaced cached audio')


@bot.command(name="tag", help="Create a new music tag")
async def tag(ctx, new_tag):
    if new_tag in get_tags():
        await ctx.send("That tag already exists")
        return
    logging.debug(f"Creating tag: {new_tag!r}")
    success = create_tag(new_tag)
    if success:
        logging.debug("Success")
        await ctx.send(f"Successfully created the tag: {new_tag!r}")
        return
    else:
        logging.error("Failed")
        await ctx.send("Something went wrong when trying to create the tag. Please try again.")
        return
    

@bot.command(name="trash", help="Mark currently playing song to be removed at next boot.")
async def trash(ctx):
    success = to_remove(get_current_player_url())
    if success:
        await ctx.send("Successfully marked song to be deleted.")
        await skip(ctx)
    else:
        await ctx.send("Something went wrong.")


@bot.command(name="duration", help="Show how much left it is of the currently played song")
async def duration(ctx):
    if not ctx.voice_client.is_playing():
        await ctx.send("Nothing currently playing to display duration of.")
        return
    if not get_current_player_duration():
        await ctx.send("duration not existent for this song")
        return
    currently_at_minutes, currently_at_seconds = divmod(get_duration(), 60)
    player_dur_minutes, player_dur_seconds     = divmod(get_current_player_duration(), 60)
    await ctx.send(f"{currently_at_minutes}:{currently_at_seconds} / {player_dur_minutes}:{player_dur_seconds}")