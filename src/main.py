import os
import logging
import subprocess
import json
import uuid
import asyncio
import requests
from quart import Quart, jsonify, request

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Global queue for processing requests
processing_queue = asyncio.Queue()
QUEUE_FILE = 'media/queue.json'
queue_processor_running = False

def save_queue_to_file():
    """Save current queue items to file"""
    logger = logging.getLogger(__name__)
    try:
        # Create media folder if it doesn't exist
        media_folder = 'media'
        if not os.path.exists(media_folder):
            os.makedirs(media_folder)

        # Get all items from queue without removing them
        queue_items = []
        temp_items = []

        # Extract all items
        while not processing_queue.empty():
            try:
                item = processing_queue.get_nowait()
                temp_items.append(item)
                queue_items.append(item)
            except asyncio.QueueEmpty:
                break

        # Put items back
        for item in temp_items:
            processing_queue.put_nowait(item)

        # Save to file
        with open(QUEUE_FILE, 'w') as f:
            json.dump(queue_items, f, indent=2)

        logger.info(f"Saved {len(queue_items)} items to queue file")
    except Exception as e:
        logger.error(f"Failed to save queue to file: {e}")

async def load_queue_from_file():
    """Load queue items from file on startup"""
    logger = logging.getLogger(__name__)
    try:
        if os.path.exists(QUEUE_FILE):
            with open(QUEUE_FILE, 'r') as f:
                queue_items = json.load(f)

            # Add items back to queue
            for item in queue_items:
                await processing_queue.put(item)

            logger.info(f"Loaded {len(queue_items)} items from queue file")

            # Clear the file after loading
            with open(QUEUE_FILE, 'w') as f:
                json.dump([], f)
        else:
            logger.info("No existing queue file found")
    except Exception as e:
        logger.error(f"Failed to load queue from file: {e}")

async def add_to_queue_with_persistence(data):
    """Add item to queue and save to file"""
    await processing_queue.put(data)
    save_queue_to_file()

def get_real_ip():
    if 'CF-Connecting-IP' in request.headers:
        return request.headers['CF-Connecting-IP']
    return request.remote_addr

def page_not_found(_):
    return jsonify({'status': 'error', 'message': 'Route not found'}), 404

async def upload_to_bucket(file_path, filename):
    """Upload processed video to public bucket using rclone"""
    logger = logging.getLogger(__name__)
    # Try rclone first
    #rclone_cmd = [
    #    'rclone', '--config', 'rclone.conf', 'copy', file_path, 'bucket:/', '--progress'
    #]
    #result = subprocess.run(rclone_cmd, capture_output=True, text=True, check=True)
    #logger.info(f"Successfully uploaded {filename} to bucket via rclone")

    # Return public URL (adjust this based on your bucket configuration)
    public_url = f"https://fl.prme.link/{filename}"
    return public_url

def download_video(url, filepath, processing_id):
    """Download video file using requests"""
    logger = logging.getLogger(__name__)

    response = requests.get(url, stream=True)
    response.raise_for_status()

    with open(filepath, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)

    logger.info(f'[{processing_id}] Video downloaded successfully to: {filepath}')

async def run_ffmpeg_command_async(cmd, processing_id):
    """Run ffmpeg command asynchronously using asyncio.create_subprocess_exec"""
    logger = logging.getLogger(__name__)
    logger.info(f"[{processing_id}] Running ffmpeg command: {' '.join(cmd)}")

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        logger.error(f"[{processing_id}] ffmpeg failed with return code {process.returncode}")
        logger.error(f"[{processing_id}] ffmpeg stderr: {stderr.decode()}")
        raise subprocess.CalledProcessError(process.returncode, cmd, output=stdout, stderr=stderr)

    logger.info(f"[{processing_id}] ffmpeg completed successfully")
    if stdout:
        logger.info(f"[{processing_id}] ffmpeg stdout: {stdout.decode()}")
    if stderr:
        logger.info(f"[{processing_id}] ffmpeg stderr: {stderr.decode()}")

    return process

async def process_video_task(data):
    """Process a single video from the queue"""
    processing_id = str(uuid.uuid4())
    logger = logging.getLogger(__name__)
    logger.info(f"[{processing_id}] Starting video processing from queue")

    input_path = None
    output_path = None
    concat_file = None
    input_watermarked_path = None
    watermarked_resized_path = None
    postroll_resized_path = None

    try:
        url = data.get('url')
        run_id = data.get('run_id')

        logger.info(f'[{processing_id}] Processing - URL: {url}, UUID: {run_id}')

        media_folder = 'media'
        if not os.path.exists(media_folder):
            os.makedirs(media_folder)

        temp_folder = 'media/tmp'
        if not os.path.exists(temp_folder):
            os.makedirs(temp_folder)

        original_filename = f"{run_id}_original.mp4"
        original_filepath = os.path.join(media_folder, original_filename)

        # Download video
        download_video(url, original_filepath, processing_id)

        input_path = original_filepath
        output_path = os.path.join(media_folder, f"{run_id}_finished.mp4")
        concat_file = f'media/tmp/{uuid.uuid4()}_concat_list.txt'
        input_watermarked_path = f'media/tmp/{uuid.uuid4()}_input_watermarked.mp4'
        watermarked_resized_path = f'media/tmp/{uuid.uuid4()}_watermarked_resized.mp4'
        postroll_resized_path = f'media/tmp/{uuid.uuid4()}_postroll_resized.mp4'

        watermark_path = 'assets/watermark.mov'
        postroll_path = 'assets/postroll.mp4'
        primary_color = '#181D2B'

        if not os.path.exists(watermark_path):
            logger.error(f"[{processing_id}] Watermark file not found: {watermark_path}")
            raise FileNotFoundError('Watermark file not found')

        if not os.path.exists(postroll_path):
            logger.error(f"[{processing_id}] Postroll file not found: {postroll_path}")
            raise FileNotFoundError('Postroll file not found')

        logger.info(f"[{processing_id}] File paths - input: {input_path}, output: {output_path}, watermark: {watermark_path}, postroll: {postroll_path}")

        if not os.path.exists(input_path) or os.path.getsize(input_path) == 0:
            logger.error(f"[{processing_id}] Downloaded file is empty or missing: {input_path}")
            raise ValueError('Downloaded video file is empty')

        logger.info(f"[{processing_id}] Getting input video dimensions")
        probe_cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json',
            '-show_streams', input_path
        ]
        probe_result = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
        probe_data = json.loads(probe_result.stdout)

        input_width = None
        input_height = None
        for stream in probe_data['streams']:
            if stream['codec_type'] == 'video':
                input_width = int(stream['width'])
                input_height = int(stream['height'])
                break

        if not input_width or not input_height:
            logger.error(f"[{processing_id}] Could not determine input video dimensions")
            raise ValueError('Could not determine video dimensions')

        logger.info(f"[{processing_id}] Input video dimensions: {input_width}x{input_height}")

        target_width = input_width
        target_height = input_height

        logger.info(f"[{processing_id}] Target dimensions: {target_width}x{target_height}")

        watermark_width = int(target_width * 0.85)
        margin_bottom = int(target_height * 0.05)  # 5% margin from bottom

        logger.info(f"[{processing_id}] Adding watermark to input video")
        watermark_cmd = [
            'ffmpeg', '-i', input_path, '-stream_loop', '-1', '-i', watermark_path,
            '-filter_complex',
            f'[1:v]scale={watermark_width}:-1[watermark];[0:v][watermark]overlay=(W-w)/2:H-h-{margin_bottom}:enable=gte(t\\,1):shortest=1',
            '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
            '-c:a', 'aac', '-b:a', '128k',
            '-r', '30', '-g', '60',
            input_watermarked_path, '-y'
        ]
        await run_ffmpeg_command_async(watermark_cmd, processing_id)
        logger.info(f"[{processing_id}] Watermark added successfully")

        logger.info(f"[{processing_id}] Resizing watermarked video with padding")
        watermarked_resize_cmd = [
            'ffmpeg', '-i', input_watermarked_path,
            '-vf', f'scale={target_width}:{target_height}:force_original_aspect_ratio=decrease,pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2:color={primary_color}',
            '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
            '-c:a', 'aac', '-b:a', '128k',
            '-r', '30', '-g', '60',
            watermarked_resized_path, '-y'
        ]
        await run_ffmpeg_command_async(watermarked_resize_cmd, processing_id)
        logger.info(f"[{processing_id}] Watermarked video resized successfully")

        logger.info(f"[{processing_id}] Resizing postroll video with padding")
        postroll_resize_cmd = [
            'ffmpeg', '-i', postroll_path,
            '-vf', f'scale={target_width}:{target_height}:force_original_aspect_ratio=decrease,pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2:color={primary_color}',
            '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
            '-c:a', 'aac', '-ar', '44100', '-b:a', '128k',
            '-r', '30', '-g', '60',
            postroll_resized_path, '-y'
        ]
        await run_ffmpeg_command_async(postroll_resize_cmd, processing_id)
        logger.info(f"[{processing_id}] Postroll video resized successfully")

        logger.info(f"[{processing_id}] Creating concat file")
        with open(concat_file, 'w') as f:
            f.write(f"file '{os.path.abspath(watermarked_resized_path)}'\n")
            f.write(f"file '{os.path.abspath(postroll_resized_path)}'\n")

        # Log concat file contents for debugging
        with open(concat_file, 'r') as f:
            concat_contents = f.read()
            logger.info(f"[{processing_id}] Concat file contents:\n{concat_contents}")

        cmd = [
            'ffmpeg',
            '-f', 'concat',
            '-safe', '0',
            '-i', concat_file,
            '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
            '-c:a', 'aac', '-b:a', '128k',
            '-movflags', '+faststart',
            output_path,
            '-y'
        ]

        await run_ffmpeg_command_async(cmd, processing_id)

        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            logger.error(f"[{processing_id}] Output file is empty or missing: {output_path}")
            raise ValueError('Video processing failed')

        logger.info(f"[{processing_id}] Cleaning up temporary files")
        for file in [concat_file, input_watermarked_path, watermarked_resized_path, postroll_resized_path]:
            if file and os.path.exists(file):
                os.remove(file)
                logger.info(f"[{processing_id}] Removed temporary file: {file}")

        logger.info(f"[{processing_id}] Video processing completed successfully. Final file: {output_path}")

        # Upload to bucket
        logger.info(f"[{processing_id}] Uploading to public bucket")
        processed_filename = f"{run_id}_finished.mp4"
        public_url = await upload_to_bucket(output_path, processed_filename)

        logger.info(f"[{processing_id}] Processing complete. Public URL: {public_url}")
        return {
            'status': 'success',
            'message': 'Video processed successfully with watermark and postroll',
            'original_file': original_filename,
            'processed_file': processed_filename,
            'public_url': public_url
        }

    except Exception as e:
        logger.error(f"[{processing_id}] Error processing video: {str(e)}", exc_info=True)
        raise
    finally:
        try:
            for file in [concat_file, input_watermarked_path, watermarked_resized_path, postroll_resized_path]:
                if file and os.path.exists(file):
                    os.remove(file)
                    logger.info(f"[{processing_id}] Cleaned up temporary file after processing: {file}")
            # Cleanup local files if they still exist
            #for file in [input_path, output_path]:
            #    if file and os.path.exists(file):
            #        os.remove(file)
            #        logger.info(f"[{processing_id}] Cleaned up local file: {file}")
        except Exception as cleanup_error:
            logger.warning(f"[{processing_id}] Failed to cleanup files: {cleanup_error}")

async def queue_processor():
    """Background task that processes videos from the queue"""
    global queue_processor_running
    logger = logging.getLogger(__name__)
    logger.info("Queue processor started")
    queue_processor_running = True

    while queue_processor_running:
        try:
            # Wait for items with a timeout to allow graceful shutdown
            try:
                data = await asyncio.wait_for(processing_queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue

            logger.info(f"Processing item from queue: {data.get('run_id')}")

            # Process the video directly and await completion
            await process_video_item(data)

        except asyncio.CancelledError:
            logger.info("Queue processor cancelled")
            break
        except Exception as e:
            logger.error(f"Error in queue processor: {str(e)}", exc_info=True)
            # Continue processing other items

    logger.info("Queue processor stopped")

async def process_video_item(data):
    """Wrapper to process individual video items and handle queue cleanup"""
    logger = logging.getLogger(__name__)
    try:
        # Process the video
        await process_video_task(data)

        # Mark task as done and update file
        processing_queue.task_done()
        save_queue_to_file()

    except Exception as e:
        logger.error(f"Error processing video item: {str(e)}", exc_info=True)
        processing_queue.task_done()
        save_queue_to_file()

def create_app():
    app = Quart(__name__)

    app.secret_key = 'Zr8pIKMOV+yrNiJ2MesAO4ch'

    @app.before_request
    async def log_request_info():
        ip = get_real_ip()
        logging.info(f'Request from IP: {ip} - Path: {request.path}')

    @app.before_serving
    async def startup():
        # Load queue from file first
        await load_queue_from_file()
        # Start the queue processor as a background task
        asyncio.create_task(queue_processor())

    app.errorhandler(404)(page_not_found)

    @app.route('/webhook', methods=['POST'])
    async def webhook():
        logger = logging.getLogger(__name__)

        try:
            data = await request.get_json()

            if not data:
                return jsonify({'status': 'error', 'message': 'No JSON data provided'}), 400

            url = data.get('url')
            run_id = data.get('run_id')

            if not url or not run_id:
                return jsonify({'status': 'error', 'message': 'Both url and uuid are required'}), 400

            logger.info(f'Webhook received - URL: {url}, UUID: {run_id}')

            # Get queue size before adding the new item
            queue_size_before = processing_queue.qsize()

            # Add to processing queue with persistence
            await add_to_queue_with_persistence(data)

            # Queue position is the size before adding + 1
            queue_position = queue_size_before + 1

            logger.info(f'Added to processing queue. Queue position: {queue_position}')

            return jsonify({
                'status': 'queued',
                'message': 'Video added to processing queue',
                'run_id': run_id,
                'queue_position': queue_position
            }), 202

        except Exception as e:
            logger.error(f"Error handling webhook: {str(e)}", exc_info=True)
            return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

    @app.route('/queue/status', methods=['GET'])
    async def queue_status():
        """Endpoint to check queue status"""
        return jsonify({
            'queue_size': processing_queue.qsize(),
            'status': 'running' if queue_processor_running else 'stopped'
        })

    return app
