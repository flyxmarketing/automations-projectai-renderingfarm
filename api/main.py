import os
import uuid
import json

from quart import Quart, jsonify, request
from datetime import datetime

from libs.downloader.init import downloadVideo
from libs.s3.init import uploadFile
from libs.postgres.init import db_cursor, db_execute, db_close

def create_app():
    app = Quart(__name__)
    app.secret_key = 'Zr8pIKMOV+yrNiJ2MesAO4ch'
    @app.route('/queueRender', methods=['POST'])
    async def webhook():
        print("===== Request for adding item to queue received.")
        request_uuid = uuid.uuid4()
        try:
            data = await request.get_json()
            if not data:
                print("===== Request was invalid")
                return jsonify({'status': 'error', 'message': 'No JSON data provided'}), 400
            id_archive = data.get('id_archive')
            id_run = data.get('id_run')
            id_bot = data.get('id_bot')
            url_post = data.get('url_post')
            render_steps = data.get('render_steps')
            if not id_archive or not id_run or not id_bot or not url_post or not render_steps:
                print("===== Request failed with missing parameters")
                return jsonify({'status': 'error', 'message': 'Missing parameters'}), 400
            video_filename = f"{request_uuid}.mp4"
            video_filepath = f"/tmp/{video_filename}"
            try:
                downloadVideo(url_post, video_filepath)
            except Exception:
                print("===== Request failed to download video")
                return jsonify({'status': 'error', 'message': 'Failed to download video'}), 500
            if uploadFile(f"{id_archive}/original.mp4",video_filepath):
                os.remove(video_filepath)
                url_archive = f"https://rf-storage.flyxmarketing.com/{id_archive}/original.mp4"
                render_steps_json = json.dumps(render_steps)
                current_timestamp = datetime.now()
                db_link = db_cursor()
                insert_result = db_execute(db_link, "INSERT INTO public.render_queue (id_archive,id_run,id_bot,url_post,url_archive,render_steps,render_status,render_status_text,date_added) VALUES (%s,%s,%s,%s,%s,%s,'queued','Waiting for Node to be available',%s) RETURNING *;", (id_archive, id_run, id_bot, url_post, url_archive, render_steps_json, current_timestamp))
                queue_info = insert_result.fetchone()
                db_close(db_link)
                if insert_result:
                    print(f"===== Request queued with position {queue_info['id']}.")
                    return jsonify({
                        'status': 'queued',
                        'message': 'Video added to queue',
                        'queue_position': queue_info['id']
                    }), 202
                else:
                    print("===== Request failed to insert into database")
                    return jsonify({'status': 'error', 'message': 'Failed to insert into database'}), 500
            else:
                print("===== Request failed to upload original video")
                return jsonify({'status': 'error', 'message': 'Failed to upload original video'}), 500
        except Exception as e:
            print(f"===== Request failed. {e}")
            return jsonify({'status': 'error', 'message': f'Internal server error. {e}'}), 500

    @app.route('/getStatus/<id>',methods=['GET'])
    async def getStatus(id):
        print(f"===== Request for status of {id} received.")
        try:
            db_link = db_cursor()
            result = db_execute(db_link, "SELECT * FROM public.render_queue WHERE id = %s;", (id,))
            status_info = result.fetchone()
            db_close(db_link)
            if status_info:
                status = status_info['render_status']
                if status == 'finished':
                    return jsonify({
                        'status': status_info['render_status'],
                        'message': status_info['render_status_text'],
                        'final_url': status_info['render_final_url'],
                        'logs': status_info['logs']
                    }), 200
                elif status == 'error':
                    return jsonify({
                        'status': status_info['render_status'],
                        'message': status_info['render_status_text'],
                        'logs': status_info['logs']
                    }), 200
                elif status == 'processing':
                    return jsonify({
                        'status': status_info['render_status'],
                        'message': status_info['render_status_text'],
                    }), 200
                else:
                    return jsonify({
                        'status': status_info['render_status'],
                        'message': status_info['render_status_text']
                    }), 200
            else:
                return jsonify({'status': 'error', 'message': 'ID not found'}), 404
        except Exception as e:
            return jsonify({'status': 'error', 'message': f'Internal server error. {e}'}), 500

    return app
