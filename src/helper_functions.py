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
                now_playing = next_song.title
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
    if ctx.voice_client and not ctx.voice_client.is_playing() and not ctx.voice_client.is_paused():
        if queue:
            next_song = queue.pop(0)
            if next_song == None:
                await ctx.send("Problem with this song, skipping to next one")
                await play_next_song(ctx)
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
def update_url_counter(url, title):
    try:
        with open(rf'{jsons_path}\url_counter.json', 'r') as read_file:
            open_json = json.load(read_file)
        if url in open_json:
            open_json[url][0] += 1
        else:
            open_json[url] = [1, title]
        with open(rf'{jsons_path}\url_counter.json', 'w') as write_file:
            json.dump(open_json, write_file, indent=4)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(e)

'''
Update values of ./play_requests_counter.json
Used in @./bot_commands.play function
'''
def update_request_counter(user):
    try:
        with open(rf'{jsons_path}\play_requests_counter.json', 'r') as read_file:
            open_json = json.load(read_file)
            with open(rf'{jsons_path}\play_requests_counter.json', 'w') as write_file:
                open_json[user] = open_json[user] + 1 if user in open_json else 1
                json.dump(open_json, write_file, indent=4)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(e)

'''
Add given alias to ./aliases.json
Used in @./bot_commands.alias function
'''
def add_alias(url, new_name):
    try:
        with open(rf'{jsons_path}\aliases.json', 'r') as read_file:
            aliases = json.load(read_file)
        if url in aliases.keys():
            return False
        with open(rf'{jsons_path}\aliases.json', 'w') as write_file:
            aliases[url] = new_name
            json.dump(aliases, write_file, indent=4)
            return True
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(e)

'''
Remove given alias from ./aliases.json
Used in @./bot_commands.rmalias function
'''
def remove_alias(alias):
    if not assert_alias(alias):
        return False
    try:
        with open(rf'{jsons_path}\aliases.json', 'r') as read_file:
            aliases = json.load(read_file)
        url = get_url_from_alias(alias)
        if url:
            del aliases[url]
        else:
            return False
        with open(rf'{jsons_path}\aliases.json', 'w') as write_file:
            json.dump(aliases, write_file, indent=4)
            return True
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(e)

'''
Sort ./url_counter.json in descending order
used in @./bot_commands.join function
'''
def sort_counter():
    try:
        with open(rf'{jsons_path}\url_counter.json', 'r') as read_file:
            data = json.load(read_file)
        sorted_data = dict(sorted(data.items(), key=lambda x: x[1][0], reverse=True))
        with open(rf'{jsons_path}\url_counter.json', 'w') as write_file:
            json.dump(sorted_data, write_file, indent=4)
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
            with open(rf'{jsons_path}\url_counter.json', 'r') as file:
                data = json.load(file)
            list_of_tuples = [(data[value][1], data[value][0]) for value in data]
            return list_of_tuples[:10]
        except Exception as e:
            print(f"In fetch_top_songs: {e}")
            return []
    

async def get_player(ctx, url, stream=True):
    async with ctx.typing():
        spotify_url = ""
        if "spotify" in url and url not in get_cached_urls():
            try:
                spotify_url = url
                url = await get_youtube_link(url)
            except youtube_dl.DownloadError as e:
                await ctx.send("There was an error processing your request. Please try a different URL or check the URL format.")
                print(e)
        try:
            if spotify_url:
                player = await YTDLSource.from_url(url, loop=bot.loop, stream=stream, spotify_url=spotify_url)
            else:
                player = await YTDLSource.from_url(url, loop=bot.loop, stream=stream)
        except youtube_dl.DownloadError as e:
            await ctx.send("There was an error processing your request. Please try a different URL or check the URL format.")
            print(e)
        return player
    
def assert_url(url):
    return "spotify" in url or "youtube" in url or "soundcloud" in url

def get_alias_from_url(url):
     with open(rf'{jsons_path}\aliases.json', 'r') as read_file:
        aliases = json.load(read_file)
        return aliases[url]
     
def get_url_from_alias(alias):
     with open(rf'{jsons_path}\aliases.json', 'r') as read_file:
        aliases = json.load(read_file)
        for url, current_alias in aliases.items():
            if current_alias == alias:
                return url
        return False

def get_aliases():
    with open(rf'{jsons_path}\aliases.json', 'r') as read_file:
        aliases = json.load(read_file)
        return list(aliases.values())

def get_alias_urls():
    with open(rf'{jsons_path}\aliases.json', 'r') as read_file:
        aliases = json.load(read_file)
        return list(aliases.keys())

def assert_alias(alias):
    return alias in get_aliases()

def get_cached_urls():
    with open(rf'{jsons_path}\cache.json', 'r') as read_file:
        caches = json.load(read_file)
        return list(caches.keys())


def get_youtube_playlist_urls(url):
    youtube = build('youtube', 'v3', developerKey=os.getenv('YT_API_KEY'))
    request = youtube.playlistItems().list(
        part="snippet",
        playlistId= _extract_playlist_id(url),
        maxResults=50  # API allows up to 50 items per request
    )
    
    response = request.execute()
    
    video_urls = []
    for item in response.get('items', []):
        video_id = item['snippet']['resourceId']['videoId']
        video_urls.append(f'https://www.youtube.com/watch?v={video_id}')
    
    return video_urls

def get_yt_playlist_name(url):
    youtube = build('youtube', 'v3', developerKey=os.getenv('YT_API_KEY'))
    request = youtube.playlists().list(
        part="snippet",
        id= _extract_playlist_id(url),
    )
    
    response = request.execute()
    
    playlist_name = response['items'][0]['snippet']['title']
    return playlist_name


def _extract_playlist_id(url):
    parsed_url = urlparse(url)
    query_string = parse_qs(parsed_url.query)
    playlist_id = query_string.get("list", [None])[0]
    return playlist_id


async def process_yt_playlist(ctx, query):
    try:
        tracks = get_youtube_playlist_urls(query)
        for url in tracks:
            player = await get_player(ctx, url)
            if player is None:
                await ctx.send("Problem processing a song, moving on to the next one.")
                continue
            queue.append(player)
        await ctx.send(f"Added '{get_yt_playlist_name(query)}' to the queue.")
        return
    except youtube_dl.DownloadError as e:
        await ctx.send("There was an error processing your request. Please try a different URL or check the URL format.")
        print(e)

async def process_spotify_playlist(ctx, query):
    tracks = get_spotify_playlist_tracks(query)
    playlist_name = get_spotify_playlist_name(query)
    for track in tracks:
        url = await get_youtube_link(track)
        player = await get_player(ctx, url)
        if player is None:
            await ctx.send("Problem processing a song, moving on to the next one.")
            continue
        queue.append(player)
    await ctx.send(f"added to queue: {playlist_name}")
    return

def download_audio(input_url):
    command = [
        'ffmpeg',
        '-i', input_url,
        '-vn',
        '-ar', '44100',
        '-ac', '2',
        '-b:a', '192k',
        f'{cache_path}\test.mp3'
    ]
    try:
        subprocess.run(command, check=True)
        # print(f"Downloaded and saved audio to {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to download audio: {e}")