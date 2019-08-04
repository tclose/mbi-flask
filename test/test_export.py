import os
import os.path as op
from app import app
from json import dump
from app.reporting.views import export

with app.app_context() as a:
    status, js = export()

with open('/Users/tclose/Desktop/report-output.html', 'w') as f:
    dump(js, f)

print("Status: {}".format(status))
print(js)
