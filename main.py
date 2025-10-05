from flask import Flask, request, render_template_string, send_file # 正しい順序に並べ替えてもOK
import subprocess
import os
import io
from urllib.parse import urlparse

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


# --- URLからファイル名候補を抽出するヘルパー関数 (改良版) ---
def get_filename_options(url):
    """
    例: https://watchdocumentaries.com/wp-content/uploads/games/drift-boss/game.js 
    -> ('game.js', 'drift-boss/game.js') を抽出
    """
    DEFAULT_NAME_BASE = "downloaded_content"
    
    try:
        # URLを解析し、クエリやフラグメントを除去
        parsed_url = urlparse(url)
        path = parsed_url.path.split(';')[0].split('?')[0].strip('/')

        if not path:
            return f"{DEFAULT_NAME_BASE}.bin", f"root_{DEFAULT_NAME_BASE}.bin"
        
        # 1. name1: 最後の要素 (ファイル名のみ)
        # os.path.basenameを使うと安全にファイル名を取得できます
        name1 = os.path.basename(path)
        if not name1: # 例: /path/to/ (スラッシュで終わる場合)
            name1 = f"{DEFAULT_NAME_BASE}.html" # フォルダ名から推測する手もありますが、ここではデフォルト名を返す
        
        # 2. name2: パスの最後の2セグメント
        path_parts = path.split('/')
        # 最後の要素が空（スラッシュ終わり）なら、最後の2つではなく、その前の2つを取得
        if not path_parts[-1] and len(path_parts) > 1:
            name2_parts = path_parts[-3:-1]
        else:
            name2_parts = path_parts[-2:]

        name2 = '/'.join(name2_parts).strip('/')
        if not name2 or name2 == name1: # name1と同じか、うまく取得できなかった場合
            # 最後の3つを取得してみる (e.g. games/drift-boss/game.js)
            name2_parts = path_parts[-3:]
            name2 = '/'.join(name2_parts).strip('/')
            if not name2:
                 name2 = f"full_{name1}" # 最終手段
        
        # / が含まれていると send_file で問題になるため、/ を _ に置き換えて表示 (ダウンロード時にはまた / が入っていると困るので、download関数で処理します)
        display_name2 = name2.replace('/', '_')
        
        # 表示のため、name2もファイル名として妥当な形に調整
        if name1 == name2:
             name2 = f"path_{name1}"

        return name1, name2
        
    except Exception:
        # 何か問題が発生した場合のデフォルト値
        return f"{DEFAULT_NAME_BASE}.bin", f"{DEFAULT_NAME_BASE}_full.bin"


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

    
@app.route('/favicon.ico')
def favicon():
    return send_from_directory('static', 'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/favicon.png')
def favicons():
    return send_from_directory('static', 'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/favicon.svg')
def faviconing():
    return send_from_directory('static', 'favicon.ico', mimetype='image/vnd.microsoft.icon')



"""
色見にくくね?
"""

@app.route('/cmd', methods=['GET', 'POST'])
def indexs():
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
