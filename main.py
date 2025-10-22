# api/callback.py
import os
import json
import requests
from flask import Flask, redirect, request, jsonify, render_template_string

# Flaskアプリのインスタンスを作成
app = Flask(__name__)

# --- 1. 環境変数から機密情報を読み込む ---
# Vercelの環境変数で 'SESSION_KEY' を設定する必要があります
app.secret_key = os.environ.get('SESSION_KEY', 'VERY_INSECURE_DEFAULT_KEY_CHANGE_ME') 
# ★★★ 修正箇所: リダイレクト先のフロントエンドURIを設定 ★★★
# Vercelの環境変数に、フロントエンドのベースURIを設定することを推奨します
FRONTEND_BASE_URI = os.environ.get('FRONTEND_URI', 'https://kakaomames.github.io')

# Vercelに設定する環境変数名に合わせて修正
CLIENT_ID = os.environ.get('G_CI')
CLIENT_SECRET = os.environ.get('G_CS')
REDIRECT_URI = os.environ.get('G_REDIRECT_URI') # VercelのコールバックURL



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
    """最初のURL入力フォームを表示"""
    return render_template_string(INDEX_HTML)


@app.route('/home', methods=['GET'])
def indexhhhhhhhd():
    """最初のURL入力フォームを表示"""
    return render_template_string(HOMEHTML)



@app.route('/login/google', methods=['GET'])
def callback():
    """
    Googleから認証コードを受け取り、アクセストークンと交換するエンドポイント
    """
    auth_code = request.args.get('code')
    error = request.args.get('error')

    # 認証エラーのチェック
    if error:
        return jsonify({"status": "error", "message": f"認証エラーが発生しました: {error}"}), 400

    if not auth_code:
        return jsonify({"status": "error", "message": "認証コードが見つかりません"}), 400
    
    # 必須環境変数のチェック（設定漏れ防止）
    if not all([CLIENT_ID, CLIENT_SECRET, REDIRECT_URI]):
        return jsonify({"status": "error", "message": "サーバー設定エラー: 環境変数が不足しています"}), 500


    # 2. 認証コードを使ってアクセストークンをGoogleと交換（サーバー間通信）
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
            # 成功: トークン情報をJSONで返却
            # ★注意★ 本番運用では、このトークンをDBなどに安全に保存し、
            #         ユーザーをフロントエンドにリダイレクトする処理が必要です。
            return jsonify({
                "status": "success",
                "message": "アクセストークンの取得に成功しました",
                "token_info": token_data
            })
        else:
            # Googleからのエラー応答
            return jsonify({
                "status": "error",
                "message": "トークン交換に失敗しました",
                "details": token_data.get('error_description', '詳細不明のエラー')
            }), 400

    except Exception as e:
        return jsonify({"status": "error", "message": f"サーバー内部エラー: {str(e)}"}), 500

# Vercel Functionとして動作させるためのエントリポイント
# def handler(event, context):
#     """Vercelがサーバーレス関数を実行するためのエントリポイント"""
#.    return app.wsgi_app(event, context)



。

@app.route('/api/refresh_token', methods=['GET'])
def refresh_access_token():
    """
    保存されたリフレッシュトークンを使用して、新しいアクセストークンを取得する
    """
    
    # 必須環境変数のチェック
    if not all([CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN]):
        return jsonify({"status": "error", "message": "サーバー設定エラー: 認証情報が不足しています"}), 500

    # 2. Googleのトークンエンドポイントにリクエストを送信
    token_refresh_url = 'https://oauth2.googleapis.com/token'
    
    try:
        refresh_response = requests.post(
            token_refresh_url,
            data={
                'client_id': CLIENT_ID,
                'client_secret': CLIENT_SECRET,
                'refresh_token': REFRESH_TOKEN,
                'grant_type': 'refresh_token' # ★トークンリフレッシュに必要な値
            }
        )
        refresh_data = refresh_response.json()


        

        if 'access_token' in refresh_data:
            # 成功: 新しいアクセストークン情報を返却
            new_access_token = refresh_data['access_token']
            
            # ★重要★
            # 実際には、この新しい access_token を、フロントエンドまたは
            # データを要求する関数に安全に渡す必要があります。


            if 'access_token' in token_data:
            new_access_token = token_data['access_token']
            
            # --- ここが重要: フロントエンドにリダイレクトする ---
            
            # 1. 成功メッセージをクエリパラメータに格納
            success_params = {
                'login_status': 'success',
                # 2. アクセストークンを渡す (一時的/テスト用)
                #    ※ 本番ではセキュリティのため、トークンをセッションID経由で渡すべきですが、
                #    今回はシンプル化のためクエリパラメータで渡します。
                'access_token': new_access_token,
            }
            
            # 3. クエリパラメータを構築
            query_string = '&'.join(f'{k}={v}' for k, v in success_params.items())
            
            # 4. フロントエンドのダッシュボードなどにリダイレクト
            # 例: https://kakaomames.github.io/?login_status=success&access_token=...
            redirect_url = f"{FRONTEND_BASE_URI}/?{query_string}"
            
            # Flaskのredirect関数でリダイレクト
            return redirect(redirect_url) 
            
            # 修正前: return jsonify({"status": "success", ...}) # これを削除
        
        else:
            # トークンリフレッシュの失敗（例：リフレッシュトークンが無効）
            return jsonify({
                "status": "error",
                "message": "アクセストークンのリフレッシュに失敗しました",
                "details": refresh_data.get('error_description', '詳細不明のエラー')
            }), 400

    except Exception as e:
        return jsonify({"status": "error", "message": f"サーバー内部エラー: {str(e)}"}), 500






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

