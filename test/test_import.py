import os
import os.path as op
from json import dump
import sys
from app import app
from app.reporting.views import import_

# os.remove(op.join(op.dirname(__file__), 'databases', 'app.db'))

# init_db(password='password')

with app.app_context() as a:
    status, js = import_()

with open('/Users/tclose/Desktop/report-output.html', 'w') as f:
    dump(js, f)

print(js)
