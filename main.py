# api/callback.py
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
# ★★★ 修正箇所 1: Google認証コードの受け取りとリダイレクト ★★★
# ----------------------------------------------------
@app.route('/login/google', methods=['GET'])
def callback():
    auth_code = request.args.get('code')
    error = request.args.get('error')

    if error:
        return jsonify({"status": "error", "message": f"認証エラーが発生しました: {error}"}), 400

    if not auth_code:
        # 認証開始のためのリダイレクト処理（もしユーザーが直接アクセスした場合）
        # ※ 今回のフロントエンドはJSでリダイレクトしているので不要かもしれませんが、念のため。
        return jsonify({"status": "error", "message": "認証コードが見つかりません"}), 400
    if not all([CLIENT_ID, CLIENT_SECRET, REDIRECT_URI]):
        return jsonify({"status": "error", "message": "サーバー設定エラー: 環境変数が不足しています"}), 500

    token_exchange_url = 'https://oauth2.googleapis.com/token'
    try:
        token_response = requests.post(
            token_exchange_url,
            data={
                'code': auth_code,
                'client_id': CLIENT_ID,
                'client_secret': CLIENT_SECRET,
                'redirect_uri': REDIRECT_URI,
                'grant_type': 'authorization_code'
            }
        )
        token_data = token_response.json()
        if 'access_token' in token_data:
            # 成功: トークン情報をフロントエンドへ渡し、リダイレクト
            new_access_token = token_data['access_token']
            
            success_params = {
                'login_status': 'success',
                'access_token': new_access_token,
            }
            # リフレッシュトークンもあれば渡す（テスト用）
            if 'refresh_token' in token_data:
                success_params['refresh_token'] = token_data['refresh_token']
            query_string = '&'.join(f'{k}={v}' for k, v in success_params.items())  
            redirect_url = f"{FRONTEND_BASE_URI}/?{query_string}"
            # リダイレクトを強制するレスポンス
            response = Response(status=302)
            response.headers['Location'] = redirect_url
            return response # ★★★ これでリダイレクト！ ★★★        
        else:
            return jsonify({
                "status": "error",
                "message": "トークン交換に失敗しました",
                "details": token_data.get('error_description', '詳細不明のエラー')
            }), 400
    except Exception as e:
        return jsonify({"status": "error", "message": f"サーバー内部エラー: {str(e)}"}), 500


# ----------------------------------------------------
# ★★★ 修正箇所 2: トークンリフレッシュ関数のバグ修正 ★★★
# ----------------------------------------------------
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
        refresh_data = refresh_response.json()
        if 'access_token' in refresh_data:
            # 成功: 新しいアクセストークン情報をJSONで返却
            return jsonify({
                "status": "success",
                "message": "アクセストークンのリフレッシュに成功しました",
                "new_access_token": refresh_data['access_token'],
                "expires_in": refresh_data.get('expires_in')
            })
        else:
            # リフレッシュ失敗
            return jsonify({
                "status": "error",
                "message": "アクセストークンのリフレッシュに失敗しました",
                "details": refresh_data.get('error_description', '詳細不明のエラー')
            }), 400
    except Exception as e:
        return jsonify({"status": "error", "message": f"サーバー内部エラー: {str(e)}"}), 500
# ... (中略: /api/youtube_channel のエンドポイントはそのまま) ...
# ----------------------------------------------------
# ★★★ /api/youtube_channel エンドポイントはそのまま ★★★
# ----------------------------------------------------
# ... (略) ...


# 開発環境でローカル実行するための設定if __name__ == '__main__':    app.run(debug=True, port=5000)






@app.route('/api/youtube_channel', methods=['GET'])
def get_user_channel_info():
    """
    ユーザーのアクセストークンを使用して、YouTubeチャンネル情報を取得するエンドポイント
    """
    # フロントエンドからクエリパラメータとして渡されたアクセストークンを取得
    access_token = request.args.get('access_token')

    if not access_token:
        return jsonify({
            "status": "error", 
            "message": "access_tokenが提供されていません。ログインが必要です。"
        }), 401

    # 2. YouTube Data API v3 のエンドポイント
    youtube_url = 'https://www.googleapis.com/youtube/v3/channels'
    
    # 3. リクエストパラメータとヘッダーを設定
    params = {
        'part': 'snippet,contentDetails,statistics', # 取得したい情報（チャンネル名、統計情報など）
        'mine': 'true'                               # ログインユーザー自身のチャンネル情報を要求
    }
    
    headers = {
        'Authorization': f'Bearer {access_token}', # ★アクセストークンをヘッダーに設定
        'Accept': 'application/json'
    }

    try:
        # 4. YouTube APIへのリクエストを送信
        response = requests.get(youtube_url, params=params, headers=headers)
        response.raise_for_status() # HTTPエラーが発生した場合に例外を発生させる

        channel_data = response.json()

        if channel_data.get('items'):
            # 成功: 取得したチャンネルデータを返却
            return jsonify({
                "status": "success",
                "message": "チャンネル情報の取得に成功しました",
                "channel_info": channel_data['items'][0]
            })
        else:
            # チャンネル情報が見つからない場合（APIの応答が空の場合など）
             return jsonify({
                "status": "error",
                "message": "チャンネル情報が見つかりませんでした (チャンネルを作成していない可能性があります)"
            }), 404


    except requests.exceptions.RequestException as e:
        # HTTPエラー（401 Unauthorizedなど）を捕捉
        if response.status_code == 401:
            error_message = "トークンの期限切れまたは無効です。トークンをリフレッシュしてください。"
        else:
            error_message = f"YouTube APIエラー: {e}"
            
        return jsonify({
            "status": "error",
            "message": error_message,
            "details": response.text
        }), response.status_code if 'response' in locals() else 500

# Vercel Functionとして動作させるための設定は vercel.json に依存します
# 開発環境でローカル実行するための設定
if __name__ == '__main__':
    # ローカル開発用に環境変数を設定してテスト
    # os.environ['G_CI'] = '...'
    # os.environ['G_CS'] = '...'
    # os.environ['G_REDIRECT_URI'] = 'http://localhost:5000/api/callback'
    # os.environ['SESSION_KEY'] = 'a_super_secret_key_for_dev'
    app.run(debug=True, port=5000)

