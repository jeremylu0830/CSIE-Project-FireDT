import os
import datetime
import secrets
from werkzeug.utils import secure_filename

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def save_uploaded_files(files):
    saved_files = []
    for f in files:
        filename = secure_filename(f.filename)
        datetime_str = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        file_ext = os.path.splitext(filename)[1]
        unique_id = secrets.token_hex(8)
        filename = f"{datetime_str}_{unique_id}{file_ext}"
        dest = os.path.join(UPLOAD_FOLDER, filename)
        try:
            f.save(dest)
        except Exception as e:
            return None, f"[ERROR] saved file unsuccessfully: {e}"
        saved_files.append(dest)
    return saved_files, None