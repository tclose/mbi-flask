import os
import os.path as op
from mbi_flask import db

os.remove(op.join(op.dirname(__file__), 'app.db'))

db.create_all()
