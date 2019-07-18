from mbi_flask import db
from mbi_flask.apps.reporting.models import (
    Subject, ImagingSession, ScanType, Report, session_scantype_assoc_table,
    report_scantype_assoc_table, user_role_assoc_table, User, Role)

db.create_all()
