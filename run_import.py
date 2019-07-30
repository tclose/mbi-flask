from app import app
from json import dump
from app.reporting.views import import_

with app.app_context() as a:
    js = import_()

with open('/Users/tclose/Desktop/report-output.html', 'w') as f:
    dump(js, f)

print(js)
