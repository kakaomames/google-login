from flask import Flask, render_template_string, request
import subprocess
import os

app = Flask(__name__)

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


@app.route('/', methods=['GET', 'POST'])

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
