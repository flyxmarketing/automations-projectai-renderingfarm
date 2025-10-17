import os
import time
import random

from libs.postgres.init import db_cursor, db_execute, db_close
from libs.ffmpeg.commands_manual import run_ffprobe
from libs.ffmpeg.init import render_run
from libs.s3.init import uploadFile

def main():
    bucket_endpoint = "https://rf-storage.flyxmarketing.com/"
    db = db_cursor()
    queue_query = db_execute(db,"SELECT * FROM public.render_queue WHERE render_status='queued' ORDER BY id ASC LIMIT 1;")
    queue_info = queue_query.fetchone()
    if queue_info:
        input = queue_info['url_archive']
        id_archive = queue_info['id_archive']
        queue_id = queue_info['id']
        db_execute(db,f"UPDATE public.render_queue SET render_status='processing' WHERE id = {str(queue_id)};")
        print(f'###### Format for {id_archive} STARTING')
        steps_count = len(queue_info['render_steps'])
        count = 0
        original_name, original_ext = queue_info['url_archive'].rsplit('.', 1)
        original_data = run_ffprobe(input)
        input_width = None
        input_height = None
        input_bitrate = None
        input_duration = None
        for stream in original_data['streams']:
            if stream['codec_type'] == 'video':
                input_width = int(stream['width'])
                input_height = int(stream['height'])
                input_bitrate = int(stream['bit_rate'])
                input_duration = float(stream['duration'])
                break
        if not input_width or not input_height:
            db_execute(db,f"UPDATE public.render_queue SET render_status='error', render_status_text='Could not determine video dimensions' WHERE id = {str(queue_id)};")
            raise Exception('Could not determine video dimensions')
        localFiles = []
        steps_count = len(queue_info['render_steps'])
        print(f'#### {queue_id} requires {steps_count} transformations.')
        for step in queue_info['render_steps']:
            print(f'#### {queue_id} step {count} [{step}] starting')
            db_execute(db,f"UPDATE public.render_queue SET render_status_text='{count} of {steps_count} [{step}]' WHERE id = {str(queue_id)};")
            if count == 0:
                name, ext = input.rsplit('.', 1)
            else:
                name, ext = localFiles[-1].rsplit('.', 1)
            output_local = '/tmp/' + str(queue_id) + '_' + str(count) + '.' + ext
            renderProcess = render_run(input,output_local, step, {'input_width': input_width, 'input_height': input_height, 'input_bitrate': input_bitrate, 'input_duration': input_duration})
            if renderProcess:
                input = renderProcess
                count = count + 1
                localFiles.append(input)
                print(f'#### {queue_id} step {count - 1} [{step}] ended')
                if count == steps_count:
                    final_name, final_ext = output_local.rsplit('.', 1)
                    output_final = 'rbucket/' + id_archive + '/final' + '.' + final_ext
                    if uploadFile(output_final,output_local):
                        db_execute(db,f"UPDATE public.render_queue SET render_status='finished',render_status_text='Processing Finished',render_final_url='{bucket_endpoint}{output_final}' WHERE id = {str(queue_id)};")
                        print(f'###### Format for {queue_id} FINISHED')
                        for localFile in localFiles:
                            os.remove(localFile)
            else:
                db_execute(db,f"UPDATE public.render_queue SET render_status='error',render_status_text='Failed to execute step {step}, check logs for more information.' WHERE id = {str(queue_id)};")
                print(renderProcess)
                break
    db_close(db)

if __name__ == "__main__":
    while True:
        main()
        sleep_for = 30 + random.randint(0, 60)
        print(f"##### Sleeping for {sleep_for} seconds")
        time.sleep(sleep_for)
