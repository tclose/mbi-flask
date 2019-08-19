import os.path as op
from app import app
import logging
from app.database import import_old_reports

app.logger.setLevel(logging.INFO)  # pylint: disable=no-member
handler = logging.StreamHandler()
formatter = logging.Formatter("%(levelname)s - %(message)s")
handler.setFormatter(formatter)
app.logger.addHandler(handler)  # pylint: disable=no-member

export_file = op.join(op.dirname(__file__), '..', 'fm-export',
                      'old-report-export.tsv')

with app.app_context() as a:
    import_old_reports(export_file)

print('Done')
