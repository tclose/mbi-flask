import sys
import os
import os.path as op
import getpass
import random
import string
from app import db, app
from datetime import datetime
from app.reporting.models import (
    Subject, ImagingSession, ScanType, Report, session_scantype_assoc_table,
    report_scantype_assoc_table, user_role_assoc_table, User, Role)
from app.reporting.constants import MRI
from werkzeug import generate_password_hash  # noqa pylint: disable=no-name-in-module

db_path = app.config['SQLALCHEMY_DATABASE_URI'][10:]
if op.exists(db_path):
    if app.config['TEST']:
        os.remove(db_path)
    else:
        raise Exception(
            "Database has already been initialised at {}".format(db_path))

db.create_all()

admin_role = Role('admin')
reporter_role = Role('reporter')

db.session.add(admin_role)  # noqa pylint: disable=no-member
db.session.add(reporter_role)  # noqa pylint: disable=no-member

if not app.config['TEST']:
    admin_password = getpass.getpass(
        "Please enter password for admin account ('manager.mbi@monash.edu'): ")
    # Add administrator
    db.session.add(User('Administrator', '', 'manager.mbi@monash.edu',  # noqa pylint: disable=no-member
                    generate_password_hash(admin_password),
                    signature=None,
                    roles=[admin_role], active=True))
# Add dummy data to test with
else:
    scan_types = [
        ScanType('Head_t1_mprage'),
        ScanType('Head_t2_space_sag_p2_iso'),
        ScanType('t1_mprage_sag_p3_iso_1_ADNI'),
        ScanType('t2_space_sag_p2_iso'),
        ScanType('Head_No MT fl3d_axial_p2_iso')]

    db.session.add_all((  # noqa pylint: disable=no-member
        User('Dr Thomas G. Close', 'PHD', 'tom.close@monash.edu',
             generate_password_hash('password'),
             roles=[reporter_role, admin_role], active=True),
        User('Parisa Zakavi', '', 'parisa.zakavi@monash.edu',
             generate_password_hash('password'),
             roles=[reporter_role, admin_role], active=True)))

    subjects = []

    for mbi_id, dob, first_name, last_name in [
        ('MSH103138', '12/03/1952', 'Bob', 'Brown'),
        ('MSH223132', '05/12/1951', 'Sami', 'Shah'),
        ('MSH892342', '24/08/1980', 'Bill', 'Bryson'),
        ('MSH234234', '21/09/1993', 'Jesse', 'Jackson'),
        ('MSH623177', '15/12/1967', 'Robert', 'Redford'),
        ('MSH823056', '27/06/2001', 'Danny', 'DeVito'),
            ('MSH097334', '12/03/1972', 'Boris', 'Becker')]:
        subj = Subject(mbi_id, first_name, last_name,
                       datetime.strptime(dob, '%d/%m/%Y'))  # noqa pylint: disable=no-member
        subjects.append(subj)
        db.session.add(subj)  # pylint: disable=no-member

    img_sessions = {}

    for subj_id, study_id, xnat_id, xnat_uri, scan_date, priority in [
            (0, 1231, 'MRH100_124_MR02', 'MBI_XNAT_E00626', '10/04/2017', 1),
            (1, 1244, 'SHOULD_NOT_BE_SHOWN_NEWER_SESSION',
             'MBI_XNAT_E00627', '11/02/2018', 1),
            (1, 1254, 'MMH092_009_MRPT01', 'MBI_XNAT_E00628', '12/02/2018', 1),
            (2, 1366, 'MRH999_999_MR01', 'MBI_XNAT_E00629', '11/10/2017', 1),
            (2, 1500, 'SHOULD_NOT_BE_SHOWN_PREV_REPORT',
             'MBI_XNAT_E00630', '11/5/2018', 1),
            (2, 1600, 'MRH999_999_MR99', 'MBI_XNAT_E00631', '11/1/2019', 3),
            (3, 3413, 'MRH088_065_MR01', 'MBI_XNAT_E00632', '13/01/2019', 2),
            (4, 4500, 'MRH112_002_MR01', 'MBI_XNAT_E00633', '11/02/2019', 1),
            (5, 5003, 'MRH100_025_MR01', 'MBI_XNAT_E00634', '1/08/2017', 2),
            (6, 9834, 'SHOULD_BE_IGNORED', 'MBI_XNAT_E00635', '10/11/2018',
             0)]:
        img_session = img_sessions[study_id] = ImagingSession(
            study_id, subjects[subj_id], xnat_id, xnat_uri,
            datetime.strptime(scan_date, '%d/%m/%Y'),
            random.choices(scan_types,
                           k=random.randint(1, len(scan_types) - 1)),
            priority)
        db.session.add(img_session)  # noqa pylint: disable=no-member

    db.session.commit()  # noqa pylint: disable=no-member

    # Add report for 1366

    img_session = img_sessions[1366]
    db.session.add(Report(img_session.id, 1, "Nothing to report", 0,  # noqa pylint: disable=no-member
                          img_session.avail_scan_types, MRI))

# Add historial reporters for previously reported records
db.session.add_all((  # noqa pylint: disable=no-member
    User('Dr. Nicholas Ferris', 'MBBS FRANZCR',
        'nicholas.ferris@monash.edu',
        generate_password_hash(
            ''.join(random.choices(string.printable, k=50))),
        roles=[reporter_role], active=False),
    User('Dr. Paul Beech', 'MBBS FRANZCR FAANMS',
        'paul.beech@monash.edu',
        generate_password_hash(
            ''.join(random.choices(string.printable, k=50))),
        roles=[reporter_role], active=False),
    User('AXIS Reporting', '',
        's.ahern@axisdi.com.au ',
        generate_password_hash(
            ''.join(random.choices(string.printable, k=50))),
        roles=[reporter_role], active=False)))

db.session.commit()  # noqa pylint: disable=no-member
