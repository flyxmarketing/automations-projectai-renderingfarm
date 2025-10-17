import os
import subprocess
import json

def run_ffprobe(input):
    probe_cmd = [
        'ffprobe', '-v', 'quiet', '-print_format', 'json',
        '-show_streams', input
    ]
    probe_result = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
    return json.loads(probe_result.stdout)

def run_ffmpeg(cmd):
    print(' '.join(cmd))
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result
    except Exception as e:
        return e

def do_hflip(input, output):
    cmd = [
        "ffmpeg", "-i", input,
        "-vf", "hflip",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-r", "30", "-g", "60",
        output, "-y"
    ]
    return run_ffmpeg(cmd)

def do_speed(input, output, speed_factor=1.05):
    cmd = [
        "ffmpeg", "-i", input,
        "-filter_complex", f"[0:v]setpts={1/speed_factor}*PTS[v];[0:a]atempo={speed_factor}[a]",
        "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-r", "30", "-g", "60",
        output, "-y"
    ]
    return run_ffmpeg(cmd)

def do_noise(input, output, strength=0.008):
    cmd = [
        "ffmpeg", "-i", input,
        "-vf", f"noise=alls={strength}:allf=t+u",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-r", "30", "-g", "60",
        output, "-y"
    ]
    return run_ffmpeg(cmd)

def do_zoom(input, output, input_params, zoom_factor=1.0):
    probe_data = run_ffprobe(input)
    input_width = None
    input_height = None
    for stream in probe_data.get('streams', []):
        if stream.get('codec_type') == 'video':
            input_width = int(stream.get('width'))
            input_height = int(stream.get('height'))
            break
    if zoom_factor >= 1.0:
        cmd = [
            "ffmpeg", "-i", input,
            "-vf", f"scale=iw*{zoom_factor}:ih*{zoom_factor},crop={input_width}:{input_height}",
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "aac", "-b:a", "128k",
            "-r", "30", "-g", "60",
            output, "-y"
        ]
    else:
        cmd = [
            "ffmpeg", "-i", input,
            "-vf", f"scale=iw*{zoom_factor}:ih*{zoom_factor},pad={input_width}:{input_height}:(ow-iw)/2:(oh-ih)/2:black",
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "aac", "-b:a", "128k",
            "-r", "30", "-g", "60",
            output, "-y"
        ]
    return run_ffmpeg(cmd)

def do_rotate(input, output, angle=90):
    angle_rad = angle * 3.14159265359 / 180
    cmd = [
        "ffmpeg", "-i", input,
        "-vf", f"rotate={angle_rad}:ow=iw:oh=ih:c=black",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-r", "30", "-g", "60",
        output, "-y"
    ]
    return run_ffmpeg(cmd)

def do_saturation(input, output, saturation=1.0):
    cmd = [
        "ffmpeg", "-i", input,
        "-vf", f"eq=saturation={saturation}",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-r", "30", "-g", "60",
        output, "-y"
    ]
    return run_ffmpeg(cmd)

def do_brightness(input, output, brightness=0.0):
    cmd = [
        "ffmpeg", "-i", input,
        "-vf", f"eq=brightness={brightness}",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-r", "30", "-g", "60",
        output, "-y"
    ]
    return run_ffmpeg(cmd)

def do_watermark(input, watermark_path, watermark_width, margin_bottom, output):
    cmd = [
        'ffmpeg', '-i', input, '-stream_loop', '-1', '-i', watermark_path,
        '-filter_complex',
        f'[1:v]scale={watermark_width}:-1[watermark];[0:v][watermark]overlay=(W-w)/2:H-h-{margin_bottom}:enable=gte(t\\,3):shortest=1',
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-r", "30", "-g", "60",
        output, '-y'
    ]
    return run_ffmpeg(cmd)

def do_changeformat(input,output,format="mp4"):
    cmd = [
        "ffmpeg", "-i", input,
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-r", "30", "-g", "60",
        "-f", format,
        output, "-y"
    ]
    return run_ffmpeg(cmd)

def do_changebitrate(input, output, bitrate=1.0):
    cmd = [
        "ffmpeg", "-i", input,
        "-b:v", bitrate,
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-r", "30", "-g", "60",
        output, "-y"
    ]
    return run_ffmpeg(cmd)

def do_border(input, output, border_width=10, color='black'):
    cmd = [
        "ffmpeg", "-i", input,
        "-vf", f"pad=iw+{border_width*2}:ih+{border_width*2}:{border_width}:{border_width}:{color}",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-r", "30", "-g", "60",
        output, "-y"
    ]
    return run_ffmpeg(cmd)

def do_replace_audio(input, duration, audio_path, output):
    cmd = [
        "ffmpeg", "-i", input, "-i", audio_path,
        "-filter_complex", f"[1:a]atrim=0:{duration}[a]",
        "-map", "0:v", "-map", "[a]",
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "128k",
        "-shortest",
        output, "-y"
    ]
    return run_ffmpeg(cmd)

def do_changeratio(input, output, ratio='9:16'):
    ratio_parts = ratio.split(':')
    aspect_w = int(ratio_parts[0])
    aspect_h = int(ratio_parts[1])
    cmd = [
        "ffmpeg", "-i", input,
        "-vf", f"scale=iw:iw*{aspect_h}/{aspect_w},setsar=1",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-r", "30", "-g", "60",
        output, "-y"
    ]
    return run_ffmpeg(cmd)

def do_injectratio(input, output, ratio='9:16', color="black"):
    ratio_parts = ratio.split(':')
    aspect_w = int(ratio_parts[0])
    aspect_h = int(ratio_parts[1])
    cmd = [
        "ffmpeg", "-i", input,
        "-vf", f"pad=ih*{aspect_w}/{aspect_h}:ih:(ow-iw)/2:0:{color}",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-r", "30", "-g", "60",
        output, "-y"
    ]
    return run_ffmpeg(cmd)

def do_vignette(input, output, vignette_strength=1.1):
    cmd = [
        "ffmpeg", "-i", input,
        "-vf", f"vignette={vignette_strength}",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-r", "30", "-g", "60",
        output, "-y"
    ]
    return run_ffmpeg(cmd)

def do_sticker(input, output, sticker_path, x_pos=0, y_pos=0, sticker_width=100, rotation=0):
    sticker_ext = os.path.splitext(sticker_path)[1].lower()
    x_percent = float(x_pos)
    y_percent = float(y_pos)
    x_pos_expr = f"W*{x_percent/100}-w/2"
    y_pos_expr = f"H*{y_percent/100}-h/2"
    angle_rad = float(rotation) * 3.14159265359 / 180
    rotation_filter = f"rotate={angle_rad}:ow='hypot(iw,ih)':oh=ow:c=none," if float(rotation) != 0 else ""
    if sticker_ext in ['.webm', '.mp4', '.gif', '.mov']:
        cmd = [
            "ffmpeg", "-i", input, "-stream_loop", "-1", "-i", sticker_path,
            "-filter_complex",
            f"[1:v]scale={sticker_width}:-1,{rotation_filter}format=rgba[sticker];"
            f"[0:v][sticker]overlay={x_pos_expr}:{y_pos_expr}:shortest=1",
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "aac", "-b:a", "128k",
            "-r", "30", "-g", "60",
            output, "-y"
        ]
    else:
        cmd = [
            "ffmpeg", "-i", input, "-i", sticker_path,
            "-filter_complex", f"[1:v]scale={sticker_width}:-1,{rotation_filter}format=rgba[sticker];[0:v][sticker]overlay={x_pos_expr}:{y_pos_expr}",
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "aac", "-b:a", "128k",
            "-r", "30", "-g", "60",
            output, "-y"
        ]
    return run_ffmpeg(cmd)

def do_geotags(input, output, latitude="", longitude=""):
    cmd = [
        "ffmpeg", "-i", input,
        "-metadata", f"location={latitude}{longitude}/",
        "-metadata", f"location-eng={latitude}{longitude}/",
        "-metadata:s:v", f"location={latitude}{longitude}/",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-r", "30", "-g", "60",
        output, "-y"
    ]
    return run_ffmpeg(cmd)

def do_preroll(input, output, preroll_path, params):
    probe_data = run_ffprobe(input)
    input_width = None
    input_height = None
    for stream in probe_data.get('streams', []):
        if stream.get('codec_type') == 'video':
            input_width = int(stream.get('width'))
            input_height = int(stream.get('height'))
            break
    cmd = [
        "ffmpeg", "-i", preroll_path, "-i", input,
        "-filter_complex",
        f"[0:v]scale={input_width}:{input_height}:force_original_aspect_ratio=decrease,pad={input_width}:{input_height}:(ow-iw)/2:(oh-ih)/2:black,setsar=1[preroll];"
        f"[1:v]scale={input_width}:{input_height}:force_original_aspect_ratio=decrease,pad={input_width}:{input_height}:(ow-iw)/2:(oh-ih)/2:black,setsar=1[main];"
        f"[preroll][main]concat=n=2:v=1:a=0[outv];"
        f"[0:a][1:a]concat=n=2:v=0:a=1[outa]",
        "-map", "[outv]", "-map", "[outa]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-r", "30", "-g", "60",
        output, "-y"
    ]
    return run_ffmpeg(cmd)

def do_postroll(input, output, postroll_path, params):
    probe_data = run_ffprobe(input)
    input_width = None
    input_height = None
    for stream in probe_data.get('streams', []):
        if stream.get('codec_type') == 'video':
            input_width = int(stream.get('width'))
            input_height = int(stream.get('height'))
            break
    cmd = [
        "ffmpeg", "-i", input, "-i", postroll_path,
        "-filter_complex",
        f"[0:v]scale={input_width}:{input_height}:force_original_aspect_ratio=decrease,pad={input_width}:{input_height}:(ow-iw)/2:(oh-ih)/2:black,setsar=1[main];"
        f"[1:v]scale={input_width}:{input_height}:force_original_aspect_ratio=decrease,pad={input_width}:{input_height}:(ow-iw)/2:(oh-ih)/2:black,setsar=1[postroll];"
        f"[main][postroll]concat=n=2:v=1:a=0[outv];"
        f"[0:a][1:a]concat=n=2:v=0:a=1[outa]",
        "-map", "[outv]", "-map", "[outa]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-r", "30", "-g", "60",
        output, "-y"
    ]
    return run_ffmpeg(cmd)

def do_thumbnail(input, output, params, time_percent=1.0):
    duration = float(params.get('input_duration', 0))
    time_seconds = (duration * time_percent) / 100.0
    cmd = [
        "ffmpeg", "-i", input,
        "-filter_complex",
        f"[0:v]trim=start={time_seconds}:duration=0.04,setpts=PTS-STARTPTS[thumb];"
        f"[0:v]setpts=PTS-STARTPTS[main];"
        f"[thumb][main]concat=n=2:v=1:a=0[outv]",
        "-map", "[outv]",
        "-map", "0:a",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-r", "30", "-g", "60",
        output, "-y"
    ]
    return run_ffmpeg(cmd)

def do_injectthumbnail(input, output, thumbnail_url, params):
    input_width = int(params.get('input_width'))
    input_height = int(params.get('input_height'))
    cmd = [
        "ffmpeg", "-i", thumbnail_url, "-i", input,
        "-filter_complex",
        f"[0:v]scale={input_width}:{input_height}:force_original_aspect_ratio=decrease,pad={input_width}:{input_height}:(ow-iw)/2:(oh-ih)/2:black,setpts=PTS-STARTPTS,fps=30,setpts=PTS-STARTPTS,trim=duration=0.04[thumb];"
        f"[1:v]setpts=PTS-STARTPTS[main];"
        f"[thumb][main]concat=n=2:v=1:a=0[outv]",
        "-map", "[outv]",
        "-map", "1:a",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-r", "30", "-g", "60",
        output, "-y"
    ]
    return run_ffmpeg(cmd)

def do_backgroundmusic(input, output, music_volume=0.1, music_path=None):
    cmd = [
        "ffmpeg", "-i", input, "-stream_loop", "-1", "-i", music_path,
        "-filter_complex",
        f"[1:a]volume={music_volume}[music];[0:a][music]amix=inputs=2:duration=first:dropout_transition=2:weights=1 1:normalize=0[outa]",
        "-map", "0:v",
        "-map", "[outa]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-r", "30", "-g", "60",
        "-shortest",
        output, "-y"
    ]
    return run_ffmpeg(cmd)

def do_text(input, output, text, padding_percent=10, fontsize=24, fontcolor='white', position='center'):
    text_escaped = text.replace("'", "'\\''").replace(":", "\\:")
    if ',' in position:
        pos_parts = position.split(',')
        x_percent = float(pos_parts[0])
        y_percent = float(pos_parts[1])
        x_pos = f"w*{x_percent/100}-tw/2"
        y_pos = f"h*{y_percent/100}-th/2"
    else:
        x_pos = "(w-tw)/2"
        if position == 'top':
            y_pos = f"h*{padding_percent/100}"
        elif position == 'bottom':
            y_pos = f"h-th-h*{padding_percent/100}"
        else:
            y_pos = "(h-th)/2"
    cmd = [
        "ffmpeg", "-i", input,
        "-vf", f"drawtext=text='{text_escaped}':fontsize={fontsize}:fontcolor={fontcolor}:x={x_pos}:y={y_pos}:box=0",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-r", "30", "-g", "60",
        output, "-y"
    ]
    return run_ffmpeg(cmd)

def do_textwithbg(input, output, text, padding_percent=10, fontsize=24, fontcolor='white', position='center', box_color='black', box_size=10):
    text_escaped = text.replace("'", "'\\''").replace(":", "\\:")
    if ',' in position:
        pos_parts = position.split(',')
        x_percent = float(pos_parts[0])
        y_percent = float(pos_parts[1])
        x_pos = f"w*{x_percent/100}-tw/2"
        y_pos = f"h*{y_percent/100}-th/2"
    else:
        x_pos = "(w-tw)/2"
        if position == 'top':
            y_pos = f"h*{padding_percent/100}"
        elif position == 'bottom':
            y_pos = f"h-th-h*{padding_percent/100}"
        else:
            y_pos = "(h-th)/2"
    cmd = [
        "ffmpeg", "-i", input,
        "-vf", f"drawtext=text='{text_escaped}':fontsize={fontsize}:fontcolor={fontcolor}:x={x_pos}:y={y_pos}:box=1:boxcolor={box_color}@1:boxborderw={box_size}",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-r", "30", "-g", "60",
        output, "-y"
    ]
    return run_ffmpeg(cmd)
