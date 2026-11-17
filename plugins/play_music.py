"""
Plugin de Música y Canciones Favoritas para Mark-LV JARVIS.
Permite reproducir canciones de YouTube al instante usando yt-dlp y el navegador / reproductor.
"""
import webbrowser
from urllib.parse import quote_plus
import subprocess
import shutil

PLUGIN = {
    "name": "play_music",
    "description": (
        "Plays music, favorite songs, classical music, hymns, or background audio. "
        "Use this tool whenever the user says 'play music', 'reproduce mi cancion', 'pon musica', "
        "or specifies an artist, song title or playlist."
    ),
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "song_name": {
                "type": "STRING",
                "description": "The song title, artist, or music genre to play"
            }
        },
        "required": ["song_name"],
    },
}

def run(parameters: dict, player=None, session_memory=None) -> str:
    song_name = parameters.get("song_name", "").strip()
    if not song_name:
        return "Father, which song or music would you like me to play?"

    try:
        # Usar yt-dlp para buscar el enlace exacto
        yt_search = f"ytsearch1:{song_name}"
        cmd = ["yt-dlp", "--get-id", yt_search]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=12)
        video_id = proc.stdout.strip().split("\n")[0]
        
        if video_id:
            url = f"https://www.youtube.com/watch?v={video_id}"
            webbrowser.open(url)
            return f"Playing '{song_name}' for you now, Father."
        else:
            # Fallback directo a búsqueda de YouTube en navegador
            url = f"https://www.youtube.com/results?search_query={quote_plus(song_name)}"
            webbrowser.open(url)
            return f"Opening '{song_name}' on YouTube, Father."

    except Exception as e:
        url = f"https://www.youtube.com/results?search_query={quote_plus(song_name)}"
        webbrowser.open(url)
        return f"Playing {song_name} on YouTube, Father."
