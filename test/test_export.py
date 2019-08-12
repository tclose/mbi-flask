import os
import os.path as op
import sys
from json import dump
from app import app
from app.reporting.views import export

with app.app_context() as a:
    status, js = export()

with open('/Users/tclose/Desktop/report-output.html', 'w') as f:
    dump(js, f)

print("Status: {}".format(status))
print(js)
