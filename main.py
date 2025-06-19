import tkinter as tk
import subprocess
from tkinter import scrolledtext
from tkinter import messagebox

def execute_command():
    command = command_input.get("1.0", tk.END).strip()
    if not command:
        messagebox.showwarning("警告", "コマンドを入力してください。")
        return

    try:
        # コマンドを実行し、標準出力と標準エラー出力を取得
        # text=True は Python 3.7以降で推奨される
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
        output_text.delete("1.0", tk.END)
        output_text.insert(tk.END, "--- コマンド実行結果 ---\n")
        output_text.insert(tk.END, result.stdout)
        if result.stderr:
            output_text.insert(tk.END, "\n--- エラー出力 ---\n")
            output_text.insert(tk.END, result.stderr)
        output_text.insert(tk.END, "\n--- 実行完了 ---")

    except subprocess.CalledProcessError as e:
        output_text.delete("1.0", tk.END)
        output_text.insert(tk.END, f"--- エラー発生 (終了コード: {e.returncode}) ---\n")
        output_text.insert(tk.END, f"コマンド: {e.cmd}\n")
        output_text.insert(tk.END, f"標準出力:\n{e.stdout}\n")
        output_text.insert(tk.END, f"標準エラー出力:\n{e.stderr}\n")
        output_text.insert(tk.END, "\n--- 実行失敗 ---")
    except Exception as e:
        output_text.delete("1.0", tk.END)
        output_text.insert(tk.END, f"--- 予期せぬエラー ---\n")
        output_text.insert(tk.END, str(e))
        output_text.insert(tk.END, "\n--- 実行失敗 ---")

# GUIの設定
root = tk.Tk()
root.title("コマンド実行ツール")

# コマンド入力用テキストボックス
command_label = tk.Label(root, text="実行したいコマンドを入力してください:")
command_label.pack(pady=5)
command_input = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=80, height=10, font=("Meiryo", 10))
command_input.pack(pady=5)

# 実行ボタン
execute_button = tk.Button(root, text="コマンドを実行", command=execute_command)
execute_button.pack(pady=10)

# 結果表示用テキストボックス
output_label = tk.Label(root, text="コマンド実行結果:")
output_label.pack(pady=5)
output_text = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=80, height=15, font=("Meiryo", 10), state=tk.NORMAL) # 初期は編集可能に
output_text.pack(pady=5)

root.mainloop()
