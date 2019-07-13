import os
import os.path as op
from mbi_flask import db
from datetime import datetime
from mbi_flask.apps.reporting.models import (
    Subject, ImagingSession, ScanType, Report, scan_type_assoc_table, Reporter)
from werkzeug import generate_password_hash  # noqa pylint: disable=no-name-in-module

db_path = op.join(op.dirname(__file__), 'app.db')
if op.exists(db_path):
    os.remove(db_path)

db.create_all()

db.session.add(Reporter('Dr Thomas G. Close', 'PHD', 'tom.close@monash.edu',  # noqa pylint: disable=no-member
                        generate_password_hash('Jygbiq-juqrad-8seqxu')))

for i, (subj_id, dob, study_id, xnat_id, scan_date, priority) in enumerate([
        ('MSH103138', '12/03/1952', 1231, 'MRH100_124_MR02', '10/04/2017', 0),
        ('MSH223132', '5/12/1951', 1244, 'MRH112_002_MR01', '11/02/2019', 0),
        ('MSH892342', '24/08/1980', 1366, 'MRH123_350_MR01', '11/10/2018', 0),
        ('MSH234234', '21/09/1983', 3413, 'MRH088_065_MR01', '13/01/2019', 2),
        ('MSH823056', '27/06/1985', 5003, 'MRH100_025_MR01', '1/08/2017', 1),
        ('MSH097334', '12/03/1952', 9834, 'MRH099_003_MR03', '10/11/2018', 1)],
        start=1):
    db.session.add(Subject(subj_id, datetime.strptime(dob, '%d/%m/%Y')))  # noqa pylint: disable=no-member
    db.session.add(ImagingSession(  # noqa pylint: disable=no-member
        study_id, i, xnat_id, datetime.strptime(scan_date, '%d/%m/%Y'),
        priority))

db.session.commit()  # noqa pylint: disable=no-member
