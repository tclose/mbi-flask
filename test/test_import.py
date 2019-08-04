import os
import os.path as op
from app import app
from json import dump
from app.reporting.views import import_
from app.database import init_db

# os.remove(op.join(op.dirname(__file__), 'databases', 'app.db'))

# init_db(password='password')

with app.app_context() as a:
    status, js = import_()

with open('/Users/tclose/Desktop/report-output.html', 'w') as f:
    dump(js, f)

print(js)
