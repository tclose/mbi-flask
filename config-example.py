import os
import os.path as op
from datetime import datetime, timedelta

PKG_ROOT = op.abspath(op.dirname(__file__))

DEBUG = False
TEST = True

os.makedirs(op.join(PKG_ROOT, 'databases'), exist_ok=True)

if TEST:
    DB_NAME = 'test.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
else:
    DB_NAME = 'app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + op.join(
    PKG_ROOT, 'databases', DB_NAME)

SECRET_KEY = 'a-long-arbitrary-string-of-chars'

SOURCE_XNAT_URL = 'https://mbi-xnat.erc.monash.edu.au'
SOURCE_XNAT_USER = 'a-xnat-user'
SOURCE_XNAT_PASSWORD = 'the-password'

TARGET_XNAT_URL = 'https://mbi-xnat-dev.erc.monash.edu.au'
TARGET_XNAT_USER = 'another-xnat-user'
TARGET_XNAT_PASSWORD = 'the-password'

TARGET_XNAT_PROJECT = 'MBIReporting'

TEMP_DOWNLOAD_DIR = '/Users/tclose/Downloads/FlaskExport'

WTF_CSRF_ENABLED = True
WTF_CSRF_SECRET_KEY = 'another-long-arbitrary-string-of-chars'

ADMIN_EMAIL = 'mbi-informatics@monash.edu'

FILEMAKER_IMPORT_FILE = op.join(PKG_ROOT, 'to-import', 'filemaker-export.csv')

AUTO_LOGOUT_PERIOD = timedelta(minutes=30)

NUM_ROWS_PER_PAGE = 25

# The number of days between sessions before a new report is required
REPORT_INTERVAL = 365

UPLOADED_SIGNATURE_DEST = op.join(PKG_ROOT, 'uploads', 'signatures')

os.makedirs(UPLOADED_SIGNATURE_DEST, exist_ok=True)


MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 465
MAIL_USE_SSL = True
MAIL_USERNAME = 'your.name@monash.edu'
MAIL_PASSWORD = 'the-password'
MAIL_DEFAULT_SENDER = ADMIN_EMAIL
