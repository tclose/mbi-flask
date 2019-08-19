from json import dump, dumps
from app import app
import logging
from app.reporting.views import sync_filemaker

app.logger.setLevel(logging.INFO)  # pylint: disable=no-member
handler = logging.StreamHandler()
formatter = logging.Formatter("%(levelname)s - %(message)s")
handler.setFormatter(formatter)
app.logger.addHandler(handler)  # pylint: disable=no-member

# os.remove(op.join(op.dirname(__file__), 'databases', 'app.db'))

# init_db(password='password')

with app.app_context() as a:
    status, js = sync_filemaker()

with open('/Users/tclose/Desktop/fm-sync-output.json', 'w') as f:
    dump(js, f, indent=4, sort_keys=True)

print(dumps(js, indent=4, sort_keys=True))
