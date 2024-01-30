from . import *
from functools import wraps

'''
Wrapper for bot.commands to check 
that the requester is in a voice channel
'''
def is_author_in_voice_channel():
    def decorator(func):
        @wraps(func)
        async def wrapper(ctx, *args, **kwargs):
            # Check if the user is not connected to any voice channel
            if not ctx.author.voice:
                await ctx.send("You are not connected to a voice channel.")
                return
        
            return await func(ctx, *args, **kwargs)
        return wrapper
    return decorator

'''
!CURRENTLY UNUSED!
Play next song if queue is not empty
and bot is not playing anything currently
'''
async def check_queue(ctx):
    if queue:
        next_song = queue.pop(0)
        if ctx.voice_client and not ctx.voice_client.is_playing():
            try:
                ctx.voice_client.play(next_song, after=lambda e: print(f"Error in playback: {e}" if e else "Playback finished."))
                await ctx.send(f'Now playing: {next_song.title}')
            except Exception as e:
                await ctx.send(f"Error playing the song: {e}")
                # Handle the error or log it
    else:
        await ctx.send("The queue is empty.")

'''
Helper function for @get_youtube_link

Search after relevant youtube link, using @query
'''
def _search_youtube(query):
    with youtube_dl.YoutubeDL(ytdl_format_options) as ydl:
        try:
            info = ydl.extract_info(query, download=False)
            return info['entries'][0]['webpage_url']
        except Exception as e:
            print(f"Error fetching YouTube URL: {e}")
            return None
        
'''
Extract youtube link, 
using information from given @spotify_url
'''
async def get_youtube_link(spotify_url):
    # Extract track info from Spotify URL
    track_info = sp.track(spotify_url)
    track_name = track_info['name']
    artist_name = track_info['artists'][0]['name']
    youtube_link = _search_youtube(f"{track_name} {artist_name}")
    return youtube_link

'''
Every second:
If bot is not playing anything and queue is not empty,
play next song
'''
@tasks.loop(seconds=1.0)
async def play_next_song(ctx):
    # print('loop called')
    if ctx.voice_client and not ctx.voice_client.is_playing() and not ctx.voice_client.is_paused():
        if queue:
            next_song = queue.pop(0)
            if next_song == None:
                await ctx.send("Problem with this song, skipping to next one")
                play_next_song(ctx)
            ctx.voice_client.play(next_song, after=lambda e: None)  # No after callback
            await ctx.send(f'Now playing: {next_song.title}')

'''
Helper for @play_next_song function
Assert bot is ready
'''
@play_next_song.before_loop
async def before_play_next_song():
    await bot.wait_until_ready()

'''
Fetch all tracks in a given spotify playlist @playlist_url
Used in @./bot_commands.play function
'''
def get_spotify_playlist_tracks(playlist_url):
    results = sp.playlist_tracks(playlist_url)
    tracks = []
    for item in results['items']:
        track = item['track']
        url = track['external_urls']['spotify']
        tracks.append(url)  
    return tracks

'''
Fetch name of given spotify playlist @playlist_url
Used in @./bot_commands.play function 
'''
def get_spotify_playlist_name(playlist_url):
    # Fetch the playlist details
    try:
        playlist_details = sp.playlist(playlist_url)
        playlist_name = playlist_details['name']
        return playlist_name
    except spotipy.exceptions.SpotifyException as e:
        print(f"An error occurred: {e}")
        return None

'''
Update values of ./url_counter.json
Used in @./bot_commands.play function
'''
def update_url_counter(url):
    try:
        with open(r'C:\Users\absol\Desktop\python\DIABETESBOT\url_counter.json', 'r') as read_file:
            open_json = json.load(read_file)
            with open(r'C:\Users\absol\Desktop\python\DIABETESBOT\url_counter.json', 'w') as write_file:
                open_json[url] = open_json[url] + 1 if url in open_json else 1
                json.dump(open_json, write_file, indent=4)
                read_file.close()
                write_file.close()
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(e)

'''
Update values of ./play_requests_counter.json
Used in @./bot_commands.play function
'''
def update_request_counter(user):
    try:
        with open(r'C:\Users\absol\Desktop\python\DIABETESBOT\play_requests_counter.json', 'r') as read_file:
            open_json = json.load(read_file)
            with open(r'C:\Users\absol\Desktop\python\DIABETESBOT\play_requests_counter.json', 'w') as write_file:
                open_json[user] = open_json[user] + 1 if user in open_json else 1
                json.dump(open_json, write_file, indent=4)
                read_file.close()
                write_file.close()
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(e)

'''
Sort ./url_counter.json in descending order
used in @./bot_commands.join function
'''
def sort_counter():
    try:
        with open(r'C:\Users\absol\Desktop\python\DIABETESBOT\url_counter.json', 'r') as file:
            data = json.load(file)
        sorted_data = dict(sorted(data.items(), key=lambda x: x[1], reverse=True))
        with open(r'C:\Users\absol\Desktop\python\DIABETESBOT\url_counter.json', 'w') as file:
            json.dump(sorted_data, file, indent=4)
        file.close()
    except FileNotFoundError:
        print("File not found.")
    except json.JSONDecodeError:
        print("Error decoding JSON.")

'''
Return top 10 requested songs
used in @./bot_commands.topsongs function
'''
async def fetch_top_songs(ctx):
    async with ctx.typing():
        try:
            with open(r'C:\Users\absol\Desktop\python\DIABETESBOT\url_counter.json', 'r') as file:
                data = json.load(file).items()
                list_of_tuples = []
                loop_counter = 0
                for url, counter in data:
                    if "playlist" in url:
                        continue
                    if loop_counter >= 10:
                        return list_of_tuples
                    player = await get_player(ctx, url)
                    list_of_tuples.append((player.title, counter))
                    loop_counter += 1
        except Exception as e:
            print(f"In fetch_top_songs: {e}")
            return []
    

async def get_player(ctx, url):
    async with ctx.typing():
        if "spotify" in url:
            try:
                url = await get_youtube_link(url)
            except youtube_dl.DownloadError as e:
                await ctx.send("There was an error processing your request. Please try a different URL or check the URL format.")
                print(e)
        try:
            player = await YTDLSource.from_url(url, loop=bot.loop, stream=True)
        except youtube_dl.DownloadError as e:
            await ctx.send("There was an error processing your request. Please try a different URL or check the URL format.")
            print(e)
        return player