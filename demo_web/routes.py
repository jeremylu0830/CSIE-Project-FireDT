from flask import render_template, request, redirect, url_for
from demo_web import app
from demo_web.utils import save_uploaded_files
from demo_web.pipeline import run_pipeline
import os

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/upload', methods=['POST'])
def upload_files():
    if 'files' not in request.files:
        return redirect(url_for('index'))

    files = request.files.getlist('files')
    if not files or files[0].filename == '':
        return redirect(url_for('index'))

    saved_files, error_msg = save_uploaded_files(files)
    if saved_files is None:
        return redirect(url_for('error_page', msg=error_msg))

    try:
        data_path = os.path.join(os.path.dirname(__file__), '20250311_140524.bag')
        result = run_pipeline(pic_input=data_path)
        #result = run_pipeline(pic_input=saved_files[0])
    except Exception as e:
        return redirect(url_for('error_page', msg=f'Pipeline 執行失敗: {e}'))

    return render_template('result.html', result=result)

@app.route('/error')
def error_page():
    msg = request.args.get('msg', '發生錯誤')
    return render_template('error.html', message=msg)