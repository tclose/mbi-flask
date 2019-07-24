from datetime import datetime, timedelta
import os
from datetime import datetime
import os.path as op

PKG_ROOT = op.abspath(op.dirname(__file__))

DEBUG = False
TEST = True

if TEST:
    DB_NAME = 'test.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
else:
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DB_NAME = 'app.db'

SECRET_KEY = 'ARandomStringOfCharacters'


os.makedirs(op.join(PKG_ROOT, 'databases'), exist_ok=True)

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + op.join(
    PKG_ROOT, 'databases', DB_NAME)

WTF_CSRF_ENABLED = True
WTF_CSRF_SECRET_KEY = "AnotherRandomStringOfCharacters"


XNAT_URL = 'https://172.22.2.13/xnat'
ADMIN_EMAIL = 'mbi-informatics@monash.edu'

FILEMAKER_EXPORT_FILE = op.join(PKG_ROOT, 'reports_status.csv')

AUTO_LOGOUT_PERIOD = timedelta(minutes=30)

UPLOADED_SIGNATURE_DEST = op.join(PKG_ROOT, 'uploads', 'signatures')

os.makedirs(UPLOADED_SIGNATURE_DEST, exist_ok=True)


MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 465
MAIL_USE_SSL = True
MAIL_USERNAME = ADMIN_EMAIL
MAIL_PASSWORD = 'admin-email-password'
MAIL_DEFAULT_SENDER = ADMIN_EMAIL
