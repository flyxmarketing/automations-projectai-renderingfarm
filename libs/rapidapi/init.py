import requests
import time

def getInstagramReel(reel_url: str):
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

def getXVideo(post_id: str):
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

def getInstagramReelsFromUser(user: str):
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "x-rapidapi-key": "3799837a21msh8a998ce2d72228cp10acc2jsn7a4dd347d615",
        "x-rapidapi-host": "instagram-scraper-stable-api.p.rapidapi.com"
    }
    all_reels = []
    pagination_token = ""
    request_count = 0
    max_reels = 10
    while len(all_reels) < max_reels:
        if request_count > 0 and request_count % 10 == 0:
            time.sleep(60)
        data = {
            "username_or_url": user,
            "amount": "10",
            "pagination_token": pagination_token
        }
        response = requests.post(
            "https://instagram-scraper-stable-api.p.rapidapi.com/get_ig_user_reels.php",
            headers=headers,
            data=data,
            timeout=120
        )
        response.raise_for_status()
        api_data = response.json()
        request_count += 1
        if 'reels' in api_data and len(api_data['reels']) > 0:
            for reel_item in api_data['reels']:
                if len(all_reels) >= max_reels:
                    break
                if 'node' in reel_item and 'media' in reel_item['node']:
                    media = reel_item['node']['media']
                    reel_data = {
                        'code': media.get('code', ''),
                        'like_count': media.get('like_count', 0),
                        'play_count': media.get('play_count', 0),
                        'view_count': media.get('view_count', 0),
                        'comment_count': media.get('comment_count', 0)
                    }
                    all_reels.append(reel_data)
            if len(all_reels) >= max_reels:
                break
            if 'pagination_token' in api_data and api_data['pagination_token']:
                pagination_token = api_data['pagination_token']
            else:
                break
        else:
            break
    if len(all_reels) > 0:
        return all_reels
    else:
        raise Exception("Failed to extract video URLs from RapidAPI response")

def getTikTokVideosFromUser(user: str):
    headers = {
        "x-rapidapi-key": "3799837a21msh8a998ce2d72228cp10acc2jsn7a4dd347d615",
        "x-rapidapi-host": "tiktok-api23.p.rapidapi.com"
    }
    user_info_response = requests.get(
        "https://tiktok-api23.p.rapidapi.com/api/user/info",
        headers=headers,
        params={"uniqueId": user},
        timeout=120
    )
    user_info_response.raise_for_status()
    user_info_data = user_info_response.json()
    if 'userInfo' not in user_info_data or 'user' not in user_info_data['userInfo']:
        raise Exception("Failed to get user info from TikTok API")
    sec_uid = user_info_data['userInfo']['user'].get('secUid')
    if not sec_uid:
        raise Exception("Failed to extract secUid from user info")
    all_posts = []
    cursor = "0"
    request_count = 0
    max_posts = 10
    while len(all_posts) < max_posts:
        if request_count > 0 and request_count % 10 == 0:
            time.sleep(60)
        data = {
            "secUid": sec_uid,
            "count": "10",
            "cursor": cursor
        }
        response = requests.get(
            "https://tiktok-api23.p.rapidapi.com/api/user/posts",
            headers=headers,
            params=data,
            timeout=120
        )
        response.raise_for_status()
        api_data = response.json()
        request_count += 1
        if 'data' in api_data and 'itemList' in api_data['data'] and len(api_data['data']['itemList']) > 0:
            for item in api_data['data']['itemList']:
                if len(all_posts) >= max_posts:
                    break
                post_data = {
                    'code': item.get('id', ''),
                    'like_count': item.get('stats', {}).get('diggCount', 0),
                    'play_count': item.get('stats', {}).get('playCount', 0),
                    'view_count': item.get('stats', {}).get('playCount', 0),
                    'comment_count': item.get('stats', {}).get('commentCount', 0)
                }
                all_posts.append(post_data)
            if len(all_posts) >= max_posts:
                break
            if 'cursor' in api_data and api_data['cursor']:
                cursor = api_data['cursor']
            else:
                break
        else:
            break
    if len(all_posts) > 0:
        return all_posts
    else:
        raise Exception("Failed to extract tiktoks URLs from RapidAPI response")

def getTwitterVideosFromUser(user: str):
    return {"status":"wip"}
