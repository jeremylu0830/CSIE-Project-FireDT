from flask import (
    render_template, request, redirect, url_for,
    send_file, abort, flash
)
from demo_web import app, db
from demo_web.models import User, File
from demo_web.utils import save_uploaded_files
from demo_web.pipeline import run_pipeline
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
import os 
import subprocess

VIDEO_DIR = r"D:\CSIE_project\CSIE-Project-FireDT\material_segmentation\fds_output"
AVI_PATH = os.path.join(VIDEO_DIR, "movie.avi")
MP4_PATH = os.path.join(VIDEO_DIR, "movie.mp4")

# @app.route('/')
# def index():
#     return render_template('index.html', video_url=None)


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html', video_url=None)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    
    # 2. 查詢資料庫，看有沒有這個 username
    user = User.query.filter_by(username=username).first()

    # 3. 如果找不到 user，或是密碼比對失敗
    if user is None or not user.check_password(password):
        # 3.1 你可以用 flash() 顯示錯誤訊息，也可以直接 redirect 到錯誤頁
        flash('帳號或密碼錯誤，請重新嘗試。', 'danger')
        return redirect('/login')
    
    # 4. 代表帳號存在且密碼正確，呼叫 login_user 將使用者登入
    login_user(user)
    
    return render_template('member.html', user=user)

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username', '').strip()
    email    = request.form.get('email', '').strip()
    password = request.form.get('password', '')

    
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return redirect(url_for('error', msg='user already exists'))

    existing_email = User.query.filter_by(email=email).first()
    if existing_email:
        return redirect(url_for('error', msg='email is already registered'))
    
    # new user
    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    
    return redirect('/')
    

@app.route('/login', methods=['GET'])
def show_login():
    return render_template('login.html')

@app.route('/register', methods=['GET'])
def show_register():
    return render_template('register.html')

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
        if os.path.exists(AVI_PATH):
        # 如果之前已經存在 MP4，就先刪掉，避免播放舊檔
            if os.path.exists(MP4_PATH):
                try:
                    os.remove(MP4_PATH)
                except OSError:
                    pass
            # Popen 會立刻返回，不會等轉檔結束
            subprocess.Popen([
                "ffmpeg",
                "-y",  # 若 MP4 已存在，強制覆蓋
                "-i", AVI_PATH,
                "-c:v", "libx264",
                "-c:a", "aac",
                MP4_PATH
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            return redirect(url_for('error_page', msg=f"找不到影片檔：{AVI_PATH}"))
    except subprocess.CalledProcessError as e:
        return redirect(url_for('error_page', msg=f"轉檔失敗: {e}"))
    except Exception as e:
        return redirect(url_for('error_page', msg=f'Pipeline 或轉檔執行失敗: {e}'))

    # 上傳與轉檔完成後，讓前端去 /video 撈 MP4
    return render_template('index.html', video_url=url_for('video'))

@app.route('/video')
def video():
    # 先看 MP4 是否存在，若無則 404
    if not os.path.exists(MP4_PATH):
        return abort(404)
    # 回傳 MP4，MIME type 要用 video/mp4
    return send_file(MP4_PATH, mimetype='video/mp4')


@app.route('/error')
def error_page():
    msg = request.args.get('msg', '發生錯誤')
    return render_template('error.html', message=msg)