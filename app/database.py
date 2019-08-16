#!/usr/bin/env python3
from tqdm import tqdm
import sys
import os
import re
import csv
import os.path as op
from argparse import ArgumentParser
import getpass
import random
import string
from datetime import datetime
from sqlalchemy import orm
import xnat
from xnat.exceptions import XNATResponseError
from werkzeug import generate_password_hash  # noqa pylint: disable=no-name-in-module
# Ensure that the app directory is on the path
sys.path.append(op.abspath(op.join(op.dirname(__file__), '..')))
from app.constants import (  # noqa
    LOW, NOT_RECORDED, MRI, PET, REPORTER_ROLE, ADMIN_ROLE,
    PRESENT, NOT_FOUND, UNIMELB_DARIS, INVALID_LABEL, NOT_CHECKED)
from app.models import (  # noqa
    Project, Subject, ImgSession, Scan, ScanType, Report,
    report_scan_assoc_table, user_role_assoc_table, User, Role)
from app.constants import (  # noqa
    MRI, ADMIN_ROLE, REPORTER_ROLE, LOW, MEDIUM, HIGH, PRESENT, NOT_FOUND,
    INVALID_LABEL)
from app import db, app  # noqa
from app.exceptions import DatabaseAlreadyInitialisedError  # noqa
sys.path.pop()


daris_id_re = re.compile(r'1008\.2\.(\d+)\.(\d+)(?:\.1\.(\d+))?.*')


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


def initial_import(export_file):
    """
    Imports data from a CSV file generated by the 'Export study reports'
    script in the FileMaker DB. Includes previously submitted reports which are
    not exported when you just dump the tables to file.

    Parameters
    ----------
    export_file : str
        Path to the output file of the 'Export study reports' script
    """
    if not op.exists(export_file):
        raise Exception("Could not find an FileMaker export file at {}"
                        .format(export_file))
    imported = []
    previous = []
    skipped = []
    # Get previous reporters
    nick_ferris = User.query.filter_by(
        email='nicholas.ferris@monash.edu').one()
    paul_beech = User.query.filter_by(email='paul.beech@monash.edu').one()
    axis = User.query.filter_by(email='s.ahern@axisdi.com.au').one()
    with xnat.connect(server=app.config['SOURCE_XNAT_URL'],
                      user=app.config['SOURCE_XNAT_USER'],
                      password=app.config['SOURCE_XNAT_PASSWORD']) as mbi_xnat:
        with open(export_file) as f:
            rows = list(csv.DictReader(f))
            for row in tqdm(rows):
                data_status = PRESENT
                # Check to see if the project ID is one of the valid types
                mbi_project_id = row['ProjectID']
                if mbi_project_id is None or not mbi_project_id:
                    mbi_project_id = ''
                    data_status = INVALID_LABEL
                else:
                    mbi_project_id = mbi_project_id.strip()
                    if mbi_project_id[:3] not in ('MRH', 'MMH', 'CLF'):
                        print("skipping {} from {}".format(row['StudyID'],
                                                           mbi_project_id))
                        skipped.append(row)
                        continue
                try:
                    project = Project.query.filter_by(
                        mbi_id=mbi_project_id).one()
                except orm.exc.NoResultFound:
                    project = Project(mbi_project_id)
                    db.session.add(project)  # pylint: disable=no-member
                db.session.commit()  # pylint: disable=no-member
                # Extract subject information from CSV row
                mbi_subject_id = (row['SubjectID'].strip()
                                  if row['SubjectID'] is not None else '')
                study_id = (row['StudyID'].strip()
                            if row['StudyID'] is not None else '')
                first_name = (row['FirstName'].strip()
                              if row['FirstName'] is not None else '')
                last_name = (row['LastName'].strip()
                             if row['LastName'] is not None else '')
                try:
                    dob = (datetime.strptime(row['DOB'].replace('.', '/'),
                                             '%d/%m/%Y')
                           if row['DOB'] is not None else datetime(1, 1, 1))
                except ValueError:
                    raise Exception(
                        "Could not parse date of birth of {} ({})"
                        .format(study_id, row['DOB']))
                # Check to see if subject is present in database already
                # otherwise add them
                try:
                    subject = Subject.query.filter_by(
                        mbi_id=mbi_subject_id).one()
                except orm.exc.NoResultFound:
                    subject = Subject(mbi_subject_id,
                                      first_name, last_name, dob)
                    db.session.add(subject)  # pylint: disable=no-member
                # Check to see whether imaging session has previously been
                # reported or not
                if ImgSession.query.get(study_id) is None:
                    # Parse scan date
                    try:
                        scan_date = datetime.strptime(
                            row['ScanDate'].replace('.', '/'), '%d/%m/%Y')
                    except ValueError:
                        raise Exception("Could not parse scan date for {} ({})"
                                        .format(study_id, row['ScanDate']))
                    # Extract subject and visit ID from DARIS ID or explicit
                    # fields
                    if row['DarisID']:
                        match = daris_id_re.match(row['DarisID'])
                        if match is not None:
                            _, subject_id, visit_id = match.groups()
                            if visit_id is None:
                                visit_id = '1'
                        else:
                            subject_id = visit_id = ''
                            if row['DarisID'].startswith('1.5.'):
                                data_status = UNIMELB_DARIS
                            else:
                                data_status = INVALID_LABEL
                    else:
                        try:
                            subject_id = row['XnatSubjectID'].strip()
                        except (KeyError, AttributeError):
                            subject_id = ''
                        try:
                            visit_id = visit_id = row['XnatVisitID'].strip()
                        except (KeyError, AttributeError):
                            visit_id = ''
                        if not subject_id or not visit_id:
                            data_status = INVALID_LABEL
                    try:
                        subject_id = int(subject_id)
                    except ValueError:
                        pass
                    else:
                        subject_id = '{:03}'.format(subject_id)
                    # Determine whether there are outstanding report(s) for
                    # this session or not and what the XNAT session prefix is
                    all_reports_submitted = bool(row['MrReport'])
                    if mbi_project_id.startswith('MMH'):
                        visit_prefix = 'MRPT'
                        all_reports_submitted &= bool(row['PetReport'])
                    else:
                        visit_prefix = 'MR'
                    # Get the visit part of the XNAT ID
                    try:
                        numeral, suffix = re.match(r'(\d+)(.*)',
                                                   visit_id).groups()
                        visit_id = '{}{:02}{}'.format(
                            visit_prefix, int(numeral),
                            (suffix if suffix is not None else ''))
                    except (ValueError, TypeError, AttributeError):
                        data_status = INVALID_LABEL
                    xnat_id = '_'.join(
                        (mbi_project_id, subject_id, visit_id)).upper()
                    # If the session hasn't been reported on check XNAT for
                    # matching session so we can export appropriate scans to
                    # the alfred
                    scan_ids = []
                    if all_reports_submitted:
                        data_status = NOT_CHECKED
                    elif data_status not in (INVALID_LABEL, UNIMELB_DARIS):
                        try:
                            exp = mbi_xnat.experiments[xnat_id]  # noqa pylint: disable=no-member
                        except KeyError:
                            data_status = NOT_FOUND
                        else:
                            try:
                                for scan in exp.scans.values():
                                    scan_ids.append((scan.id, scan.type))
                            except XNATResponseError as e:
                                raise Exception(
                                    "Problem reading scans of {} ({}):\n{}"
                                    .format(study_id, xnat_id, str(e)))
                    session = ImgSession(study_id,
                                         project,
                                         subject,
                                         xnat_id,
                                         scan_date,
                                         data_status,
                                         priority=LOW)
                    db.session.add(session)  # pylint: disable=no-member
                    # Add scans to session
                    for scan_id, scan_type in scan_ids:
                        try:
                            scan_type = ScanType.query.filter_by(
                                name=scan_type).one()
                        except orm.exc.NoResultFound:
                            scan_type = ScanType(scan_type)
                            db.session.add(scan_type)  # noqa pylint: disable=no-member
                        db.session.add(Scan(scan_id, session, scan_type))  # noqa pylint: disable=no-member
                    # Add dummy reports if existing report was stored in FM
                    if row['MrReport'] is not None and row['MrReport'].strip():
                        if 'MSH' in row['MrReport']:
                            reporter = axis
                        else:
                            reporter = nick_ferris
                        db.session.add(Report(  # noqa pylint: disable=no-member
                            session.id, reporter.id, '', NOT_RECORDED,
                            [], MRI, date=scan_date, dummy=True))
                    if (row['PetReport'] is not None and
                            row['PetReport'].strip()):
                        db.session.add(Report(  # noqa pylint: disable=no-member
                            session.id, paul_beech.id, '', NOT_RECORDED,
                            [], PET, date=scan_date, dummy=True))  # noqa pylint: disable=no-member
                    db.session.commit()  # pylint: disable=no-member
                    imported.append(study_id)
                else:
                    previous.append(study_id)


if __name__ == '__main__':
    ACTIONS = ['init', 'import']
    parser = ArgumentParser("Perform actions on the Flask app database")
    parser.add_argument('action', help="The action to perform", type=str,
                        choices=ACTIONS)
    args = parser.parse_args(sys.argv[1:2])

    if args.action == 'init':
        init_parser = ArgumentParser("Initialise the database")
        init_parser.add_argument('--password', '-p', default=None,
                                 help="The password for the admin account")
        init_args = init_parser.parse_args(sys.argv[2:])
        if init_args.password is None:
            password = getpass.getpass(
                "Please enter password for admin account "
                "('manager.mbi@monash.edu'): ")
        else:
            password = init_args.password

        try:
            db_path = init(password)
        except DatabaseAlreadyInitialisedError:
            print("Database already initialised")
        else:
            print("Successfully initialised database at {}"
                  .format(db_path))
    elif args.action == 'import':
        import_parser = ArgumentParser("Initialise the database")
        import_parser.add_argument('export_file',
                                   help="The exported file from filemaker")
        import_args = import_parser.parse_args(sys.argv[2:])

        initial_import(import_args.export_file)
    else:
        print("Unrecognised action '{}' can be one of {}".format(args.action,
                                                                 ACTIONS))
