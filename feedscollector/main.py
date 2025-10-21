import json

from quart import Quart, jsonify, request

from libs.rapidapi.init import getInstagramReelsFromUser, getTikTokVideosFromUser, getTwitterVideosFromUser
from libs.postgres.init import db_cursor, db_execute, db_close

def create_app():
    app = Quart(__name__)
    app.secret_key = 'Zr8pIKM1V+yrNiJ2M3sAO4ch'
    @app.route('/getFeed', methods=['GET'])
    async def webhook():
        source = request.args.get('source', '')
        username = request.args.get('username', '')
        if not source or not username:
            return jsonify({'error': 'Parameters missing'}), 400
        allowed_sources = ['instagram', 'twitter', 'tiktok']
        if source not in allowed_sources:
            return jsonify({'error': 'Invalid source. Must be instagram, twitter, or tiktok'}), 400
        if source == 'instagram':
            reels = getInstagramReelsFromUser(username)
            return jsonify(reels), 200
        elif source == 'tiktok':
            posts = getTikTokVideosFromUser(username)
            return jsonify(posts), 200
        elif source == 'twitter':
            posts = getTwitterVideosFromUser(username)
            return jsonify(posts), 200
        else:
            return jsonify({'error': 'Source Not Found'}), 404

    @app.errorhandler(404)
    async def not_found(e):
        return '', 302, {'Location': 'https://botfarm.live'}

    @app.route('/')
    async def index():
        return '', 302, {'Location': 'https://botfarm.live'}

    return app
