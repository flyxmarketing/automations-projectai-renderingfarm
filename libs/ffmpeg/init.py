import os
import subprocess
import json

from .commands_manual import *

def render_run(input, output, step, params):
    match step:
        case 'hflip':
            render = do_hflip(input,output)
            if render.returncode == 0:
                return output
            else:
                return False
        case step_speed if step_speed.startswith('speed'):
            speed = float(step_speed.replace('speed', '', 1))
            render = do_speed(input,output,speed)
            if render.returncode == 0:
                return output
            else:
                return False
        case step_noise if step_noise.startswith('noise'):
            noise = float(step_noise.replace('noise','',1)) / 1000
            render = do_noise(input,output,noise)
            if render.returncode == 0:
                return output
            else:
                return False
        case step_format if step_format.startswith('format'):
            format = str(step_format.replace('format','',1))
            output = os.path.splitext(output)[0] + '.' + format
            render = do_changeformat(input,output,format)
            if render.returncode == 0:
                return output
            else:
                return False
        case step_bitrate if step_bitrate.startswith('bitrate'):
            bitrate = str(int(int(params.get('input_bitrate')) * float(step_bitrate.replace('bitrate','',1))))
            render = do_changebitrate(input,output,bitrate)
            if render.returncode == 0:
                return output
            else:
                return False
        case step_border if step_border.startswith('border'):
            border = int(step_border.replace('border','',1))
            render = do_border(input,output,border,'black')
            if render.returncode == 0:
                return output
            else:
                return False
        case step_wborder if step_wborder.startswith('wborder'):
            border = int(step_wborder.replace('wborder','',1))
            render = do_border(input,output,border,'white')
            if render.returncode == 0:
                return output
            else:
                return False
        case step_vignette if step_vignette.startswith('vignette'):
            vignette = float(step_vignette.replace('vignette','',1))
            render = do_vignette(input,output,vignette)
            if render.returncode == 0:
                return output
            else:
                return False
        case step_saturation if step_saturation.startswith('saturation'):
            saturation = float(step_saturation.replace('saturation','',1))
            render = do_saturation(input,output,saturation)
            if render.returncode == 0:
                return output
            else:
                return False
        case step_brightness if step_brightness.startswith('brightness'):
            brightness = float(step_brightness.replace('brightness','',1))
            render = do_brightness(input,output,brightness)
            if render.returncode == 0:
                return output
            else:
                return False
        case step_zoom if step_zoom.startswith('zoom'):
            zoom = float(step_zoom.replace('zoom','',1))
            render = do_zoom(input,output,params,zoom)
            if render.returncode == 0:
                return output
            else:
                return False
        case step_rotate if step_rotate.startswith('rotate'):
            rotate = int(step_rotate.replace('rotate','',1))
            render = do_rotate(input,output,rotate)
            if render.returncode == 0:
                return output
            else:
                return False
        case step_watermark if step_watermark.startswith('watermark'):
            watermark = int(step_watermark.replace('watermark','',1))
            watermark_path = ''
            watermark_width = 0
            margin_bottom = 0
            match watermark:
                case 1:
                    watermark_path = 'https://rf-storage.flyxmarketing.com/watermarks/watermark_v1.mov'
                    watermark_width = int(params.get('input_width') * 0.75)
                    margin_bottom = "-" + params.get('input_height') * 0.03
                case 2:
                    watermark_path = 'https://rf-storage.flyxmarketing.com/watermarks/watermark_v2.mov'
                    watermark_width = int(params.get('input_width') * 0.55)
                    margin_bottom = "-" + params.get('input_height') * 0.03
                case 6:
                    watermark_path = 'https://rf-storage.flyxmarketing.com/watermarks/watermark_20251126_v6.mov'
                    watermark_width = int(params.get('input_width') * 0.75)
                    margin_bottom = "+70"
                case 7:
                    watermark_path = 'https://rf-storage.flyxmarketing.com/watermarks/watermark_20251126_v7.mov'
                    watermark_width = int(params.get('input_width') * 0.75)
                    margin_bottom = "+70"
                case 8:
                    watermark_path = 'https://rf-storage.flyxmarketing.com/watermarks/watermark_20251126_v8.mov'
                    watermark_width = int(params.get('input_width') * 0.75)
                    margin_bottom = "+70"
                case 9:
                    watermark_path = 'https://rf-storage.flyxmarketing.com/watermarks/watermark_20251201_v1.mov'
                    watermark_width = int(params.get('input_width') * 0.75)
                    margin_bottom = "+70"
                case 10:
                    watermark_path = 'https://rf-storage.flyxmarketing.com/watermarks/watermark_20251201_v2.mov'
                    watermark_width = int(params.get('input_width') * 0.75)
                    margin_bottom = "+70"
                case 11:
                    watermark_path = 'https://rf-storage.flyxmarketing.com/watermarks/watermark_20251201_v3.mov'
                    watermark_width = int(params.get('input_width') * 0.75)
                    margin_bottom = "+70"
                case _:
                    return False
            render = do_watermark(input,watermark_path,watermark_width,margin_bottom,output)
            if render.returncode == 0:
                return output
            else:
                return False
        case step_replaceaudio if step_replaceaudio.startswith('replace_audio:'):
            audio_path = step_replaceaudio.replace('replace_audio:','',1)
            render = do_replace_audio(input,params['input_duration'],audio_path,output)
            if render.returncode == 0:
                return output
            else:
                return False
        case step_backgroundmusic if step_backgroundmusic.startswith('backgroundmusic::'):
            backgroundmusic_params = step_backgroundmusic.replace('backgroundmusic::','',1)
            backgroundmusic_params_list = backgroundmusic_params.split('::')
            volume = float(int(backgroundmusic_params_list[0]) / 100)
            render = do_backgroundmusic(input,output,volume,backgroundmusic_params_list[1])
            if render.returncode == 0:
                return output
            else:
                return False
        case step_changeratio if step_changeratio.startswith('ratio'):
            ratio = step_changeratio.replace('ratio','',1)
            render = do_changeratio(input,output,ratio)
            if render.returncode == 0:
                return output
            else:
                return False
        case step_injectratio if step_injectratio.startswith('iratio'):
            ratio = step_injectratio.replace('iratio','',1)
            render = do_injectratio(input,output,ratio,'black')
            if render.returncode == 0:
                return output
            else:
                return False
        case step_sticker if step_sticker.startswith('sticker::'):
            sticker_params = step_sticker.replace('sticker::','',1)
            sticker_params_list = sticker_params.split('::')
            sticker_url = sticker_params_list[4]
            x_pos = sticker_params_list[0]
            y_pos = sticker_params_list[1]
            width = sticker_params_list[2]
            rotation = sticker_params_list[3]
            render = do_sticker(input,output,sticker_url,x_pos,y_pos,width,rotation)
            if render.returncode == 0:
                return output
            else:
                return False
        case step_geotags if step_geotags.startswith('geotags::'):
            geotags = step_geotags.replace('geotags::','',1)
            geotags_list = geotags.split('::')
            render = do_geotags(input,output,geotags_list[0],geotags_list[1])
            if render.returncode == 0:
                return output
            else:
                return False
        case step_thumbnail if step_thumbnail.startswith('thumbnail'):
            thumbnail = float(step_thumbnail.replace('thumbnail','',1))
            render = do_thumbnail(input,output,params,thumbnail)
            if render.returncode == 0:
                return output
            else:
                return False
        case step_injectthumbnail if step_injectthumbnail.startswith('injectthumbnail:'):
            thumbnail_url = step_injectthumbnail.replace('injectthumbnail:','',1)
            render = do_injectthumbnail(input,output,thumbnail_url,params)
            if render.returncode == 0:
                return output
            else:
                return False
        case step_preroll if step_preroll.startswith('preroll:'):
            preroll_path = step_preroll.replace('preroll:','',1)
            render = do_preroll(input,output,preroll_path,params)
            if render.returncode == 0:
                return output
            else:
                return False
        case step_postroll if step_postroll.startswith('postroll:'):
            postroll_path = step_postroll.replace('postroll:','',1)
            render = do_postroll(input,output,postroll_path,params)
            if render.returncode == 0:
                return output
            else:
                return False
        case step_text if step_text.startswith('text::'):
            text_params = step_text.replace('text::','',1)
            text_params_list = text_params.split('::')
            padding = int(text_params_list[0])
            font_size = int(text_params_list[1])
            position = str(text_params_list[2])
            color = str(text_params_list[3])
            text = str(text_params_list[4])
            render = do_text(input,output,text,padding,font_size,color,position)
            if render.returncode == 0:
                return output
            else:
                return False
        case step_textwithbg if step_textwithbg.startswith('textwithbg::'):
            text_params = step_textwithbg.replace('textwithbg::','',1)
            text_params_list = text_params.split('::')
            padding = int(text_params_list[0])
            font_size = int(text_params_list[1])
            position = str(text_params_list[2])
            color = str(text_params_list[3])
            text = str(text_params_list[6])
            box_color = str(text_params_list[4])
            box_size = int(text_params_list[5])
            render = do_textwithbg(input,output,text,padding,font_size,color,position,box_color,box_size)
            if render.returncode == 0:
                return output
            else:
                return False
        case _:
            return False
