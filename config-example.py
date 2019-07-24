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

ALFRED_START_DATE = datetime(2019, 7, 2)
