import os
import re
import requests

from ..ytdlp.init import downloadVideoWithYTDLP
from ..rapidapi.init import getInstagramReel, getXVideo

def downloadVideo(url, filepath):
    social_media_patterns = [
        r'instagram\.com',
        r'tiktok\.com',
        r'facebook\.com',
        r'fb\.watch',
        r'youtube\.com',
        r'youtu\.be',
        r'x\.com',
        r'twitter\.com'
    ]
    is_social_media = any(re.search(pattern, url, re.IGNORECASE) for pattern in social_media_patterns)
    is_instagram = re.search(r'instagram\.com', url, re.IGNORECASE)
    is_twitter = re.search(r'(x\.com|twitter\.com)', url, re.IGNORECASE)
    if is_social_media:
        try:
            downloadVideoWithYTDLP(url,filepath)
        except Exception as e:
            if is_instagram:
                video_url = getInstagramReel(url)
                video_response = requests.get(video_url, stream=True)
                video_response.raise_for_status()
                with open(filepath, 'wb') as f:
                    for chunk in video_response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
            elif is_twitter:
                url_path = url.split('?')[0]
                post_id = url_path.rstrip('/').split('/')[-1]
                video_url = getXVideo(post_id)
                video_response = requests.get(video_url, stream=True)
                video_response.raise_for_status()
                with open(filepath, 'wb') as f:
                    for chunk in video_response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
            else:
                raise e
    else:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
