import sys
import os
import os.path as op
import random
from mbi_flask import db, app
from datetime import datetime
from mbi_flask.apps.reporting.models import (
    Subject, ImagingSession, ScanType, Report, session_scantype_assoc_table,
    report_scantype_assoc_table, user_role_assoc_table, User, Role)
from werkzeug import generate_password_hash  # noqa pylint: disable=no-name-in-module

db_path = app.config['SQLALCHEMY_DATABASE_URI'][10:]
if op.exists(db_path):
    os.remove(db_path)

db.create_all()

admin_role = Role('admin')
reporter_role = Role('reporter')

db.session.add(admin_role)  # noqa pylint: disable=no-member
db.session.add(reporter_role)  # noqa pylint: disable=no-member

scan_types = [
    ScanType('Head_t1_mprage'),
    ScanType('Head_t2_space_sag_p2_iso'),
    ScanType('t1_mprage_sag_p3_iso_1_ADNI'),
    ScanType('t2_space_sag_p2_iso'),
    ScanType('Head_No MT fl3d_axial_p2_iso')]

db.session.add(User('Dr Thomas G. Close', 'PHD', 'tom.close@monash.edu',  # noqa pylint: disable=no-member
                    generate_password_hash('Jygbiq-juqrad-8seqxu'),
                    roles=[reporter_role, admin_role], active=True),
               User('Parisa Zakavi', '', 'parisa.zakavi@monash.edu',  # noqa pylint: disable=no-member
                    generate_password_hash('password'),
                    roles=[reporter_role, admin_role], active=True))

for mbi_subj_id, dob in [('MSH103138', '12/03/1952'),
                         ('MSH223132', '05/12/1951'),
                         ('MSH892342', '24/08/1980'),
                         ('MSH234234', '21/09/1993'),
                         ('MSH623177', '15/12/1967'),
                         ('MSH823056', '27/06/2001'),
                         ('MSH097334', '12/03/1972')]:
    db.session.add(Subject(mbi_subj_id, datetime.strptime(dob, '%d/%m/%Y')))  # noqa pylint: disable=no-member

img_sessions = {}

for subj_id, study_id, xnat_id, xnat_uri, scan_date, priority in [
        (1, 1231, 'MRH100_124_MR02', 'MBI_XNAT_E00626', '10/04/2017', 0),
        (2, 1244, 'SHOULD_NOT_BE_SHOWN_NEWER_SESSION',
         'MBI_XNAT_E00627', '11/02/2018', 0),
        (2, 1254, 'MMH092_009_MRPT01', 'MBI_XNAT_E00628', '12/02/2018', 0),
        (3, 1366, 'MRH999_999_MR01', 'MBI_XNAT_E00629', '11/10/2017', 0),
        (3, 1500, 'SHOULD_NOT_BE_SHOWN_PREV_REPORT',
         'MBI_XNAT_E00630', '11/5/2018', 0),
        (3, 1600, 'MRH999_999_MR99', 'MBI_XNAT_E00631', '11/1/2019', 2),
        (4, 3413, 'MRH088_065_MR01', 'MBI_XNAT_E00632', '13/01/2019', 1),
        (5, 4500, 'MRH112_002_MR01', 'MBI_XNAT_E00633', '11/02/2019', 0),
        (6, 5003, 'MRH100_025_MR01', 'MBI_XNAT_E00634', '1/08/2017', 1),
        (7, 9834, 'MRH099_003_MR03', 'MBI_XNAT_E00635', '10/11/2018', 1)]:
    img_session = img_sessions[study_id] = ImagingSession(
        study_id, subj_id, xnat_id, xnat_uri,
        datetime.strptime(scan_date, '%d/%m/%Y'),
        random.choices(scan_types, k=random.randint(1, len(scan_types) - 1)),
        priority)
    db.session.add(img_session)  # noqa pylint: disable=no-member

db.session.commit()  # noqa pylint: disable=no-member

# Add report for 1366

img_session = img_sessions[1366]
db.session.add(Report(img_session.id, 1, "Nothing to report", 0,  # noqa pylint: disable=no-member
                      img_session.avail_scan_types, date=datetime.today()))

db.session.commit()  # noqa pylint: disable=no-member
