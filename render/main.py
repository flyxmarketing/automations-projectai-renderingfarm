import os
import subprocess
import json
import logging
import time
import requests
from rclone_python import rclone

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def run_ffmpeg_command(cmd):
    logger.info(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error(f"FFmpeg error: {result.stderr}")
        raise subprocess.CalledProcessError(result.returncode, cmd, result.stderr)
    return result

def run_ffmpeg_watermark(input_path, watermark_path, watermark_width, margin_bottom, input_watermarked_path):
    cmd = [
        'ffmpeg', '-i', input_path, '-stream_loop', '-1', '-i', watermark_path,
        '-filter_complex',
        f'[1:v]scale={watermark_width}:-1[watermark];[0:v][watermark]overlay=(W-w)/2:H-h-{margin_bottom}:enable=gte(t\\,3):shortest=1',
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
        '-c:a', 'aac', '-b:a', '128k',
        '-r', '30', '-g', '60',
        input_watermarked_path, '-y'
    ]
    return run_ffmpeg_command(cmd)

def run_ffmpeg_watermark_fixed(input_path, watermark_path, fixed_width, fixed_height, margin_bottom, input_watermarked_path):
    # This function keeps watermark fixed in size, regardless of video width
    cmd = [
        'ffmpeg', '-i', input_path, '-stream_loop', '-1', '-i', watermark_path,
        '-filter_complex',
        f'[1:v]scale={fixed_width}:{fixed_height}[watermark];[0:v][watermark]overlay=(W-w)/2:H-h-{margin_bottom}:enable=gte(t\\,3):shortest=1',
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
        '-c:a', 'aac', '-b:a', '128k',
        '-r', '30', '-g', '60',
        input_watermarked_path, '-y'
    ]
    return run_ffmpeg_command(cmd)

def run_ffmpeg_resize(input_path, target_width, target_height, primary_color, output_path):
    cmd = [
        'ffmpeg', '-i', input_path,
        '-vf', f'scale={target_width}:{target_height}:force_original_aspect_ratio=decrease,pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2:color={primary_color}',
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
        '-c:a', 'aac', '-b:a', '128k',
        '-r', '30', '-g', '60',
        output_path, '-y'
    ]
    return run_ffmpeg_command(cmd)

def run_ffmpeg_resize_postroll(input_path, target_width, target_height, primary_color, output_path):
    cmd = [
        'ffmpeg', '-i', input_path,
        '-vf', f'scale={target_width}:{target_height}:force_original_aspect_ratio=decrease,pad={target_width}:{target_height}:(ow-iw)/2:(oh-ih)/2:color={primary_color}',
        '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
        '-c:a', 'aac', '-ar', '44100', '-b:a', '128k',
        '-r', '30', '-g', '60',
        output_path, '-y'
    ]
    return run_ffmpeg_command(cmd)

def run_ffmpeg_concat(concat_file, output_path):
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
    return run_ffmpeg_command(cmd)

def run_ffmpeg_thumbnail(input_path, thumbnail_path):
    cmd = [
        'ffmpeg', '-i', input_path,
        '-ss', '00:00:01',
        '-vframes', '1',
        '-vf', 'scale=1080:1080:force_original_aspect_ratio=decrease,pad=1080:1080:(ow-iw)/2:(oh-ih)/2:color=black',
        '-q:v', '2',
        thumbnail_path, '-y'
    ]
    return run_ffmpeg_command(cmd)

def run_ffmpeg_hflip(input_path, output_path):
    logger.info(f"Flipping video horizontally: {input_path} -> {output_path}")
    cmd = [
        "ffmpeg", "-i", input_path,
        "-vf", "hflip",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-r", "30", "-g", "60",
        output_path, "-y"
    ]
    return run_ffmpeg_command(cmd)

def run_ffmpeg_invisible_noise(input_path, output_path, strength=0.008):
    logger.info(f"Adding invisible noise to video: {input_path} -> {output_path} (strength={strength})")
    cmd = [
        "ffmpeg", "-i", input_path,
        "-vf", f"noise=alls={strength}:allf=t+u",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "copy",
        "-r", "30", "-g", "60",
        output_path, "-y"
    ]
    return run_ffmpeg_command(cmd)

def upload_render(archive_id, item_id):
    logger.info(f"Uploading render for item {item_id}")
    try:
        rclone.set_config_file("/root/.config/rclone/rclone.conf")
        rclone.copyto(f"/media/original/{item_id}.mp4",f"storage:{archive_id}/{item_id}/original.mp4")
        rclone.copyto(f"/media/processed/{item_id}.mp4",f"storage:{archive_id}/{item_id}/render.mp4")
        rclone.copyto(f"/media/processed/{item_id}_thumbnail.jpg",f"storage:{archive_id}/{item_id}/thumbnail.jpg")
        webhook_url = "https://automations.flyxmarketing.com/api/v1/webhooks/imI7XJaffmV9Q7qYNfFBH"
        item_url_original = f"https://rf-storage.flyxmarketing.com/{archive_id}/{item_id}/original.mp4"
        item_url_rendered = f"https://rf-storage.flyxmarketing.com/{archive_id}/{item_id}/render.mp4"
        item_url_rendered_thumbnail = f"https://rf-storage.flyxmarketing.com/{archive_id}/{item_id}/thumbnail.jpg"
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
                watermark_path = "/media/assets/watermark.mov"
                postroll_path = "/media/assets/postroll.mp4"
                output_path = f"/media/processed/{item_id}.mp4"
                primary_color = "#000000"

                hflip_path = f"/media/queue/tmp/{item_id}_hflip.mp4"
                input_watermarked_path = f"/media/queue/tmp/{item_id}_watermarked.mp4"
                watermarked_resized_path = f"/media/queue/tmp/{item_id}_watermarked_resized.mp4"
                postroll_resized_path = f"/media/queue/tmp/{item_id}_postroll_resized.mp4"
                concat_file = f"/media/queue/tmp/{item_id}_concat.txt"
                output_with_noise_path = f"/media/processed/{item_id}_noised.mp4"

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

                aspect_ratio = input_width / input_height if input_height != 0 else 0
                is_instagram_reel = abs(aspect_ratio - 9/16) < 0.05  # Tolerance for rounding errors

                if is_instagram_reel:
                    watermark_width = int(target_width * 0.75)
                    margin_bottom = int(target_height * 0.03)
                else:
                    watermark_width = int(target_width * 0.75)
                    margin_bottom = int(target_height * 0.03)

                mirror = item.get("mirror", False)
                if mirror:
                    logger.info("Mirror flag is True. Flipping original input video horizontally")
                    run_ffmpeg_hflip(
                        input_path,
                        hflip_path
                    )
                    logger.info("Original video flipped successfully")
                    watermark_input_path = hflip_path
                else:
                    logger.info("Mirror flag is False. Skipping horizontal flip.")
                    watermark_input_path = input_path

                logger.info("Adding watermark to video")
                if is_instagram_reel:
                    run_ffmpeg_watermark(
                        watermark_input_path,
                        watermark_path,
                        watermark_width,
                        margin_bottom,
                        input_watermarked_path
                    )
                else:
                    run_ffmpeg_watermark_fixed(
                        watermark_input_path,
                        watermark_path,
                        watermark_width,
                        watermark_height,
                        margin_bottom,
                        input_watermarked_path
                    )
                logger.info("Watermark added successfully")

                input_for_resize = input_watermarked_path

                logger.info("Resizing watermarked video with padding")
                run_ffmpeg_resize(
                    input_for_resize,
                    target_width,
                    target_height,
                    primary_color,
                    watermarked_resized_path
                )
                logger.info("Watermarked video resized successfully")

                postroll_enabled = os.path.exists(postroll_path) and os.path.getsize(postroll_path) > 0

                if postroll_enabled:
                    logger.info("Resizing postroll video with padding")
                    run_ffmpeg_resize_postroll(
                        postroll_path,
                        target_width,
                        target_height,
                        primary_color,
                        postroll_resized_path
                    )
                    logger.info("Postroll video resized successfully")

                    logger.info("Creating concat file with watermarked and postroll video")
                    with open(concat_file, 'w') as f:
                        f.write(f"file '{os.path.abspath(watermarked_resized_path)}'\n")
                        f.write(f"file '{os.path.abspath(postroll_resized_path)}'\n")

                else:
                    logger.warning("Postroll video not found. Skipping postroll concatenation, only using watermarked video.")
                    # Only the watermarked_resized video in concat file
                    with open(concat_file, 'w') as f:
                        f.write(f"file '{os.path.abspath(watermarked_resized_path)}'\n")

                with open(concat_file, 'r') as f:
                    concat_contents = f.read()
                    logger.info(f"Concat file contents:\n{concat_contents}")

                run_ffmpeg_concat(concat_file, output_path)

                logger.info("Adding invisible noise to the final concatenated video")
                run_ffmpeg_invisible_noise(output_path, output_with_noise_path)
                logger.info("Invisible noise added successfully")

                logger.info("Creating thumbnail for the final video")
                thumbnail_path = f"/media/processed/{item_id}_thumbnail.jpg"
                run_ffmpeg_thumbnail(input_path, thumbnail_path)
                logger.info("Thumbnail created successfully")

                os.remove(input_watermarked_path)
                if mirror:
                    os.remove(hflip_path)
                os.remove(watermarked_resized_path)
                if postroll_enabled:
                    os.remove(postroll_resized_path)
                os.remove(concat_file)
                os.remove(output_path)  # Remove the un-noised concatenated output

                original_filename = os.path.basename(input_path)
                original_destination = f"/media/original/{original_filename}"

                logger.info(f"Moving input file from {input_path} to {original_destination}")
                os.rename(input_path, original_destination)
                logger.info("Input file moved to originals directory")

                if not os.path.exists(output_with_noise_path) or os.path.getsize(output_with_noise_path) == 0:
                    logger.error(f"Output file is empty or missing: {output_with_noise_path}")
                    item["status"] = "failed"
                    with open('/media/queue.json', 'w') as f:
                        json.dump(queue_data, f, indent=2)
                    report_status(item.get("archive_id"), item_id, "failed")
                    raise ValueError('Video processing failed')

                logger.info("Video processing completed successfully")

                os.rename(output_with_noise_path, output_path)

                upload_render(item.get("archive_id"), item_id)

                os.remove(thumbnail_path)
                os.remove(original_destination)
                os.remove(output_path)

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
