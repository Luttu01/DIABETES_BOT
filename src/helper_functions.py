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
            if not ctx.author.voice:
                logging.debug(f'Decorator failed for function: {func.__name__}')
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
                await ctx.send(f'--- Now playing: {next_song.title} ---')
                set_current_player(next_song)
                set_np(next_song.title)
            except Exception as e:
                await ctx.send(f"Error playing the song")
                print(e)

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
# @tasks.loop(seconds=1.0)
# async def play_next_song(ctx):
#     if ctx.voice_client and not ctx.voice_client.is_playing() and not ctx.voice_client.is_paused():
#         if queue:
#             next_song = queue.pop(0)
#             if next_song == None:
#                 await ctx.send("Problem with this song, skipping to next one")
#                 await play_next_song(ctx)
#             ctx.voice_client.play(next_song, after=lambda e: None)  # No after callback
#             set_current_player(next_song)
#             set_np(next_song.title)
#             await ctx.send(f'--- Now playing: {next_song.title} ---')
            

'''
Helper for @play_next_song function
Assert bot is ready
'''
# @play_next_song.before_loop
# async def before_play_next_song():
#     await bot.wait_until_ready()

'''
Fetch all tracks in a given spotify playlist @playlist_url
Used in @./bot_commands.play function
'''
def get_spotify_playlist_tracks(playlist_url):
    results = sp.playlist_tracks(playlist_url)
    tracks = []
    for item in results['items']:
        track = item.get('track', {})
        url = track.get('external_urls', {}).get('spotify') 
        if url: 
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

def spoof_user(username, id):
    try:
        with open(rf'{jsons_path}\author_id.json', 'r') as read_file:
            author_ids = json.load(read_file)
        
        if id in author_ids.values():
            for username, current_id in author_ids.items():
                if current_id == id:
                    author_ids[username] == id
        else:
            author_ids[username] = id
        
        with open(rf'{jsons_path}\author_id.json', 'w') as write_file:
            json.dump(author_ids, write_file, indent=4)
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
    

async def get_player(url, stream=False):
    parsed_url = urlparse(url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"

    if "spotify" in url:
        if base_url not in get_cached_urls():
            try:
                print(sp.track(base_url))
                url = await get_youtube_link(url)
                player = await YTDLSource.from_url(url, loop=bot.loop, stream=stream, spotify_url=base_url)
            except youtube_dl.DownloadError as e:
                print(e)
                return None
        else:
            player = await YTDLSource.from_url(base_url, loop=bot.loop, stream=stream)
    elif "youtube" in url or "youtu.be" in url:
        query_params = parse_qs(parsed_url.query)
        if 'v' in query_params:
            new_query = f"v={query_params['v'][0]}"
            cleaned_url = urlunparse(parsed_url._replace(query=new_query))
            print(cleaned_url)
            player = await YTDLSource.from_url(cleaned_url, loop=bot.loop, stream=stream)
        else:
            player = await YTDLSource.from_url(url, loop=bot.loop, stream=stream)
    else:
        player = await YTDLSource.from_url(url, loop=bot.loop, stream=stream)

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

def get_spoofed_users():
    with open(rf'{jsons_path}\author_id.json', 'r') as read_file:
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


async def process_yt_playlist(query, stream, mtag):
    try:
        tracks        = get_youtube_playlist_urls(query)
        playlist_name = get_yt_playlist_name(query)
        to_append     = []
        failures      = 0
        for url in tracks:
            player = await get_player(url, stream=stream)
            if player is None:
                failures += 1
                continue
            if mtag:
                add_tag(player.url, mtag)
            to_append.append(player)
        add_to_q(to_append)
        return (playlist_name, failures)
    except youtube_dl.DownloadError as e:
        print(e)
        return None

async def process_spotify_playlist(query):
    tracks        = get_spotify_playlist_tracks(query)
    playlist_name = get_spotify_playlist_name(query)
    to_append     = []
    failures      = 0
    for track in tracks:
        url    = await get_youtube_link(track)
        player = await get_player(url, stream=True)
        if player is None:
            failures += 1
            continue
        to_append.append(player)
    add_to_q(to_append)
    return (playlist_name, failures)


def get_spotify_album_name(url):
    try:
        album_details = sp.album(url)
        album_name = album_details['name']
        return album_name
    except spotipy.exceptions.SpotifyException as e:
        print(f"An error occurred: {e}")
        return None


def get_spotify_album_tracks(url):
    results = sp.album_tracks(url)
    tracks = []
    for item in results['items']:
        url = item.get('external_urls', {}).get('spotify') 
        if url: 
            tracks.append(url)
    return tracks


async def process_spotify_album(query):
    tracks        = get_spotify_album_tracks(query)
    album_name    = get_spotify_album_name(query)
    to_append     = []
    failures      = 0
    for track in tracks:
        url    = await get_youtube_link(track)
        player = await get_player(url, stream=True)
        if player is None:
            failures += 1
            continue
        to_append.append(player)
    add_to_q(to_append)
    return (album_name, failures)


def sort_cache():
    try:
        cache_path = os.path.join(jsons_path, 'cache.json')
        with open(cache_path, 'r') as read_file:
            data = json.load(read_file)

        keys_to_delete = []
        for cached_url in data:
            date_to_check = datetime.datetime.strptime(data[cached_url]['last_accessed'], '%Y-%m-%d')
            current_date = datetime.datetime.now()
            delta_time = current_date - date_to_check
            if delta_time > datetime.timedelta(weeks=24):
                keys_to_delete.append(cached_url)

        for key in keys_to_delete:
            os.remove(data[key]['path'])
            del data[key]

        with open(cache_path, 'w') as write_file:
            json.dump(data, write_file, indent=4)

    except json.JSONDecodeError:
        print("Error decoding JSON.")


def set_np(title):
    global now_playing
    now_playing = title


def get_np():
    global now_playing
    return now_playing


def set_current_player(player):
    global current_player
    current_player = player


def get_current_player_title():
    global current_player
    return current_player.title


def get_current_player_url():
    global current_player
    return current_player.url


def add_to_q(what):
    global queue
    try:
        if type(what) == list:
            queue.extend(what)
            return True
        else:
            queue.append(what)
            return True    
    except Exception:
        return False
    

# def get_random_cached_urls(n):
#     with open(json_cache_file, 'r') as r:
#         cache = json.load(r)

#     cached_urls = get_cached_urls()
#     random.shuffle(cached_urls)
#     weights = [cache[url]['weight'] for url in cached_urls]

#     selection_weights = [1 / (1 + weight) for weight in weights]

#     total_weight = sum(selection_weights)
#     normalized_weights = [w / total_weight for w in selection_weights]

#     random_urls = random.choices(cached_urls, weights=normalized_weights, k=n)

#     for url in random_urls:
#         cache[url]['weight'] += 1

#     with open(json_cache_file, 'w') as w:
#         json.dump(cache, w, indent=4)

#     return list(set(random_urls))

def get_random_cached_urls(n, mtag):
    with open(json_cache_file, 'r') as r:
        cache = json.load(r)

    weighted_urls = []
    
    cached_urls = get_cached_urls()

    if mtag == None:
        for url in cached_urls:
            for _ in range(100//cache[url]['weight']):
                weighted_urls.append(url)
    else:
        for url in cached_urls:
            if check_tag(cache[url], mtag):
                weighted_urls.append(url)

    random.shuffle(weighted_urls)

    random_urls = list(set(random.choices(weighted_urls, k=int(n))))

    for url in random_urls:
        cache[url]['weight'] += 1

    with open(json_cache_file, 'w') as w:
        json.dump(cache, w, indent=4)

    return random_urls


def clear_logs():
    with open(log_file_path, 'w'):
        pass


def reformat_cache():
    with open(r'C:\Users\absol\Desktop\python\DIABETESBOT\res\cache_backup.json', 'r') as r:
        cache = json.load(r)
    
    new_cache = {}
    for url, details in cache.items():
        if isinstance(cache[url], list):
            new_cache[url] = {
                "path": details[0], 
                "title": details[1], 
                "last_accessed": details[2], 
                "weight": 1,
                "volume": 0.5
            }
    with open(json_cache_file, 'w') as w:
        json.dump(new_cache, w, indent=4)
    
# def reformat_cache():
#     with open(r'C:\Users\absol\Desktop\python\DIABETESBOT\res\cache_backup.json', 'r') as r:
#         cache = json.load(r)
    
#     for url in cache.keys():
#         print(url)
#         print(cache[url])
#         cache[url]["volume"] = 0.5

#     with open(json_cache_file, 'w') as w:
#         json.dump(cache, w, indent=4)


def reset_weighting():
    with open(json_cache_file, 'r') as r:
        cache = json.load(r)
    
    for url in cache.keys():
        cache[url]['weight'] = 1

    with open(json_cache_file, 'w') as w:
        json.dump(cache, w, indent=4)


def toggle_silence():
    global silence_bool
    silence_bool = not silence_bool
    return silence_bool

def get_silence_bool():
    global silence_bool
    return silence_bool

def idle():
    global idle_count
    idle_count += 1
    if idle_count >= (10 * 60):
        return True
    else:
        return False

def set_silence(bool):
    global silence_bool
    silence_bool = bool


def check_allowed_to_skip(who, current_song):
    with open(r'C:\Users\absol\Desktop\python\DIABETESBOT\res\blacklists.json', 'r') as r:
        blacklists = json.load(r)
    
    if current_song in blacklists[who]:
        return False
    else:
        return True


def remove_cache_entry(url):
    with open(json_cache_file, 'r') as r:
        cache = json.load(r)
    
    del cache[url]

    with open(json_cache_file, 'w') as w:
        json.dump(cache, w, indent=4)


def get_path_from_url(url):
    with open(json_cache_file, 'r') as r:
        cache = json.load(r)
    
    return cache[url]['path']


def remove_cached_audio(url):
    with open(json_cache_file, 'r') as r:
        cache = json.load(r)
    
    os.remove(cache[url]['path'])


def set_path_for_url(new_path, url):
    with open(json_cache_file, 'r') as r:
        cache = json.load(r)

    cache[url]['path'] = new_path

    with open(json_cache_file, 'w') as w:
        json.dump(cache, w, indent=4)


def get_tags():
    with open(json_tags_file_path, 'r') as r:
        data = json.load(r)
        return data['tags']
    

def create_tag(new_tag):
    try:
        try:
            with open(json_tags_file_path, 'r') as r:
                data = json.load(r)
                tags = data.get('tags', [])
        except json.JSONDecodeError:
            tags = []
            
        tags.append(new_tag)
            
        with open(json_tags_file_path, 'w') as w:
            data['tags'] = tags
            json.dump(data, w, indent=4)
        
        return True
    
    except Exception:
        return False
    

def add_tag(url, tag):
    with open(json_cache_file, 'r') as r:
        cache = json.load(r)
    
    if 'tag' in cache[url]:
        return cache[url]['tag']
    else:
        cache[url]['tag'] = tag

    with open(json_cache_file, 'w') as w:
        json.dump(cache, w, indent=4)
        return None
    
    
def check_tag(cache_entry_attributes, mtag):
    cea = cache_entry_attributes
    if 'tag' in cea:
        return cea['tag'] == mtag
    else:
        return False
    

def assert_tag(mtag):
    return mtag in get_tags()


def extract_mtag(flags):
    tags = get_tags()
    for flag in flags:
        if flag in tags:
            return flag
    return False


def to_remove(new_tag):
    try:
        try:
            with open(json_to_remove_path, 'r') as r:
                data = json.load(r)
                remove_list = data.get('to_remove', [])
        except json.JSONDecodeError:
            data = {}
            remove_list = []
            
        remove_list.append(new_tag)
            
        with open(json_to_remove_path, 'w') as w:
            data['to_remove'] = remove_list
            json.dump(data, w, indent=4)
        
        return True
    
    except Exception:
        return False
    

def remove_doomed_urls():
    try:
        with open(json_to_remove_path, 'r') as r:
            data = json.load(r)
            remove_list = data.get('to_remove', [])
    except json.JSONDecodeError:
        data = {}
        remove_list = []
    
    for url in remove_list:
        remove_cached_audio(url)
        remove_cache_entry(url)
    
    with open(json_to_remove_path, 'w') as w:
        data['to_remove'] = []
    