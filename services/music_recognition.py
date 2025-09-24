from shazamio import Shazam

async def recognize_song(file_path: str):
    shazam = Shazam()
    result = await shazam.recognize_song(file_path)
    if 'track' in result and result['track']:
        title = result['track']['title']
        subtitle = result['track']['subtitle']
        url = result['track'].get('url')
        return {
            "title": title,
            "artist": subtitle,
            "url": url
        }
    return None