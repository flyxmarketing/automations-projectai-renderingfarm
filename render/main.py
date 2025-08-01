import os
import subprocess
import json
import logging
import time
import requests

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def run_ffmpeg_command(cmd):
    logger.info(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error(f"FFmpeg error: {result.stderr}")
        raise subprocess.CalledProcessError(result.returncode, cmd, result.stderr)
    return result

def upload_render(archive_id, item_id):
    logger.info(f"Uploading render for item {item_id}")
    try:
        webhook_url = "https://automations.flyxmarketing.com/api/v1/webhooks/imI7XJaffmV9Q7qYNfFBH"
        item_url_original = f"https://example.com/item/{item_id}"
        item_url_rendered = f"https://example.com/item/{item_id}/render"
        item_url_rendered_thumbnail = f"https://example.com/item/{item_id}/render/thumbnail"
        body = {
            "archive_id": archive_id,
            "item_id": item_id,
            "item_url_original": item_url_original,
            "item_url_rendered": item_url_rendered,
            "item_url_rendered_thumbnail": item_url_rendered_thumbnail
        }
        response = requests.post(webhook_url, json=body)
        logger.info(f"Webhook response status: {response.status_code}")
    except Exception as e:
        logger.error(f"Failed to send webhook: {e}")

def report_status(archive_id, item_id, status):
    logger.info(f"Informing about render for item {item_id}")
    try:
        webhook_url = "https://automations.flyxmarketing.com/api/v1/webhooks/Wu2THyojY4nBkFw3kFZSO"
        body = {
            "archive_id": archive_id,
            "item_id": item_id,
            "status": status
        }
        response = requests.post(webhook_url, json=body)
        logger.info(f"Webhook response status: {response.status_code}")
    except Exception as e:
        logger.error(f"Failed to send webhook: {e}")

def main():
    logger.info("Searching for files to render")

    try:
        with open('/media/queue.json', 'r') as f:
            queue_data = json.load(f)

        for item in queue_data:
            if item.get("status") == "queued":
                logger.info(f"Found item to render: {item}")
                item_id = item.get("request_uuid")
                item["status"] = "processing"
                with open('/media/queue.json', 'w') as f:
                    json.dump(queue_data, f, indent=2)
                logger.info(f"Item {item_id} marked as processing.")

                report_status(item.get("archive_id"), item_id, "processing")

                input_path = item.get("video_filepath")
                watermark_path = "/code/assets/watermark.mov"
                postroll_path = "/code/assets/postroll.mp4"
                output_path = f"/media/processed/{item_id}.mp4"
                primary_color = "#000000"

                input_watermarked_path = f"/media/queue/tmp/{item_id}_watermarked.mp4"
                watermarked_resized_path = f"/media/queue/tmp/{item_id}_watermarked_resized.mp4"
                postroll_resized_path = f"/media/queue/tmp/{item_id}_postroll_resized.mp4"
                concat_file = f"/media/queue/tmp/{item_id}_concat.txt"

                logger.info("Getting input video dimensions")
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
                    logger.error("Could not determine input video dimensions")
                    raise ValueError('Could not determine video dimensions')

                logger.info(f"Input video dimensions: {input_width}x{input_height}")

                target_width = input_width
                target_height = input_height

                logger.info(f"Target dimensions: {target_width}x{target_height}")

                watermark_width = int(target_width * 0.85)
                margin_bottom = int(target_height * 0.05)  # 5% margin from bottom

                logger.info("Adding watermark to input video")
                watermark_cmd = [
                    'ffmpeg', '-i', input_path, '-stream_loop', '-1', '-i', watermark_path,
                    '-filter_complex',
                    f'[1:v]scale={watermark_width}:-1[watermark];[0:v][watermark]overlay=(W-w)/2:H-h-{margin_bottom}:enable=gte(t\\,1):shortest=1',
                    '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
                    '-c:a', 'aac', '-b:a', '128k',
                    '-r', '30', '-g', '60',
                    input_watermarked_path, '-y'
                ]
                run_ffmpeg_command(watermark_cmd)
                logger.info("Watermark added successfully")

                logger.info("Resizing watermarked video with padding")
                watermarked_resize_cmd = [
                    'ffmpeg', '-i', input_watermarked_path,
                    '-vf', f'scale={target_width}:{target_height}:force_original_aspect_ratio=decrease,pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2:color={primary_color}',
                    '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
                    '-c:a', 'aac', '-b:a', '128k',
                    '-r', '30', '-g', '60',
                    watermarked_resized_path, '-y'
                ]
                run_ffmpeg_command(watermarked_resize_cmd)
                logger.info("Watermarked video resized successfully")

                logger.info("Resizing postroll video with padding")
                postroll_resize_cmd = [
                    'ffmpeg', '-i', postroll_path,
                    '-vf', f'scale={target_width}:{target_height}:force_original_aspect_ratio=decrease,pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2:color={primary_color}',
                    '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
                    '-c:a', 'aac', '-ar', '44100', '-b:a', '128k',
                    '-r', '30', '-g', '60',
                    postroll_resized_path, '-y'
                ]
                run_ffmpeg_command(postroll_resize_cmd)
                logger.info("Postroll video resized successfully")

                logger.info("Creating concat file")
                with open(concat_file, 'w') as f:
                    f.write(f"file '{os.path.abspath(watermarked_resized_path)}'\n")
                    f.write(f"file '{os.path.abspath(postroll_resized_path)}'\n")

                # Log concat file contents for debugging
                with open(concat_file, 'r') as f:
                    concat_contents = f.read()
                    logger.info(f"Concat file contents:\n{concat_contents}")

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

                run_ffmpeg_command(cmd)

                logger.info("Creating thumbnail for the final video")
                thumbnail_path = f"/media/processed/{item_id}_thumbnail.jpg"
                thumbnail_cmd = [
                    'ffmpeg', '-i', input_path,
                    '-ss', '00:00:01',
                    '-vframes', '1',
                    '-vf', 'scale=1080:1080:force_original_aspect_ratio=decrease,pad=1080:1080:(ow-iw)/2:(oh-ih)/2:color=black',
                    '-q:v', '2',
                    thumbnail_path, '-y'
                ]
                run_ffmpeg_command(thumbnail_cmd)
                logger.info("Thumbnail created successfully")

                os.remove(input_watermarked_path)
                os.remove(watermarked_resized_path)
                os.remove(postroll_resized_path)
                os.remove(concat_file)

                original_filename = os.path.basename(input_path)
                original_destination = f"/media/original/{original_filename}"

                logger.info(f"Moving input file from {input_path} to {original_destination}")
                os.rename(input_path, original_destination)
                logger.info("Input file moved to originals directory")

                if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
                    logger.error(f"Output file is empty or missing: {output_path}")
                    item["status"] = "failed"
                    with open('/media/queue.json', 'w') as f:
                        json.dump(queue_data, f, indent=2)
                    report_status(item.get("archive_id"), item_id, "failed")
                    raise ValueError('Video processing failed')

                logger.info("Video processing completed successfully")

                upload_render(item.get("archive_id"), item_id)

                item["status"] = "completed"
                with open('/media/queue.json', 'w') as f:
                    json.dump(queue_data, f, indent=2)
                logger.info(f"Item {item_id} marked as completed")

                break

    except FileNotFoundError:
        logger.error("Queue file not found: /media/queue.json")
    except json.JSONDecodeError:
        logger.error("Invalid JSON in queue file")
    except Exception as e:
        logger.error(f"Error reading queue file: {e}")


if __name__ == "__main__":
    logger.info("Starting render server")
    while True:
        main()
        time.sleep(120)
