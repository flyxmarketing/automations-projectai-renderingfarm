import requests

def getInstagramReel(reel_url):
    headers = {
        "Content-Type": "application/json",
        "x-rapidapi-key": "3799837a21msh8a998ce2d72228cp10acc2jsn7a4dd347d615",
        "x-rapidapi-host": "instagram-scraper-stable-api.p.rapidapi.com"
    }
    params = {
        "type": "reel",
        "reel_post_code_or_url": reel_url
    }
    response = requests.get(
        "https://instagram-scraper-stable-api.p.rapidapi.com/get_media_data.php",
        headers=headers,
        params=params
    )
    response.raise_for_status()
    api_data = response.json()
    if 'video_url' in api_data and len(api_data['video_url']) > 0:
        video_url = api_data['video_url']
        return video_url
    else:
        raise Exception("Failed to extract video URL from RapidAPI response")

def getXVideo(post_id):
    headers = {
        "Content-Type": "application/json",
        "x-rapidapi-key": "3799837a21msh8a998ce2d72228cp10acc2jsn7a4dd347d615",
        "x-rapidapi-host": "twitter241.p.rapidapi.com"
    }
    params = {
        "pid": post_id
    }
    response = requests.get(
        "https://twitter241.p.rapidapi.com/tweet-v2",
        headers=headers,
        params=params
    )
    response.raise_for_status()
    api_data = response.json()
    if 'result' in api_data and 'tweetResult' in api_data['result']:
        tweet_result = api_data['result']['tweetResult']['result']
        if 'legacy' in tweet_result and 'extended_entities' in tweet_result['legacy']:
            media_list = tweet_result['legacy']['extended_entities'].get('media', [])
            for media in media_list:
                if media.get('type') == 'video' and 'video_info' in media:
                    variants = media['video_info'].get('variants', [])
                    mp4_variants = [v for v in variants if v.get('content_type') == 'video/mp4' and 'bitrate' in v]
                    if mp4_variants:
                        latest_variant = max(mp4_variants, key=lambda x: x['bitrate'])
                        return latest_variant['url']
        raise Exception("No video found in tweet")
    else:
        raise Exception("Failed to extract video URL from RapidAPI response")
