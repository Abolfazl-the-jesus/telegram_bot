import requests
import asyncio

async def search_musicbrainz(title: str, artist: str = ""):
    """
    جستجو در MusicBrainz API
    """
    url = f"https://musicbrainz.org/ws/2/recording/?query={title}&fmt=json"
    def req():
        res = requests.get(url)
        if res.status_code == 200:
            data = res.json()
            if "recordings" in data and len(data["recordings"]) > 0:
                rec = data["recordings"][0]
                return {
                    "title": rec.get("title", ""),
                    "artist": rec["artist-credit"][0]["name"] if rec.get("artist-credit") else "Unknown",
                    "id": rec.get("id", "")
                }
        return None
    return await asyncio.to_thread(req)

async def search_lastfm(api_key: str, title: str, artist: str = ""):
    """
    جستجو در Last.fm
    """
    url = "http://ws.audioscrobbler.com/2.0/"
    params = {
        "method": "track.search",
        "track": title,
        "artist": artist,
        "api_key": api_key,
        "format": "json"
    }
    def req():
        res = requests.get(url, params=params)
        if res.status_code == 200:
            results = res.json()
            tracks = results.get("results", {}).get("trackmatches", {}).get("track", [])
            if tracks:
                return {
                    "title": tracks[0].get("name", ""),
                    "artist": tracks[0].get("artist", ""),
                    "url": tracks[0].get("url", "")
                }
        return None
    return await asyncio.to_thread(req)