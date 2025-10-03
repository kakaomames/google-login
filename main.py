from flask import Flask, render_template_string, request
import subprocess
import os

app = Flask(__name__)
# --- CSS定義 ---
CUSTOM_CSS = """
    <style>
        body { font-family: 'Meiryo', sans-serif; margin: 20px; background-color: #f4f4f4; color: #333; }
        .container { max-width: 800px; margin: auto; background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        h1 { color: #0056b3; text-align: center; }
        input[type="text"], select { width: 98%; padding: 10px; margin-bottom: 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 1rem; box-sizing: border-box; }
        button { background-color: #007bff; color: white; padding: 10px 15px; border: none; border-radius: 4px; cursor: pointer; font-size: 1rem; }
        button:hover { background-color: #0056b3; }
        pre { background-color: #e2e2e2; padding: 15px; border-radius: 4px; overflow-x: auto; white-space: pre-wrap; word-break: break-all; }
        .warning { color: red; font-weight: bold; text-align: center; margin-bottom: 15px; }
    </style>
"""

# --- テンプレート (1): URL入力フォーム ---
HTML_FORM_TEMPLATE = lambda warning="": f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>オンラインダウンローダー</title>
    {CUSTOM_CSS}
</head>
<body>
    <div class="container">
        <h1>🔗 オンラインダウンローダー</h1>
        {f'<p class="warning">{warning}</p>' if warning else ''}
        <p>ダウンロードしたいファイルのURLを入力してください。</p>
        <form method="POST" action="/select_name">
            <input type="text" name="url" placeholder="例: https://kakaomames.gothub.io/a/index.html" required>
            <br>
            <button type="submit">ファイル名選択へ進む</button>
        </form>
    </div>
</body>
</html>
"""

# --- テンプレート (2): ファイル名選択フォーム ---
# name1: 'index.html' の形式, name2: '/a/index.html' の形式, original_url: 元のURL
HTML_SELECT_TEMPLATE = lambda name1, name2, original_url: f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ファイル名を選択</title>
    {CUSTOM_CSS}
</head>
<body>
    <div class="container">
        <h1>ファイル名の選択</h1>
        <p>ダウンロードするファイル名を以下の2つの候補から選択してください。</p>
        <form method="POST" action="/download">
            <input type="hidden" name="original_url" value="{original_url}">
            
            <label for="filename_select">ダウンロード名:</label>
            <select id="filename_select" name="filename" required>
                <option value="{name1}">{name1} (ファイル名のみ)</option>
                <option value="{name2}">{name2} (パスを含む)</option>
            </select>
            <br><br>
            <button type="submit">📥 ダウンロード開始</button>
        </form>
        <hr>
        <p>元のURL: <pre>{original_url}</pre></p>
        <p><a href="/">最初に戻る</a></p>
    </div>
</body>
</html>

"""

# --- URLからファイル名候補を抽出するヘルパー関数 ---
def get_filename_options(url):
    """
    例: https://kakaomames.gothub.io/a/index.html -> ('index.html', 'a/index.html')
    """
    try:
        parsed_url = urlparse(url)
        path = parsed_url.path.split(';')[0].split('?')[0] # クエリやパラメータを除去
        
        # 2. パス全体からファイル名候補を取得
        path_parts = path.split('/')
        
        # name1: 最後の要素 (index.html)
        name1 = path_parts[-1] if path_parts[-1] else "downloaded_file"
        
        # name2: 最後の2,3要素 (a/index.html)
        # 最後の要素が空の場合はその一つ前までを含める
        if not path_parts[-1] and len(path_parts) > 1:
            name2_parts = path_parts[-3:-1] if len(path_parts) >= 3 else path_parts[-2:-1]
        else:
            name2_parts = path_parts[-2:] if len(path_parts) >= 2 else path_parts[-1:]
            
        name2 = '/'.join(name2_parts).strip('/')
        if not name2:
            name2 = name1
            
        # 安全のため、/ を - に置換するなど、より厳密な処理が必要ですが、ここではユーザーの要望を優先します。
        
        # name1: index.html (basename)
        # name2: a/index.html (dirname + basename)
        return name1, name2
        
    except Exception:
        return "downloaded_file.bin", "downloaded_file_full.bin"


# --- ルート定義 ---

@app.route('/', methods=['GET'])
def index():
    """最初のURL入力フォームを表示"""
    return render_template_string(HTML_FORM_TEMPLATE())

@app.route('/select_name', methods=['POST'])
def select_name():
    """URLを受け取り、ファイル名選択フォームを表示"""
    url = request.form.get('url')
    
    if not url:
        return render_template_string(HTML_FORM_TEMPLATE("URLを入力してください。")), 400
        
    # URLからファイル名候補を抽出
    name1, name2 = get_filename_options(url)
    
    # ファイル名選択フォームをレンダリング
    return render_template_string(HTML_SELECT_TEMPLATE(name1, name2, url))

@app.route('/download', methods=['POST'])
def download():
    """選択されたファイル名とURLでダウンロード処理を実行"""
    target_url = request.form.get('original_url')
    download_name = request.form.get('filename')

    if not target_url or not download_name:
        return render_template_string(HTML_FORM_TEMPLATE("URLまたはファイル名が不正です。")), 400

    # 2. curlコマンドを構築し実行
    # -sL: サイレントモードでリダイレクトを追跡
    # ユーザーの要望通り、curl -L を使用してファイル内容を取得します。
    try:
        result = subprocess.run(
            ['curl', '-s', '-L', target_url],
            capture_output=True,
            check=True,
            timeout=60 # タイムアウトを少し長めに設定
        )

        file_data = io.BytesIO(result.stdout)
        
        # ファイルとしてクライアントに送信
        # download_nameとしてユーザーが選択したファイル名を設定
        return send_file(
            file_data,
            mimetype='application/octet-stream', # 一般的なバイナリファイル
            as_attachment=True,
            download_name=download_name.replace('/', '_') # ファイル名に / が含まれると問題があるので _ に置換
        )

    except subprocess.CalledProcessError as e:
        error_output = e.stderr.decode('utf-8', errors='ignore')
        error_message = f"ダウンロード中にエラーが発生しました。Exit Code: {e.returncode} / Error Output: {error_output}"
        return render_template_string(f'<div class="container"><h1 class="warning">ダウンロードエラー</h1><pre>{error_message}</pre><p><a href="/">戻る</a></p></div>'), 500

    except Exception as e:
        return render_template_string(f'<div class="container"><h1 class="warning">予期せぬエラー</h1><pre>{str(e)}</pre><p><a href="/">戻る</a></p></div>'), 500

# HTMLテンプレートをPythonコード内に直接記述
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Webコマンド実行ツール (Flask)</title>
    <style>
        body { font-family: 'Meiryo', sans-serif; margin: 20px; background-color: #f4f4f4; color: #333; }
        .container { max-width: 800px; margin: auto; background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        h1 { color: #0056b3; text-align: center; }
        textarea { width: 98%; padding: 10px; margin-bottom: 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 1rem; box-sizing: border-box; }
        button { background-color: #007bff; color: white; padding: 10px 15px; border: none; border-radius: 4px; cursor: pointer; font-size: 1rem; }
        button:hover { background-color: #0056b3; }
        pre { background-color: #e2e2e2; padding: 15px; border-radius: 4px; overflow-x: auto; white-space: pre-wrap; word-break: break-all; }
        .warning { color: red; font-weight: bold; text-align: center; margin-bottom: 15px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Webコマンド実行ツール (Flask)</h1>
        <p class="warning">警告: このツールは非常に危険です。自己責任で、信頼できる環境でのみ使用してください。</p>

        <form method="POST">
            <label for="command">実行したいコマンドを入力してください:</label><br>
            <textarea id="command" name="command" rows="10" placeholder="例: ls -l (Linux/macOS), dir (Windows)"></textarea><br>
            <button type="submit">コマンドを実行</button>
        </form>

        {% if output %}
            <hr>
            <h2>コマンド実行結果:</h2>
            <pre>{{ output }}</pre>
        {% endif %}
    </div>
</body>
</html>
"""


def run():
    long = request.args.get("lang")
    if not long:
        return "<h1>404 Not Found</h1>", 200

    
@app.route('/')
def indexs():
    # 定義したHTML文字列をそのまま返す
    # Flaskはこれをレスポンスボディとしてブラウザに送ります
    return HTML_TEMPLATE


@app.route("/run")
def run_command():
    cmd = request.args.get("cmd")
    if not cmd:
        return "Error: No command provided.", 400

    print(f"[実行] {cmd}")
    try:
        output = subprocess.getoutput(cmd)
        return f"<pre>{output}</pre>"
    except Exception as e:
        return f"<pre>実行エラー: {str(e)}</pre>", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
    
@app.route('/favicon.ico')
def favicon():
    return send_from_directory('static', 'favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.route('/cmd', methods=['GET', 'POST'])
def index():
    output = ""
    if request.method == 'POST':
        command = request.form['command'].strip()
        if not command:
            output = "警告: コマンドを入力してください。"
        else:
            try:
                # subprocess.run を使用してコマンドを実行
                # shell=True はセキュリティリスクが高いため注意
                # text=True は Python 3.7以降で推奨
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    check=True,
                    encoding='utf-8' # 日本語の文字化け対策
                )
                output = f"--- コマンド実行結果 ---\n{result.stdout}"
                if result.stderr:
                    output += f"\n--- エラー出力 ---\n{result.stderr}"
                output += "\n--- 実行完了 ---"

            except subprocess.CalledProcessError as e:
                output = (
                    f"--- エラー発生 (終了コード: {e.returncode}) ---\n"
                    f"コマンド: {e.cmd}\n"
                    f"標準出力:\n{e.stdout}\n"
                    f"標準エラー出力:\n{e.stderr}\n"
                    f"--- 実行失敗 ---"
                )
            except Exception as e:
                output = f"--- 予期せぬエラー ---\n{str(e)}\n--- 実行失敗 ---"
    
    return render_template_string(HTML_TEMPLATE, output=output)

if __name__ == '__main__':
    # デバッグモードは開発用です。本番環境では絶対に有効にしないでください。
    app.run(debug=True, host='0.0.0.0', port=5000)
