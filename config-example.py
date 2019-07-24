from datetime import datetime, timedelta
import os
from datetime import datetime
import os.path as op

DEBUG = False
TEST = True

SECRET_KEY = 'ARandomStringOfCharacters'

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + op.join(
    op.abspath(op.dirname(__file__)), 'app.db')

WTF_CSRF_ENABLED = True
WTF_CSRF_SECRET_KEY = "AnotherRandomStringOfCharacters"


XNAT_URL = 'https://172.22.2.13/xnat'
ADMIN_EMAIL = 'mbi-informatics@monash.edu'

FILEMAKER_EXPORT_FILE = op.join(
    op.abspath(op.dirname(__file__)), 'reports_status.csv')

AUTO_LOGOUT_PERIOD = timedelta(minutes=30)

UPLOADED_SIGNATURE_DEST = op.join(
    op.abspath(op.dirname(__file__)), 'uploads', 'signatures')

os.makedirs(UPLOADED_SIGNATURE_DEST, exist_ok=True)

MAIL_SERVER = 'localhost'
MAIL_PORT = 25
MAIL_USE_TLS = False
MAIL_USE_SSL = False
MAIL_USERNAME = None
MAIL_PASSWORD = None
MAIL_DEFAULT_SENDER = ADMIN_EMAIL
