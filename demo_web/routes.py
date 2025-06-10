from flask import (
    render_template, request, redirect, url_for,
    send_file, abort, flash
)
from datetime import datetime
from demo_web import app, db
from demo_web.models import User, File
from demo_web.utils import save_uploaded_files
from demo_web.pipeline import run_pipeline
from flask_login import LoginManager, login_user, login_required, logout_user, current_user

import os 
import subprocess

VIDEO_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'material_segmentation', 'fds_output')
AVI_PATH = os.path.join(VIDEO_DIR, "movie_fire.avi")
AVI_PATH_2 = os.path.join(VIDEO_DIR, "movie_smoke.avi")

NEW_VIDEO_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'material_segmentation', 'videos')


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
        data_path = os.path.join(os.path.dirname(__file__), '20250605_171517.bag')
        result = run_pipeline(pic_input=data_path)

        # 生成檔案名稱，包含使用者ID與上傳時間
        current_time = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        if current_user.is_authenticated:
            filename_fire = f"{current_user.username}_fire.mp4"
            filename_smoke = f"{current_user.username}_smoke.mp4"
        else:
            filename_fire = f"anonymous_fire.mp4"
            filename_smoke = f"anonymous_smoke.mp4"

        # 使用靜態路徑來儲存影片
        MP4_PATH_DYNAMIC = os.path.join(NEW_VIDEO_DIR, filename_fire)
        MP4_PATH_2_DYNAMIC = os.path.join(NEW_VIDEO_DIR, filename_smoke)
            
        # 處理第一個影片
        if os.path.exists(AVI_PATH):
            if os.path.exists(MP4_PATH_DYNAMIC):
                try:
                    os.remove(MP4_PATH_DYNAMIC)
                except OSError:
                    pass
            subprocess.run([
                "ffmpeg",
                "-y",  # 若 MP4 已存在，強制覆蓋
                "-i", AVI_PATH,
                "-c:v", "libx264",
                "-c:a", "aac",
                MP4_PATH_DYNAMIC
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # 儲存影片資料到資料庫，僅在使用者登入時才儲存資料
            if current_user.is_authenticated:
                filename_fire = f"{current_user.id}_{current_time}_fire.mp4"
                video1 = File(user_id=current_user.id, file_name=filename_fire, file_path=MP4_PATH_DYNAMIC)
                db.session.add(video1)

        else:
            return redirect(url_for('error_page', msg=f"找不到影片檔：{AVI_PATH}"))

        # 處理第二個影片
        if os.path.exists(AVI_PATH_2):
            if os.path.exists(MP4_PATH_2_DYNAMIC):
                try:
                    os.remove(MP4_PATH_2_DYNAMIC)
                except OSError:
                    pass
            subprocess.run([
                "ffmpeg",
                "-y",  # 若 MP4 已存在，強制覆蓋
                "-i", AVI_PATH_2,
                "-c:v", "libx264",
                "-c:a", "aac",
                MP4_PATH_2_DYNAMIC
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # 儲存第二個影片資料到資料庫，僅在使用者登入時才儲存資料
            if current_user.is_authenticated:
                filename_smoke = f"{current_user.id}_{current_time}_smoke.mp4"
                video2 = File(user_id=current_user.id, file_name=filename_smoke, file_path=MP4_PATH_2_DYNAMIC)
                db.session.add(video2)

        else:
            return redirect(url_for('error_page', msg=f"找不到第二個影片檔：{AVI_PATH_2}"))

        # 提交資料到資料庫
        if current_user.is_authenticated:
            db.session.commit()

    except subprocess.CalledProcessError as e:
        return redirect(url_for('error_page', msg=f"轉檔失敗: {e}"))
    except Exception as e:
        return redirect(url_for('error_page', msg=f'Pipeline 或轉檔執行失敗: {e}'))

    # 上傳與轉檔完成後，讓前端去 /video 撈兩個 MP4
    return redirect(url_for('video'))

@app.route('/video')
def video():
    # 檢查使用者是否已登入，並設置預設 ID
    if current_user.is_authenticated:
        user_id = current_user.id
    else:
        user_id = 'anonymous'  # 或者設為0，根據你的需求


    # 動態生成影片的路徑
    video_path_1 = os.path.join(NEW_VIDEO_DIR, f"{user_id}_fire.mp4")
    video_path_2 = os.path.join(NEW_VIDEO_DIR, f"{user_id}_smoke.mp4")

    # 檢查兩個 MP4 檔案是否存在
    if not os.path.exists(video_path_1) or not os.path.exists(video_path_2):
        return abort(404)

    # 傳遞兩個影片的 URL 給前端
    video_urls = {
        "video1": url_for('send_video', video_id=1),
        "video2": url_for('send_video', video_id=2)
    }
    
     # 根據使用者是否登入來決定重定向的頁面
    if current_user.is_authenticated:
        return render_template('member.html', video_urls=video_urls,user = current_user)  # 登入使用者，回傳 member 頁面
    else:
        return render_template('index.html', video_urls=video_urls)  # 匿名使用者，回傳 index 頁面

@app.route('/send_video/<int:video_id>')
def send_video(video_id):
    # 檢查使用者是否已登入，並設置預設 ID
    if current_user.is_authenticated:
        user_id = current_user.id
    else:
        user_id = 'anonymous'  # 或者設為0，根據你的需求

    if video_id == 1:
        video_path = os.path.join(NEW_VIDEO_DIR, f"{user_id}_fire.mp4")
        if not os.path.exists(video_path):
            return abort(404)
        return send_file(video_path, mimetype='video/mp4')
    
    elif video_id == 2:
        video_path = os.path.join(NEW_VIDEO_DIR, f"{user_id}_smoke.mp4")
        if not os.path.exists(video_path):
            return abort(404)
        return send_file(video_path, mimetype='video/mp4')
    
    else:
        return abort(404)


@app.route('/error')
def error_page():
    msg = request.args.get('msg', '發生錯誤')
    return render_template('error.html', message=msg)