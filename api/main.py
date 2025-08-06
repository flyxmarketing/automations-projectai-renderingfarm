import logging
import json
import uuid
import requests
import re
import yt_dlp

from quart import Quart, jsonify, request

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

QUEUE_FILE = '/media/queue.json'

def download_video(url, filepath, processing_id):
    social_media_patterns = [
        r'instagram\.com',
        r'tiktok\.com',
        r'facebook\.com',
        r'fb\.watch',
        r'youtube\.com',
        r'youtu\.be'
    ]

    is_social_media = any(re.search(pattern, url, re.IGNORECASE) for pattern in social_media_patterns)

    if is_social_media:
        ydl_opts = {
            'outtmpl': filepath,
            'format': 'best[ext=mp4]/best'
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    else:
        response = requests.get(url, stream=True)
        response.raise_for_status()

        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

    logger.info(f'[{processing_id}] Video downloaded successfully to: {filepath}')

def create_app():
    app = Quart(__name__)

    app.secret_key = 'Zr8pIKMOV+yrNiJ2MesAO4ch'

    @app.route('/', methods=['POST'])
    async def webhook():
        request_uuid = uuid.uuid4()

        try:
            data = await request.get_json()

            if not data:
                return jsonify({'status': 'error', 'message': 'No JSON data provided'}), 400

            url = data.get('url')
            archive_id = data.get('archive_id')
            run_id = data.get('run_id')

            if not url or not run_id or not archive_id:
                return jsonify({'status': 'error', 'message': 'Both url and uuid are required'}), 400

            logger.info(f'Webhook received - URL: {url}, UUID: {run_id}')

            video_filename = f"{request_uuid}.mp4"
            video_filepath = f"/media/queue/{video_filename}"

            try:
                download_video(url, video_filepath, run_id)
            except Exception as e:
                logger.error(f"[{run_id}] Failed to download video: {str(e)}")
                return jsonify({'status': 'error', 'message': 'Failed to download video'}), 500

            try:
                with open(QUEUE_FILE, 'r') as f:
                    queue_data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                queue_data = []

            queue_item = {
                'url': url,
                'archive_id': archive_id,
                'run_id': run_id,
                'video_filepath': video_filepath,
                'request_uuid': str(request_uuid),
                'status': 'queued'
            }
            queue_data.append(queue_item)

            try:
                with open(QUEUE_FILE, 'w') as f:
                    json.dump(queue_data, f, indent=2)
                logger.info(f"[{run_id}] Added to queue: {video_filepath}")
            except Exception as e:
                logger.error(f"[{run_id}] Failed to update queue file: {str(e)}")
                return jsonify({'status': 'error', 'message': 'Failed to update queue'}), 500

            return jsonify({
                'status': 'queued',
                'message': 'Video added to queue',
                'request_uuid': request_uuid,
                'queue_position': len(queue_data) - 1
            }), 202

        except Exception as e:
            logger.error(f"Error handling webhook: {str(e)}", exc_info=True)
            return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

    return app
