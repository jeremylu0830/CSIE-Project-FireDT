from demo_web import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    files = db.relationship('File', backref='owner', lazy=True)
    
    def set_password(self, plaintext_password):
        self.password_hash = generate_password_hash(plaintext_password)

    def check_password(self, plaintext_password):
        return check_password_hash(self.password_hash, plaintext_password)

class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    file_name = db.Column(db.String(120), nullable=False)
    file_path = db.Column(db.String(250), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)