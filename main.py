# api/callback.py (統合版)
import os
import json
import requests
from flask import Flask, redirect, request, jsonify, render_template_string, Response
from flask_cors import CORS
# Flaskアプリのインスタンスを作成

# Flaskアプリのインスタンスを作成
app = Flask(__name__)
CORS(app)

# --- 1. 環境変数から機密情報を読み込む ---
# Vercelの環境変数で 'SESSION_KEY' を設定する必要があります
app.secret_key = os.environ.get('SESSION_KEY', 'VERY_INSECURE_DEFAULT_KEY_CHANGE_ME')
# Vercel環境変数から各値を読み込み
FRONTEND_BASE_URI = os.environ.get('FRONTEND_URI', 'https://kakaomames.github.io')
CLIENT_ID = os.environ.get('G_CI')
CLIENT_SECRET = os.environ.get('G_CS')
REDIRECT_URI = os.environ.get('G_REDIRECT_URI') # Google Cloud Consoleに登録したVercelのURL
# リフレッシュトークン（RT）を環境変数から読み込み
REFRESH_TOKEN = os.environ.get('RT') # RTという環境変数名を使う場合
# ★★★ 追加 ★★★ 公開APIアクセス用のキー
YOUTUBE_API_KEY = os.environ.get('Y_A_K') 


INDEX_HTML = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ホームページ - pokemoguプロジェクト</title>
    <link rel="apple-touch-icon" sizes="180x180" href="https://kakaomames.github.io/Minecraft-flask-app/static/apple-touch-icon.png">
<link rel="icon" type="image/png" sizes="32x32" href="https://kakaomames.github.io/Minecraft-flask-app/static/favicon-32x32.png">
<link rel="icon" type="image/png" sizes="16x16" href="https://kakaomames.github.io/Minecraft-flask-app/static/favicon-16x16.png">
<link rel="manifest" href="https://kakaomames.github.io/Minecraft-flask-app/static/site.webmanifest">
    <link rel="stylesheet" href="https://kakaomames.github.io/Minecraft-flask-app/static/style.css">
</head>
<body>
    <header>
        <h1>HOME🏠</h1>
        <nav>
            <ul>
                <li><a href="/home">ホーム</a></li>
            </ul>
        </nav>
    </header>
    <main>
    </main>
    <footer>
        <p>&copy; 2025  pokemoguプロジェクト</p>
    </footer>
</body>
</html>
"""

HOMEHTML = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ホーム - pokemoguプロジェクト</title>
    <link rel="apple-touch-icon" sizes="180x180" href="https://kakaomames.github.io/Minecraft-flask-app/static/apple-touch-icon.png">
<link rel="icon" type="image/png" sizes="32x32" href="https://kakaomames.github.io/Minecraft-flask-app/static/favicon-32x32.png">
<link rel="icon" type="image/png" sizes="16x16" href="https://kakaomames.github.io/Minecraft-flask-app/static/favicon-16x16.png">
<link rel="manifest" href="https://kakaomames.github.io/Minecraft-flask-app/static/site.webmanifest">
    <link rel="stylesheet" href="https://kakaomames.github.io/Minecraft-flask-app/static/style.css">
</head>
<body>
    <header>
        <h1>マイクラプロジェクト</h1>
        <nav>
            <ul>
                <li><a href="/home">ホーム</a></li>
                <li><a href="/">ホーム(何も無い)</a></li>
                <li><a href="/login/google">Googleでログイン</a></li>
     
            </ul>
        </nav>
    </header>
    <main>
        <p>ここはホーム画面です。各メニューから移動してください。</p>
    </main>
    <footer>
        <p>&copy; 2025 pokemoguプロジェクト</p>
    </footer>
</body>
</html>
"""

@app.route('/', methods=['GET'])
def indexhhhhhhhh():
    return render_template_string(INDEX_HTML)

@app.route('/home', methods=['GET'])
def indexhhhhhhhd():
    return render_template_string(HOMEHTML)

# ----------------------------------------------------
# A. Google OAuth 認証関連
# ----------------------------------------------------
@app.route('/login/google', methods=['GET'])
def callback():
    """Google認証後のコールバック処理"""
    code = request.args.get('code')
    error = request.args.get('error')

    if error:
        # 認証エラーをフロントエンドにリダイレクト
        redirect_url = f"{FRONTEND_BASE_URI}/?login_status=error&message={error}"
        return redirect(redirect_url)

    if not code:
        return jsonify({"status": "error", "message": "認証コードが見つかりません"}), 400
    if not all([CLIENT_ID, CLIENT_SECRET, REDIRECT_URI]):
        return jsonify({"status": "error", "message": "サーバー設定エラー: 認証情報が不足しています"}), 500

    token_exchange_url = 'https://oauth2.googleapis.com/token'
    try:
        token_response = requests.post(
            token_exchange_url,
            data={
                'code': code,
                'client_id': CLIENT_ID,
                'client_secret': CLIENT_SECRET,
                'redirect_uri': REDIRECT_URI,
                'grant_type': 'authorization_code'
            }
        )
        token_data = token_response.json()
        
        if 'access_token' in token_data:
            # 成功: トークン情報をフロントエンドへ渡し、リダイレクト
            success_params = {
                'login_status': 'success',
                'access_token': token_data['access_token'],
                'expires_in': token_data['expires_in']
            }
            # リフレッシュトークンもあれば渡す（テスト用。本番ではサーバーで保存推奨）
            if 'refresh_token' in token_data:
                success_params['refresh_token'] = token_data['refresh_token']
            
            query_string = '&'.join(f'{k}={v}' for k, v in success_params.items())  
            redirect_url = f"{FRONTEND_BASE_URI}/?{query_string}"
            return redirect(redirect_url) 
        else:
            return jsonify({
                "status": "error",
                "message": "トークン交換に失敗しました",
                "details": token_data.get('error_description', '詳細不明のエラー')
            }), 400
    except Exception as e:
        return jsonify({"status": "error", "message": f"サーバー内部エラー: {str(e)}"}), 500


@app.route('/api/refresh_token', methods=['GET'])
def refresh_access_token():
    """
    保存されたリフレッシュトークンを使用して、新しいアクセストークンを取得する
    """    
    # REFRESH_TOKEN が定義されていない可能性があるのでチェック
    if not REFRESH_TOKEN:
        return jsonify({"status": "error", "message": "サーバー設定エラー: REFRESH_TOKEN(RT)が不足しています"}), 500
    if not all([CLIENT_ID, CLIENT_SECRET]):
        return jsonify({"status": "error", "message": "サーバー設定エラー: 認証情報が不足しています"}), 500
        
    token_refresh_url = 'https://oauth2.googleapis.com/token' 
    
    try:
        refresh_response = requests.post(
            token_refresh_url,
            data={
                'client_id': CLIENT_ID,
                'client_secret': CLIENT_SECRET,
                'refresh_token': REFRESH_TOKEN,
                'grant_type': 'refresh_token'
            }
        )
        refresh_response.raise_for_status()
        refresh_data = refresh_response.json()
        
        # 成功: 新しいアクセストークン情報をJSONで返却
        return jsonify({
            "status": "success",
            "message": "アクセストークンのリフレッシュに成功しました",
            "access_token": refresh_data['access_token'],
            "expires_in": refresh_data.get('expires_in')
        })
        
    except requests.exceptions.RequestException as e:
        error_details = refresh_response.json().get('error', '不明なエラー') if 'refresh_response' in locals() else str(e)
        status_code = refresh_response.status_code if 'refresh_response' in locals() else 500
        return jsonify({"status": "error", "message": "トークンリフレッシュエラー", "details": error_details}), status_code

# ----------------------------------------------------
# B. YouTube API 関連 (カスタムルーティング)
# ----------------------------------------------------

# ★★★ 既存の /api/youtube_channel は、汎用的な /api/youtube/channel/mine に置き換わります ★★★
@app.route('/api/youtube_channel', methods=['GET'])
@app.route('/api/youtube/channel/mine', methods=['GET']) # 旧エンドポイントの互換性維持と新ルール追加
def get_authenticated_user_channel_info():
    """
    ログインユーザー自身のYouTubeチャンネル情報を取得 (mine=trueを使用)
    """
    access_token = request.args.get('access_token')

    if not access_token:
        return jsonify({
            "status": "error", 
            "message": "access_tokenが提供されていません。ログインが必要です。"
        }), 401

    youtube_url = 'https://www.googleapis.com/youtube/v3/channels'
    params = {'part': 'snippet,contentDetails,statistics', 'mine': 'true'}
    headers = {'Authorization': f'Bearer {access_token}', 'Accept': 'application/json'}

    try:
        response = requests.get(youtube_url, params=params, headers=headers)
        response.raise_for_status() 
        channel_data = response.json()

        if channel_data.get('items'):
            return jsonify({"status": "success", "channel_info": channel_data['items'][0]})
        else:
            return jsonify({"status": "error", "message": "チャンネル情報が見つかりませんでした"}), 404

    except requests.exceptions.RequestException as e:
        error_message = response.json().get('error', {}).get('message', '詳細不明') if 'response' in locals() else str(e)
        status_code = response.status_code if 'response' in locals() else 500
        return jsonify({"status": "error", "message": "YouTube Channel APIエラー", "details": error_message}), status_code


@app.route('/api/youtube/channel/<identifier>', methods=['GET'])
def get_specific_channel_info(identifier):
    """
    チャンネルID (UC...) またはカスタムURL (@user) から情報を取得する
    """
    if not YOUTUBE_API_KEY:
        return jsonify({"status": "error", "message": "YOUTUBE_API_KEYが設定されていません"}), 500

    youtube_url = 'https://www.googleapis.com/youtube/v3/channels'
    params = {'part': 'snippet,contentDetails,statistics', 'key': YOUTUBE_API_KEY}

    if identifier.startswith('@'):
        # カスタムURL (@user) の場合
        params['forHandle'] = identifier.lstrip('@')
    else:
        # チャンネルID (UC...) の場合
        params['id'] = identifier
        
    try:
        response = requests.get(youtube_url, params=params)
        response.raise_for_status() 
        channel_data = response.json()
        
        if not channel_data.get('items'):
             return jsonify({"status": "error", "message": "チャンネルが見つかりません"}), 404

        return jsonify({"status": "success", "channel_info": channel_data['items'][0]})

    except requests.exceptions.RequestException as e:
        error_message = response.json().get('error', {}).get('message', '詳細不明') if 'response' in locals() else str(e)
        status_code = response.status_code if 'response' in locals() else 500
        return jsonify({"status": "error", "message": "YouTube Channel APIエラー", "details": error_message}), status_code


@app.route('/api/youtube/list/<playlist_id>', methods=['GET'])
def get_playlist_videos(playlist_id):
    """
    プレイリストID（UU...やPL...）から動画一覧を取得する
    - /api/youtube/list/UU...
    """
    if not YOUTUBE_API_KEY:
        return jsonify({"status": "error", "message": "YOUTUBE_API_KEYが設定されていません"}), 500

    youtube_url = 'https://www.googleapis.com/youtube/v3/playlistItems'
    
    params = {
        'part': 'snippet',
        'playlistId': playlist_id,
        'maxResults': 10, 
        'key': YOUTUBE_API_KEY
    }
    
    try:
        response = requests.get(youtube_url, params=params)
        response.raise_for_status()
        video_data = response.json()

        videos = []
        for item in video_data.get('items', []):
            snippet = item['snippet']
            videos.append({
                "videoId": snippet['resourceId']['videoId'],
                "title": snippet['title'],
                "publishedAt": snippet['publishedAt'],
                "thumbnailUrl": snippet['thumbnails']['medium']['url']
            })

        return jsonify({"status": "success", "message": "動画一覧の取得に成功しました", "videos": videos})

    except requests.exceptions.RequestException as e:
        error_message = response.json().get('error', {}).get('message', '詳細不明') if 'response' in locals() else str(e)
        status_code = response.status_code if 'response' in locals() else 500
        return jsonify({"status": "error", "message": "YouTube Playlist APIエラー", "details": error_message}), status_code


@app.route('/api/youtube/video/<video_id>', methods=['GET'])
def get_single_video_info(video_id):
    """
    動画ID（v=...）から動画の詳細情報を取得する
    - /api/youtube/video/VIDEO_ID
    """
    if not YOUTUBE_API_KEY:
        return jsonify({"status": "error", "message": "YOUTUBE_API_KEYが設定されていません"}), 500

    youtube_url = 'https://www.googleapis.com/youtube/v3/videos'
    
    params = {
        'part': 'snippet,contentDetails,statistics',
        'id': video_id, 
        'key': YOUTUBE_API_KEY
    }
    
    try:
        response = requests.get(youtube_url, params=params)
        response.raise_for_status()
        video_data = response.json()
        
        if not video_data.get('items'):
             return jsonify({"status": "error", "message": "動画が見つかりません"}), 404
             
        return jsonify({"status": "success", "video_info": video_data['items'][0]})

    except requests.exceptions.RequestException as e:
        error_message = response.json().get('error', {}).get('message', '詳細不明') if 'response' in locals() else str(e)
        status_code = response.status_code if 'response' in locals() else 500
        return jsonify({"status": "error", "message": "YouTube Video APIエラー", "details": error_message}), status_code


# 開発環境でローカル実行するための設定
if __name__ == '__main__':
    # ローカル実行時には、環境変数設定はここに書くか、.envファイルを使ってください。
    app.run(debug=True, port=5000)
