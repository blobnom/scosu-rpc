from osuapi.osuapi import OsuApi
from pypresence import Presence
from config import config
from json import loads
from time import sleep
from time import time

import subprocess
import websocket
import requests

APPLICATION_ID = 1001141712623763477
OSU_LOGO = "osulogo"
OSU_MODES = ["osu", "osutaiko", "osucatch", "osumania"]

rpc = Presence(APPLICATION_ID)
rpc.connect()
api = OsuApi()
start_time = time()

def get_user(name, mode):
    u = api.search_user(name)
    if u is None:
        return None
        
    return api.get_user(u.id, mode)
    
def user_stats(user):
    score = user.stats.ranked_score
    if score > 1_000_000_000:
        score = f"{score / 1_000_000_000:.1f}b"
    elif score > 1_000_000:
        score = f"{score / 1_000_000:.1f}m"
    else:
        score = f"{score:,}"
        
    return f"{user.info.name} (#{user.stats.global_rank:,}) ▸ {score} score"

def map_name(map, mapper = False, diff = True):
    name = f"{map['artist']} - {map['title']}"
    if mapper:
        name += f" ({map['mapper']})"
    if diff:
        name += f" [{map['difficulty']}]"
    return name
    
def map_stats(stats):
    return f"{stats['fullSR']}★ ▸ View Beatmap"

def map_url(data):
    bm = data["menu"]["bm"]
    gm = ["osu", "taiko", "fruits", "mania"][data["menu"]["gameMode"]]
    url = f"https://osu.ppy.sh/beatmapsets/{bm['set']}#{gm}/{bm['id']}"
    req = requests.get(url)
    return url if req.status_code == 200 else None

def main():
    next_time = time()
    activity = {}
    user = None
    current_mode = -1

    def get_activity(data):
        nonlocal user, current_mode
        state = data["menu"]["state"]
        map = data["menu"]["bm"]
        stats = map["stats"]
        play = data["gameplay"]
        
        activity = {
            "buttons": [],
            "assets": {
                "large_image": OSU_LOGO,
                "large_text": map_name(map["metadata"]),
                "small_image": OSU_MODES[data['menu']['gameMode']],
                "small_text": f"Playing osu!{['', 'taiko', 'catch', 'mania'][data['menu']['gameMode']]}",
            }
        }

        mode = data["menu"]["gameMode"]
        modsStr = data['menu']['mods']['str']
        if mode == 0 and "RX" in modsStr:
            mode = 4
        elif mode == 1 and "RX" in modsStr:
            mode = 5
        elif mode == 2 and "RX" in modsStr:
            mode = 6

        if user is None or current_mode != mode:
            user = get_user(config["username"], mode)
        current_mode = mode

        if user is not None:
            activity["assets"].update({
                "large_image": f"https://a.scosu.net/{user.info.id}"
            })
            activity["buttons"].append({
                "label": user_stats(user),
                "url": f"https://scosu.net/u/{user.info.id}"
            })
        else:
            not_found = True

        match state:
            case 0 | 3 | 10 | 11 | 19:
                activity.update({
                    "details": "Main menu",
                    "state": map_name(map["metadata"], diff = False)
                })

            case 1:
                activity.update({
                    "details": "Editing a beatmap",
                    "state": map_name(map["metadata"], diff = False)
                })

            case 4 | 5 | 13:
                activity.update({
                    "details": f"Song select (+{modsStr})",
                    "state": map_name(map["metadata"])
                })
                url = map_url(data)
                if url is not None:
                    activity["buttons"].append({
                        "label": map_stats(stats),
                        "url": url
                    })
            
            case 12:
                activity.update({
                    "details": "In multiplayer",
                    "state": map_name(map["metadata"])
                })
            
            case 2:
                if play["name"] == config["username"]:
                    activity.update({
                        "details": f"Playing (+{modsStr}) ▸ {play['accuracy']:.2f}% ({play['hits']['grade']['current']})",
                        "state": f"{play['score']:,} ▸ {play['combo']['current']:,}x ▸ {play['hits']['0']:,} misses"
                    })
                else:
                    activity.update({
                        "details": f"Watching {play['name']} (+{modsStr}) ▸ {play['accuracy']:.2f}% ({play['hits']['grade']['current']})",
                        "state": f"{play['score']:,} ▸ {play['combo']['current']:,}x ▸ {play['hits']['0']:,} misses"
                    })
                
                url = map_url(data)
                if url is not None:
                    activity["buttons"].append({
                        "label": map_stats(stats),
                        "url": url
                    })
            
            case 7 | 14 | 17 | 18:
                if play["name"] == config["username"]:
                    activity.update({
                        "details": f"Result screen (+{modsStr}) ▸ {play['accuracy']:.2f}% ({play['hits']['grade']['current']})",
                        "state": f"{play['score']:,} ▸ {play['combo']['max']:,}x ▸ {play['hits']['0']:,} misses"
                    })
                else:
                    activity.update({
                        "details": f"Result screen of {play['name']} (+{modsStr}) ▸ {play['accuracy']:.2f}% ({play['hits']['grade']['current']})",
                        "state": f"{play['score']:,} ▸ {play['combo']['max']:,}x ▸ {play['hits']['0']:,} misses"
                    })
                
                url = map_url(data)
                if url is not None:
                    activity["buttons"].append({
                        "label": map_stats(stats),
                        "url": url
                    })
            
            case 15:
                activity.update({
                    "details": "Browsing osu!direct",
                    "state": map_name(map["metadata"])
                })
            
            case _:
                activity.update({
                    "details": "???",
                    "state": map_name(map["metadata"])
                })

        return activity

    def on_message(_ws, message):
        nonlocal next_time, activity
        if time() < next_time:
            return
        
        next_time = time() + config["cooldown"]
        data = loads(message)

        new_activity = get_activity(data)
        if new_activity != activity:
            rpc.update(
                state = new_activity.get("state", ""),
                details = new_activity.get("details", ""),
                large_image = new_activity["assets"]["large_image"],
                large_text = new_activity["assets"]["large_text"],
                small_image = new_activity["assets"]["small_image"],
                small_text = new_activity["assets"]["small_text"],
                buttons = new_activity.get("buttons", []),
                start = start_time
            )
            activity = new_activity

    if config["gosumemory_path"] != "":
        subprocess.Popen(config["gosumemory_path"])

    sleep(5)

    ws = websocket.WebSocketApp(
        config["ws_url"],
        on_message = on_message,
        on_error = lambda _ws, exc: print(type(exc).__name__, exc),
        on_open = lambda _: print("Connected to websocket!")
    )
    ws.run_forever()

if __name__ == "__main__":
    main()
