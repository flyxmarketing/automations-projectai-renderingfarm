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
