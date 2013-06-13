import os
basedir = os.path.abspath(os.path.dirname(__file__))

CSRF_ENABLED = True
SECRET_KEY = 'you can not imagine'

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')

DEBUG = True

CONTENT_DIR = os.path.join(basedir, 'wiki')
#EMAIL SETTINGS
MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 465
MAIL_USE_SSL = True
MAIL_USE_TLS = False
MAIL_USERNAME = 'brotherbigger@gmail.com'
MAIL_PASSWORD = '0358wsadjkln'
DEFAULT_MAIL_SENDER = 'brotherbigger@google.com'

LANGUAGES = {
    'en': 'English',
    'zh': 'Chinese Simplified'
}

BABEL_DEFAULT_LOCALE = 'zh_cn'