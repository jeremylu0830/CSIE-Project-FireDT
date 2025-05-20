from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

app = Flask(__name__)
app.config.from_object('demo_web.config.Config')
db = SQLAlchemy(app)

# login_manager = LoginManager(app)
# login_manager.login_view = 'login'

from . import models, routes

with app.app_context():
    db.create_all()