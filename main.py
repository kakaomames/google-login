# api/callback.py
import os
import json
import requests
from flask import Flask, redirect, request, jsonify

# Flaskアプリのインスタンスを作成
app = Flask(__name__)

# --- 1. 環境変数から機密情報を読み込む ---
# Vercelの環境変数で 'SESSION_KEY' を設定する必要があります
app.secret_key = os.environ.get('SESSION_KEY', 'VERY_INSECURE_DEFAULT_KEY_CHANGE_ME') 

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
def handler(event, context):
    """Vercelがサーバーレス関数を実行するためのエントリポイント"""
    return app.wsgi_app(event, context)

# 開発環境でローカル実行するための設定
if __name__ == '__main__':
    # ローカル開発用に環境変数を設定してテスト
    # os.environ['G_CI'] = '...'
    # os.environ['G_CS'] = '...'
    # os.environ['G_REDIRECT_URI'] = 'http://localhost:5000/api/callback'
    # os.environ['SESSION_KEY'] = 'a_super_secret_key_for_dev'
    app.run(debug=True, port=5000)

