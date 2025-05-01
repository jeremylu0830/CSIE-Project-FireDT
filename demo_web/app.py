# test: data_path = os.path.join(BASE_DIR, '20250311_140524.bag')
# demo_web/app.py
from flask import Flask, request, render_template, redirect, url_for
from werkzeug.utils import secure_filename
import os, subprocess
from demo_web.pipeline import run_media_bat, run_pipeline

app = Flask(__name__)

# 設定上傳資料夾
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/api/upload', methods=['POST'])
def upload_files():
    # 確認有檔案欄位
    if 'files' not in request.files:
        return redirect(url_for('index'))

    files = request.files.getlist('files')
    if not files or files[0].filename == '':
        return redirect(url_for('index'))

    # 儲存上傳檔案
    saved_files = []
    for f in files:
        filename = secure_filename(f.filename)
        dest = os.path.join(UPLOAD_FOLDER, filename)
        try:
            f.save(dest)
        except Exception as e:
            return redirect(url_for('error_page', msg=f'儲存檔案失敗: {e}'))
        saved_files.append(dest)

    # 執行 .bat 處理檔案
    try:
        # 用 cmd.exe /c + 完整脚本路径，
        # 并且切到 BASE_DIR 执行，这样脚本里的 %~dp0 就会指向 demo_web/
        bat_path = os.path.join(BASE_DIR, 'process_media.bat')
        result = subprocess.run(
            f'cmd.exe /c "{bat_path}"',
            shell=True,
            cwd=BASE_DIR,
            capture_output=True,
            text=True
        )
        stdout_text = result.stdout.strip()
        stderr_text = result.stderr.strip()
        if result.returncode != 0:
            # 把 stderr 或 stdout 一并贴出来看看
            error_msg = stderr_text or stdout_text or f'返回碼 {result.returncode}'
            return redirect(url_for('error_page', msg=f'.bat 執行失敗: {error_msg}'))
    except Exception as e:
        return redirect(url_for('error_page', msg=f'呼叫 .bat 發生錯誤: {e}'))

    # 執行所有步驟
    try:
        data_path = os.path.join(BASE_DIR, '20250311_140524.bag')
        result = run_pipeline(pic_input=data_path)
        # result = run_pipeline(pic_input=saved_files[0])
    except Exception as e:
        return redirect(url_for('error_page', msg=f'Pipeline 執行失敗: {e}'))

    # 成功，渲染結果頁
    return render_template('result.html', logs=stdout_text, result=result)

# 成功頁面
@app.route('/upload_success')
def upload_success():
    return render_template('upload_success.html')

# 錯誤頁面
@app.route('/error')
def error_page():
    msg = request.args.get('msg', '發生錯誤')
    return render_template('error.html', message=msg)

if __name__ == '__main__':
    # 自動重載
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=True)
