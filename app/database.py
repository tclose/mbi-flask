#!/usr/bin/env python3
import sys
import os
import os.path as op
from argparse import ArgumentParser
import getpass
import random
import string
from datetime import datetime
from sqlalchemy import orm
from werkzeug import generate_password_hash  # noqa pylint: disable=no-name-in-module
# Ensure that the app directory is on the path
sys.path.append(op.abspath(op.join(op.dirname(__file__), '..')))
from app.models import (  # noqa
    Project, Subject, ImgSession, Scan, ScanType, Report,
    report_scan_assoc_table, user_role_assoc_table, User, Role)
from app.constants import (  # noqa
    MRI, ADMIN_ROLE, REPORTER_ROLE, LOW, MEDIUM, HIGH, PRESENT, NOT_FOUND,
    INVALID_LABEL)
from app import db, app  # noqa
from app.exceptions import DatabaseAlreadyInitialisedError  # noqa
sys.path.pop()


def init(password=None):

    db_path = app.config['SQLALCHEMY_DATABASE_URI'][10:]
    if op.exists(db_path):
        if app.config.get('TEST', False):
            os.remove(db_path)
        else:
            raise DatabaseAlreadyInitialisedError(
                "Database has already been initialised at {}".format(db_path))
    else:
        os.makedirs(op.dirname(db_path), exist_ok=True)

    db.create_all()

    admin_role = Role(ADMIN_ROLE, 'Administrator')
    reporter_role = Role(REPORTER_ROLE, 'Reporter')

    db.session.add(admin_role)  # noqa pylint: disable=no-member
    db.session.add(reporter_role)  # noqa pylint: disable=no-member

    if not app.config.get('TEST', False):
        if password is None:
            raise Exception("Admin password needs to be provided for "
                            "production database")
        # Add administrator
        db.session.add(User('Administrator', 'Account',  # noqa pylint: disable=no-member
                            app.config['ADMIN_EMAIL'],
                            generate_password_hash(password),
                            roles=[admin_role], active=True))
    # Add dummy data to test with
    else:
        scan_types = [
            ScanType('Head_t1_mprage'),
            ScanType('Head_t2_space_sag_p2_iso'),
            ScanType('t1_mprage_sag_p3_iso_1_ADNI'),
            ScanType('t2_space_sag_p2_iso'),
            ScanType('Head_No MT fl3d_axial_p2_iso'),
            ScanType('Shouldnt_be_shown')]

        db.session.add_all((  # noqa pylint: disable=no-member
            User('Thomas', 'Close', 'tom.close@monash.edu', suffixes='PHD',
                 title='Dr.', password=generate_password_hash('password'),
                 middle_name='G.', roles=[reporter_role, admin_role],
                 active=True),
            User('Parisa', 'Zakavi', 'parisa.zakavi@monash.edu',
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
            ('MSH097334', '12/03/1972', 'Boris', 'Becker'),
            ('MSH097335', '12/03/1972', 'Charlie', 'Chaplin'),
                ('MSH097336', '12/03/1972', 'Emilio', 'Estevez')]:
            subj = Subject(mbi_id, first_name, last_name,
                        datetime.strptime(dob, '%d/%m/%Y'))  # noqa pylint: disable=no-member
            subjects.append(subj)
            db.session.add(subj)  # pylint: disable=no-member

        img_sessions = {}

        for subj_id, study_id, xnat_id, scan_date, priority, status in [
                (0, 1231, 'MRH100_124_MR02', '10/04/2017', LOW, PRESENT),
                (1, 1244, 'SHOULD_NOT_BE_SHOWN_NEWER_SESSION', '11/02/2018',
                 LOW, PRESENT),
                (1, 1254, 'SHOULD_NOT_BE_SHOWN_AS_NOT_FOUND', '12/02/2018',
                 LOW, NOT_FOUND),
                (2, 1366, 'MRH999_999_MR01', '11/10/2017', LOW, PRESENT),
                (2, 1500, 'SHOULD_NOT_BE_SHOWN_PREV_REPORT', '11/5/2018', LOW,
                 PRESENT),
                (2, 1600, 'MRH999_999_MR99', '11/1/2019', HIGH, PRESENT),
                (3, 3413, 'MRH088_065_MR01', '13/01/2019', MEDIUM, PRESENT),
                (4, 4500, 'MRH112_002_MR01', '11/02/2019', LOW, PRESENT),
                (5, 5003, 'MRH100_025_MR01', '1/08/2017', MEDIUM, PRESENT),
                (6, 9834, 'SHOULD_NOT_BE_SHOWN_AS_NOT_EXPORTED', '10/11/2018',
                 LOW, PRESENT),
                (7, 9835, 'SHOULD_NOT_BE_SHOWN_AS_INVALID', '10/12/2018', LOW,
                 INVALID_LABEL),
                (8, 9836, 'SHOULD_NOT_BE_SHOWN_AS_NOT_PRESENT', '10/10/2018',
                 LOW, NOT_FOUND)]:
            project_id = xnat_id.split('_')[0]
            try:
                project = Project.query.filter_by(mbi_id=project_id).one()
            except orm.exc.NoResultFound:
                project = Project(project_id)
            img_session = img_sessions[study_id] = ImgSession(
                study_id, project, subjects[subj_id], xnat_id,
                datetime.strptime(scan_date, '%d/%m/%Y'),
                data_status=status, priority=priority)
            db.session.add(img_session)  # noqa pylint: disable=no-member
            for i, scan_type in enumerate(random.sample(
                    scan_types, random.randint(1, len(scan_types) - 1))):
                db.session.add(Scan(i, img_session, scan_type,  # noqa pylint: disable=no-member
                                    exported=scan_type.clinical))
        db.session.commit()  # noqa pylint: disable=no-member

        # Add report for 1366
        img_session = img_sessions[1366]
        db.session.add(Report(img_session.id, 1, "Nothing to report", 0,  # noqa pylint: disable=no-member
                            used_scans=img_session.scans, modality=MRI))

        # Set the final scan of the final session to be not-exported, so it
        # shouldn't show up
        img_sessions[9834].scans[-1].exported = False

        db.session.commit()  # noqa pylint: disable=no-member

    # Add historial reporters for previously reported records
    db.session.add_all((  # noqa pylint: disable=no-member
        User('Nicholas', 'Ferris', 'nicholas.ferris@monash.edu',
            generate_password_hash(
                ''.join(random.choices(string.printable, k=50))),
            suffixes='MBBS FRANZCR', title='Dr.', roles=[reporter_role],
            active=False),
        User('Paul', 'Beech', 'paul.beech@monash.edu',
            generate_password_hash(
                ''.join(random.choices(string.printable, k=50))),
            suffixes='MBBS FRANZCR', title='Dr.',
            roles=[reporter_role], active=False),
        User('AXIS', 'Reporting', 's.ahern@axisdi.com.au',
            generate_password_hash(
                ''.join(random.choices(string.printable, k=50))),
            roles=[reporter_role], active=False)))

    db.session.commit()  # noqa pylint: disable=no-member
    return db_path


if __name__ == '__main__':
    ACTIONS = ['init']
    parser = ArgumentParser("Perform actions on the Flask app database")
    parser.add_argument('action', help="The action to perform", type=str,
                        choices=ACTIONS)
    parser.add_argument('--password', '-p', default=None,
                        help="The password for the admin account")
    args = parser.parse_args()

    if args.action == 'init':
        if args.password is None:
            password = getpass.getpass(
                "Please enter password for admin account "
                "('manager.mbi@monash.edu'): ")
        else:
            password = args.password

        try:
            db_path = init(password)
        except DatabaseAlreadyInitialisedError:
            print("Database already initialised")
        else:
            print("Successfully initialised database at {}"
                  .format(db_path))
    else:
        print("Unrecognised action '{}' can be one of {}".format(args.action,
                                                                 ACTIONS))
