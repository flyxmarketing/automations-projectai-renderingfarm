import os
import yt_dlp

def downloadVideoWithYTDLP(url, filepath):
    try:
        ydl_opts = {
            'outtmpl': filepath,
            'format': 'best[ext=mp4]/best'
        }
        cookies_file = '/code/libs/ytdlp/cookies.txt'
        if os.path.exists(cookies_file):
            ydl_opts['cookiefile'] = cookies_file
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as e:
        raise Exception(f"Failed to download using yt-dlp. Error: {e}")
