import os
repo_root = os.path.abspath(os.path.dirname(__file__))

DEBUG = False

ADMIN_EMAIL = 'mbi-informatics@monash.edu'

ADMINS = frozenset(['tom.close@monash.edu'])
SECRET_KEY = 'SecretKeyForSessionSigning'

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(repo_root, 'app.db')
DATABASE_CONNECT_OPTIONS = {}

THREADS_PER_PAGE = 8

CSRF_ENABLED = True
CSRF_SESSION_KEY = "eegeiVai5ijoihucak4pheeso5eegae5"
