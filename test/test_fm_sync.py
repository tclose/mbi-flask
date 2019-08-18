from json import dump
from app import app
import logging
from app.reporting.views import sync_filemaker

app.logger.setLevel(logging.INFO)

# os.remove(op.join(op.dirname(__file__), 'databases', 'app.db'))

# init_db(password='password')

with app.app_context() as a:
    status, js = sync_filemaker()

with open('/Users/tclose/Desktop/report-output.html', 'w') as f:
    dump(js, f)

print(js)
