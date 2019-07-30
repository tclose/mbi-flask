from pprint import pprint
import os.path as op
import re
from datetime import timedelta, datetime
import csv
from tqdm import tqdm
from flask import (
    Blueprint, request, render_template, flash, g, session,
    redirect, url_for)
from flask_breadcrumbs import Breadcrumbs, register_breadcrumb
from flask_mail import Message
from sqlalchemy import sql, orm
from sqlalchemy.exc import IntegrityError
from werkzeug import (  # noqa pylint: disable=no-name-in-module
    check_password_hash, generate_password_hash,
    secure_filename)
import xnatutils
from app import db, templates_dir, static_dir, app, signature_images, mail
from .forms import RegisterForm, LoginForm, ReportForm
from .models import Subject, ImagingSession, User, Report, ScanType, Role
from .decorators import requires_login
from .constants import (
    REPORT_INTERVAL, LOW, IGNORE, NOT_RECORDED, MRI, PET,
    PATHOLOGIES, REPORTER_ROLE, ADMIN_ROLE,
    PRESENT, NOT_FOUND, UNIMELB_DARIS, INVALID_LABEL, NOT_REQUIRED)
from flask_breadcrumbs import register_breadcrumb, default_breadcrumb_root
from xnat.exceptions import XNATResponseError


mod = Blueprint('reporting', __name__, url_prefix='/reporting')
default_breadcrumb_root(mod, '.')


daris_id_re = re.compile(r'1008\.2\.(\d+)\.(\d+)(?:\.1\.(\d+))?.*')

clinical_res = [re.compile(s) for s in (
    r'(?!.*kspace.*).*(?<![a-zA-Z])(?i)(t1).*',
    r'(?!.*kspace.*).*(?<![a-zA-Z])(?i)(t2).*',
    r'(?!.*kspace.*).*(?i)(mprage).*',
    r'(?!.*kspace.*).*(?i)(qsm).*',
    r'(?!.*kspace.*).*(?i)(flair).*',
    r'(?!.*kspace.*).*(?i)(fl3d).*')]


@mod.before_request
def before_request():
    """
    pull user's profile from the database before every request are treated
    """
    g.user = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        logout_msg = None
        try:
            last_activity = session['time_of_last_activity']
        except (KeyError, ValueError):
            logout_msg = (
                "Could not read time of last activity, so logging out '{}'"
                .format(user.name))
        else:
            if datetime.now() > (last_activity +
                                 app.config['AUTO_LOGOUT_PERIOD']):
                logout_msg = ("'{}' has been logged out due to inactivity"
                              .format(user.name))
        if logout_msg is not None:
            session.pop('user_id', None)
            session.pop('time_of_last_activity', None)
            flash(logout_msg, "info")
        else:
            g.user = user
            session['time_of_last_activity'] = datetime.now()


@mod.route('/', methods=['GET'])
@register_breadcrumb(mod, '.', 'Home')
@requires_login()
def index():
    # This should be edited to be a single jumping off page instead of
    # redirects
    if g.user.has_role(REPORTER_ROLE):
        return redirect(url_for('reporting.sessions'))
    elif g.user.has_role(ADMIN_ROLE):
        return redirect(url_for('reporting.admin'))
    else:
        raise Exception(
            "Unrecognised role for user {} ({})".format(
                g.user, (str(r) for r in g.user.roles)))


@mod.route('/login/', methods=['GET', 'POST'])
def login():
    """
    Login form
    """
    if g.user is not None and g.user.active:
        return redirect(url_for('reporting.index'))
    form = LoginForm(request.form)
    # make sure data are valid, but doesn't validate password is right
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        # we use werzeug to validate user's password
        if user and check_password_hash(user.password, form.password.data):
            # the session can't be modified as it's signed,
            # it's a safe place to store the user id
            session['user_id'] = user.id
            session['time_of_last_activity'] = datetime.now()
            flash('Welcome {}'.format(user.name), 'success')
            return redirect(url_for('reporting.index'))
        flash('Wrong email or password', 'error')
    return render_template("reporting/login.html", form=form)


@mod.route('/logout/', methods=['GET', 'POST'])
def logout():
    """
    Logout page
    """
    if g.user is not None:
        user = g.user
        g.user = None
        flash('Logged out {}'.format(user.name), 'info')
    session.pop('user_id', None)
    return redirect(url_for('reporting.login'))


@mod.route('/register/', methods=['GET', 'POST'])
def register():
    """
    Registration Form
    """
    form = RegisterForm()
    if form.validate_on_submit():
        # Save signature file
        if form.signature.data is not None:
            signature_fname = signature_images.save(form.signature.data,
                                                    name=form.email.data + '.')
        else:
            signature_fname = None
        # create an user instance not yet stored in the database
        user = User(
            name=form.name.data,
            suffixes=form.suffixes.data,
            email=form.email.data,
            password=generate_password_hash(form.password.data),
            signature=signature_fname,
            roles=[Role.query.get(form.role.data)],
            active=app.config['TEST'])
        # Insert the record in our database and commit it
        db.session.add(user)  # pylint: disable=no-member
        try:
            db.session.commit()  # pylint: disable=no-member
        except IntegrityError as e:
            clash_field = re.match(
                r'.*UNIQUE constraint failed: reporting_user.(.*)',
                e.args[0]).group(1)
            if clash_field == 'email':
                msg = ("The email address '{}' has already been registered"
                       .format(form.email.data))
            elif clash_field == 'name':
                msg = ("The name '{}' has already been registered with the "
                       "email '{}'".format(form.name.data, form.email.data))
            else:
                raise Exception("Unrecognised clash_field, {}"
                                .format(clash_field))
            flash("{}. Please try logging in or contact {} to reset."
                  .format(msg, app.config['ADMIN_EMAIL']), 'error')
        else:
            # flash will display a message to the user
            msg = "Registration successful"
            if not user.active:
                msg += (", please wait to be activated. If urgent contact {}"
                        .format(app.config['ADMIN_EMAIL']))
            flash(msg, 'success')
            msg = Message("New reporting registration: {}"
                          .format(form.email.data),
                          recipients=[app.config['ADMIN_EMAIL']])
            msg.html = render_template('reporting/email/registration.html',
                                       email=form.email.data)
            mail.send(msg)
            return redirect(url_for('reporting.login'))
    return render_template("reporting/register.html", form=form)


@mod.route('/sessions', methods=['GET'])
@register_breadcrumb(mod, '.sessions', 'Sessions to report')
@requires_login(REPORTER_ROLE)
def sessions():
    """
    Display all sessions that still need to be reported.
    """

    # Create an alias of the ImagingSession model so we can search within its
    # table for more recent sessions and earlier sessions that have been
    # reported
    S = orm.aliased(ImagingSession)

    # Create query for sessions that still need to be reported
    to_report = (
        db.session.query(S)  # pylint: disable=no-member
        # Filter out "ignored" sessions that are to be reported by AXIS
        .filter(S.priority != IGNORE)
        # Filter out sessions of subjects that have a more recent session
        .filter(~(
            db.session.query(ImagingSession)  # pylint: disable=no-member
            .filter(
                ImagingSession.subject_id == S.subject_id,
                ImagingSession.scan_date > S.scan_date)
            .exists()))
        # Filter out sessions of subjects that have been reported on less than
        # the REPORT_INTERVAL (e.g. 365 days) beforehand
        .filter(~(
            db.session.query(ImagingSession)  # pylint: disable=no-member
            .join(Report)  # Only select sessions with a report
            .filter(
                ImagingSession.subject_id == S.subject_id,
                sql.func.abs(
                    sql.func.julianday(ImagingSession.scan_date) -
                    sql.func.julianday(S.scan_date)) <= REPORT_INTERVAL)
            .exists()))
        .order_by(S.priority.desc(),
                  S.scan_date))

    return render_template("reporting/sessions.html",
                           sessions=to_report)


@mod.route('/report', methods=['GET', 'POST'])
@register_breadcrumb(mod, '.sessions.report', 'Report submission')
@requires_login(REPORTER_ROLE)
def report():
    """
    Enter report
    """

    form = ReportForm(request.form)

    session_id = form.session_id.data

    # Retrieve session from database
    img_session = ImagingSession.query.filter_by(
        id=session_id).first()

    if img_session is None:
        raise Exception(
            "Session corresponding to ID {} was not found".format(
                session_id))

    # Dynamically set form fields
    form.scan_types.choices = [
        (t.id, t.name) for t in img_session.avail_scan_types]

    if form.selected_only.data != 'true':  # From sessions page
        if form.validate_on_submit():

            # create an report instance not yet stored in the database
            report = Report(
                session_id=session_id,
                reporter_id=g.user.id,
                findings=form.findings.data,
                conclusion=int(form.conclusion.data),
                used_scan_types=ScanType.query.filter(
                    ScanType.id.in_(form.scan_types.data)).all(),
                modality=MRI)

            # Insert the record in our database and commit it
            db.session.add(report)  # pylint: disable=no-member
            db.session.commit()  # pylint: disable=no-member

            # flash will display a message to the user
            flash('Report submitted for {}'.format(session_id), 'success')
            # redirect user to the 'home' method of the user module.
            return redirect(url_for('reporting.sessions'))
        else:
            flash("Some of the submitted values were invalid", "error")
    return render_template("reporting/report.html", session=img_session,
                           form=form, xnat_url=app.config['TARGET_XNAT_URL'],
                           PATHOLOGIES=[str(c) for c in PATHOLOGIES])


# @mod.route('/import', methods=['GET'])
# @requires_login(ADMIN_ROLE)
def import_():
    export_file = app.config['FILEMAKER_EXPORT_FILE']
    if not op.exists(export_file):
        raise Exception("Could not find an FileMaker export file at {}"
                        .format(export_file))
    num_imported = 0
    num_prev = 0
    skipped = []
    # Get previous reporters
    nick_ferris = User.query.filter_by(
        email='nicholas.ferris@monash.edu').one()
    paul_beech = User.query.filter_by(email='paul.beech@monash.edu').one()
    axis = User.query.filter_by(name='AXIS Reporting').one()
    with xnatutils.connect(server=app.config['SOURCE_XNAT_URL']) as mbi_xnat:
        with open(export_file) as f:
            rows = list(csv.DictReader(f))
            for row in tqdm(rows):
                data_status = PRESENT
                # Check to see if the project ID is one of the valid types
                project_id = row['ProjectID']
                if project_id is None or not project_id:
                    project_id = ''
                    data_status = INVALID_LABEL
                else:
                    project_id = project_id.strip()
                    if project_id[:3] not in ('MRH', 'MMH', 'CLF'):
                        print("skipping {} from {}".format(row['StudyID'],
                                                           project_id))
                        skipped.append(row)
                        continue
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
                        "Could not process date of birth of {} ({})"
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
                if ImagingSession.query.get(study_id) is None:
                    # Parse scan date
                    try:
                        scan_date = datetime.strptime(
                            row['ScanDate'].replace('.', '/'), '%d/%m/%Y')
                    except ValueError:
                        scan_date = datetime(1, 1, 1)
                        print("Could not read scan date for {}"
                              .format(study_id))
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
                    if project_id.startswith('MMH'):
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
                        (project_id, subject_id, visit_id)).upper()
                    # If the session hasn't been reported on check XNAT for
                    # matching session so we can export appropriate scans to
                    # the alfred
                    if all_reports_submitted:
                        data_status = NOT_REQUIRED
                        xnat_uri = ''
                        avail_scan_types = []
                    elif data_status not in (INVALID_LABEL, UNIMELB_DARIS):
                        try:
                            exp = mbi_xnat.experiments[xnat_id]  # noqa pylint: disable=no-member
                        except KeyError:
                            xnat_uri = ''
                            data_status = NOT_FOUND
                        else:
                            avail_scan_types = []
                            try:
                                for scan in exp.scans.values():
                                    try:
                                        scan_type = ScanType.query.filter_by(
                                            name=scan.type).one()
                                    except orm.exc.NoResultFound:
                                        scan_type = ScanType(
                                            scan.type,
                                            clinical=any(
                                                r.match(scan.type)
                                                for r in clinical_res))
                                        db.session.add(scan_type)  # noqa pylint: disable=no-member
                                    avail_scan_types.append(scan_type)
                            except XNATResponseError as e:
                                raise Exception(
                                    "Problem reading scans of {} ({}):\n{}"
                                    .format(study_id, xnat_id, str(e)))
                            xnat_uri = exp.uri.split('/')[-1]
                    else:
                        xnat_uri = ''
                        avail_scan_types = []
                    session = ImagingSession(study_id, subject,
                                             xnat_id,
                                             xnat_uri, scan_date,
                                             avail_scan_types,
                                             data_status,
                                             priority=LOW)
                    db.session.add(session)  # pylint: disable=no-member
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
                    num_imported += 1
                else:
                    num_prev += 1
    return {'num_imported': num_imported,
            'num_prev': num_prev,
            'skipped': skipped}
    # return render_template('reporting/import.html',
    #                        num_imported=num_imported, num_prev=num_prev,
    #                        malformed=malformed, no_xnat=no_xnat,
    #                        skipped=skipped)
