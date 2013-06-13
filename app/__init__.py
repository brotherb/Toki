from flask import Flask
from flask.ext.login import LoginManager
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.mail import Mail
from flask.ext.babel import Babel, lazy_gettext as _
import os
import subprocess

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)
lm = LoginManager()
lm.init_app(app)
lm.login_view = 'login'
lm.login_message = _('Please log in to access this page.')
mail = Mail(app)
babel = Babel(app)

if not os.path.exists(app.config['CONTENT_DIR']):
    print 'content directory not exist, Toki will make it for u'
    work_dir = os.path.abspath(os.curdir)
    os.mkdir(app.config['CONTENT_DIR'])
    os.chdir(app.config['CONTENT_DIR'])
    subprocess.call('git init', shell=True)
    os.chdir(work_dir)


def clear_time(time):
    return '%s-%s-%s %s:%s' % (time.year, time.month, time.day, time.hour, time.minute)


def format_float(value):
    return "{:,.1f}".format(value)

app.jinja_env.globals.update(clear_time=clear_time)
app.jinja_env.globals.update(format_float=format_float)

from app import forms, views