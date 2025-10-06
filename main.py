from flask import Flask, request, render_template_string, send_file,redirect, url_for, jsonify, Response # 正しい順序に並べ替えてもOK
import subprocess
import os
import io
from urllib.parse import urljoin, urlparse
import subprocess
import base64
import json
from bs4 import BeautifulSoup
from typing import Tuple, Dict, Any, Union

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












# --- HTMLフォームの文字列定義 (トリプルクォート/ヒアドキュメント) ---
def get_link_form_html() -> str:
    """
    /link エンドポイント用のHTMLフォーム文字列を返す
    """
    return """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>URL探索フォームと結果表示</title>
    <style>
        body { font-family: sans-serif; }
        .log-container { background-color: #f4f4f4; border: 1px solid #ddd; padding: 15px; margin-top: 20px; white-space: pre-wrap; font-family: monospace; font-size: 14px; }
        .json-output { background-color: #e6e6ff; border: 1px solid #aaa; padding: 15px; margin-top: 20px; white-space: pre-wrap; font-family: monospace; font-size: 14px; }
        .content-preview { 
            border: 2px solid #333; 
            margin-top: 20px; 
            height: 300px; 
            overflow: auto; 
            padding: 10px; 
            background-color: white; 
        }
    </style>
</head>
<body>
    <h1>URL探索✨</h1>
    
    <form id="linkForm">
        <input type="text" name="url" id="urlInput" placeholder="URLを入力してください (例: https://example.com)" size="50" required>
        <button type="submit">探索🚀</button>
    </form>

    <div id="loading" style="display:none; color: blue; margin-top: 10px;">処理中... しばらくお待ちください。⏳</div>

    <div id="results" style="margin-top: 30px; display:none;">
        <h2>📝 JSON レスポンス</h2>
        <pre class="json-output" id="jsonOutput"></pre>
        
        <h2>🌐 ネットワークログ (NL / logs)</h2>
        <pre class="log-container" id="networkLog"></pre>

        <h2>📄 コンテンツ (Base64からデコードし表示)</h2>
        <p id="htmlStatus"></p>
        <div class="content-preview" id="contentPreview"></div>
    </div>

    <script>
        document.getElementById('linkForm').addEventListener('submit', async function(e) {
            e.preventDefault(); // デフォルトのフォーム送信をキャンセル

            const url = document.getElementById('urlInput').value;
            const loading = document.getElementById('loading');
            const resultsDiv = document.getElementById('results');
            const jsonOutput = document.getElementById('jsonOutput');
            const networkLog = document.getElementById('networkLog');
            const contentPreview = document.getElementById('contentPreview');
            const htmlStatus = document.getElementById('htmlStatus');

            loading.style.display = 'block';
            resultsDiv.style.display = 'none';

            try {
                // /curl エンドポイントにリクエスト
                const response = await fetch(`/curl?url=${encodeURIComponent(url)}`);
                const json = await response.json();

                // JSON全体を表示
                jsonOutput.textContent = JSON.stringify(json, null, 2);
                
                const data = json.data;

                // ネットワークログを表示
                networkLog.textContent = data.NL || data.logs || 'ログなし';

                // Base64コンテンツをデコード
                // Base64はASCII文字のみなので、デコードは安全に行えます
                const decodedContent = atob(data.code);
                
                // HTMLリライト情報
                const isRewritten = json.data.is_html_rewritten;
                htmlStatus.innerHTML = isRewritten 
                    ? '💡 **HTMLコンテンツ**が検出され、**相対パス**が**絶対URL**に変換されました。'
                    : '（HTMLコンテンツではない、またはリライトされませんでした。）';
                
                // コンテンツをエスケープして表示 (preタグでソースコード表示のように扱う)
                contentPreview.textContent = decodedContent;
                
                // 結果を表示
                resultsDiv.style.display = 'block';

            } catch (error) {
                // ネットワーク接続などのエラーの場合
                jsonOutput.textContent = `リクエストエラー: ${error.message}`;
                networkLog.textContent = `リクエストエラーが発生しました。`;
                resultsDiv.style.display = 'block';
            } finally {
                loading.style.display = 'none';
            }
        });
    </script>
</body>
</html>
"""

# --- 外部コマンド実行とログ取得 (バイナリ対応) ---
def run_curl(url: str) -> Dict[str, Union[bytes, str]]:
    """
    curl -v -L URL を実行し、コンテンツ(bytes)とログ(str)を返す
    """
    try:
        # text=False で stdout/stderr をバイト列(バイナリ)として受け取る
        result = subprocess.run(
            ['curl', '-v', '-L', url],
            capture_output=True,
            timeout=30 # タイムアウト設定
        )
        
        # ログ (-v の出力) は stderr に含まれるので、UTF-8でデコード
        logs = result.stderr.decode('utf-8', errors='ignore')
        
        return {
            'content': result.stdout,
            'log': logs,
            'status': 'success'
        }
    except subprocess.TimeoutExpired:
        return {'content': b'', 'log': 'Error: Curl command timed out.', 'status': 'timeout'}
    except Exception as e:
        return {'content': b'', 'log': f'Error: {str(e)}', 'status': 'error'}

# --- HTMLパス変換 (案1ロジック採用) ---
def rewrite_html_paths(html_content_bytes: bytes, base_url: str) -> Tuple[bytes, bool]:
    """
    BeautifulSoupでHTMLを解析し、相対パスを絶対パスに変換する
    """
    # 1. バイト列を文字列にデコード
    try:
        html_content_str = html_content_bytes.decode('utf-8')
    except UnicodeDecodeError:
        # デコードできない場合はHTMLではないと判断
        return html_content_bytes, False

    # 2. Beautiful Soupで解析と<html>タグの存在チェック
    try:
        soup = BeautifulSoup(html_content_str, 'html.parser')
        
        # <html>タグが見つからなければ、HTMLコンテンツではないと判断 (案1ロジック)
        if not soup.html:
            return html_content_bytes, False

        # 3. HTMLタグと属性の書き換え処理
        tags_and_attrs = {
            'a': 'href', 'link': 'href', 'script': 'src', 
            'img': 'src', 'source': 'src', 'video': 'poster',
        }

        for tag, attr in tags_and_attrs.items():
            for element in soup.find_all(tag):
                if element.has_attr(attr):
                    url = element[attr]
                    # 絶対URL以外を対象とする
                    if not urlparse(url).scheme: 
                        absolute_url = urljoin(base_url, url)
                        element[attr] = absolute_url
        
        # 4. 書き換えたHTMLをバイト列に戻す
        rewritten_html_bytes = str(soup).encode('utf-8')
        return rewritten_html_bytes, True

    except Exception as e:
        print(f"HTML parsing/rewriting error: {e}")
        # エラーが発生した場合は、元のバイト列を返す
        return html_content_bytes, False

# --- エンドポイント1: URL入力フォーム ---
@app.route('/link', methods=['GET', 'POST'])
def link_form() -> Response:
    """
    URL入力フォームの表示と、POSTリクエストを/curlへリダイレクトする処理
    """
    if request.method == 'POST':
        url = request.form.get('url')
        if url:
            # POSTを受け取り、GETで処理する /curl へリダイレクト
            return redirect(url_for('curl_request', url=url))
        
    # GETリクエスト、またはPOSTでURLがない場合は、直接HTML文字列を返す
    return Response(get_link_form_html(), mimetype='text/html')

# --- エンドポイント2: curl実行と結果表示 (JSONレスポンス) ---
@app.route('/curl', methods=['GET', 'POST'])
def curl_request() -> Tuple[Response, int]:
    """
    curl -v -L を実行し、結果をJSON形式で返す
    """
    url = request.args.get('url') # GETパラメータからURLを取得
    
    if not url:
        return jsonify({
            'data': {
                'url': '',
                'code': '',
                'logs': 'Error: URL parameter is missing.',
                'NL': 'Error: URL parameter is missing.',
            }
        }), 400

    # 1. curlコマンドを実行
    result = run_curl(url)
    
    # 2. コンテンツがHTMLであればパスを変換 (Base64エンコード前にリライト)
    content_binary = result['content']
    
    # HTML判定とパスリライトの実行
    content_binary, is_html = rewrite_html_paths(content_binary, url)
    
    # 3. バイナリコンテンツをBase64にエンコード
    # Base64はバックスラッシュをそのまま使用するため、JSONの要件にも合致します
    content_base64 = base64.b64encode(content_binary).decode('utf-8')
    
    # 4. JSONレスポンスの構築
    response_data = {
        'url': url,
        # code: curlの結果のバイナリ(Base64エンコード)
        'code': content_base64, 
        # logs: curlコマンドの -v で出たやつ
        'logs': result['log'],
        # NL: Network Logの略。logsと同じ内容を格納
        'NL': result['log'],
        # (追加) HTMLをリライトしたかどうかの情報
        'is_html_rewritten': is_html 
    }

    # 成功ステータスでJSONを返す
    return jsonify({'data': response_data}), 200






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
