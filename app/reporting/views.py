from pprint import pprint
import os.path as op
import os
import re
import json
import glob
from datetime import timedelta, datetime
import csv
from tqdm import tqdm
from flask import (
    Blueprint, request, render_template, flash, g, session,
    redirect, url_for, Markup)
from flask_breadcrumbs import Breadcrumbs, register_breadcrumb
from flask_mail import Message
from sqlalchemy import sql, orm
from sqlalchemy.exc import IntegrityError
from werkzeug import (  # noqa pylint: disable=no-name-in-module
    check_password_hash, generate_password_hash,
    secure_filename)
from xnatutils import connect as xnat_connect
from app import db, templates_dir, static_dir, app, signature_images, mail
from .forms import (
    RegisterForm, LoginForm, ReportForm, RepairForm, CheckScanTypeForm)
from ..models import (
    Project, Subject, ImgSession, User, Report, Role, Scan, ScanType)
from .decorators import requires_login
from ..constants import (
    LOW, NOT_RECORDED, MRI, PET, PATHOLOGIES, REPORTER_ROLE, ADMIN_ROLE,
    DATA_STATUS, FIX_XNAT, PRESENT, NOT_FOUND, UNIMELB_DARIS,
    INVALID_LABEL, NOT_CHECKED, CRITICAL, NONURGENT, FIX_OPTIONS,
    FOUND_NO_CLINICAL, NOT_REQUIRED)
from flask_breadcrumbs import register_breadcrumb, default_breadcrumb_root
from xnat.exceptions import XNATResponseError


mod = Blueprint('reporting', __name__, url_prefix='/reporting')
default_breadcrumb_root(mod, '.')


daris_id_re = re.compile(r'1008\.2\.(\d+)\.(\d+)(?:\.1\.(\d+))?.*')


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
@register_breadcrumb(mod, '.', 'Incidental Reporting')
@requires_login()
def index():
    # This should be edited to be a single jumping off page instead of
    # redirects
    return render_template("reporting/index.html",
                           is_reporter=g.user.has_role(REPORTER_ROLE),
                           is_admin=g.user.has_role(ADMIN_ROLE))


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

    # Create query for sessions that still need to be reported
    to_report = (
        ImgSession.require_report()
        .filter_by(data_status=PRESENT)
        .filter(
            Scan.query
            .filter(Scan.session_id == ImgSession.id,
                    Scan.exported)
            .exists())
        .filter(~(
            Scan.query
            .join(ScanType)
            .filter(
                Scan.session_id == ImgSession.id,
                sql.or_(~ScanType.confirmed, sql.and_(ScanType.clinical,
                                                      ~Scan.exported)))
            .exists()))
        .order_by(ImgSession.priority.desc(), ImgSession.scan_date)).all()

    if not to_report:
        flash("There are no more sessions to report!", "success")
        return redirect(url_for('reporting.index'))

    return render_template("reporting/sessions.html",
                           page_title="Sessions to Report",
                           sessions=to_report,
                           form_target=url_for('reporting.report'),
                           number_of_rows=len(to_report),
                           include_priority=True)


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
    img_session = ImgSession.query.filter_by(
        id=session_id).first()

    if img_session is None:
        raise Exception(
            "Session corresponding to ID {} was not found".format(
                session_id))

    # Dynamically set form fields
    form.scans.choices = [
        (s.id, s.type_.name) for s in img_session.scans if s.exported]

    if form.selected_only.data != 'true':  # From sessions page
        if form.validate_on_submit():

            # create an report instance not yet stored in the database
            report = Report(
                session_id=session_id,
                reporter_id=g.user.id,
                findings=form.findings.data,
                conclusion=int(form.conclusion.data),
                used_scans=Scan.query.filter(
                    Scan.id.in_(form.scans.data)).all(),
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
                           form=form, PATHOLOGIES=map(str, PATHOLOGIES),
                           CRITICAL=CRITICAL, NONURGENT=NONURGENT)


@mod.route('/fix-sessions', methods=['GET'])
@register_breadcrumb(mod, '.fix_sessions', 'Sessions to repair')
@requires_login(ADMIN_ROLE)
def fix_sessions():
    # Create query for sessions that need to be fixed
    to_fix = (
        ImgSession.require_report()
        .filter(ImgSession.data_status.in_((
            INVALID_LABEL, NOT_FOUND, UNIMELB_DARIS, FIX_XNAT,
            FOUND_NO_CLINICAL)))
        .order_by(ImgSession.data_status.desc(), ImgSession.scan_date)).all()

    new_missing_scans = (
        ImgSession.require_report()
        .filter_by(data_status=PRESENT)
        .filter(~(
            Scan.query
            .join(ScanType)
            .filter(
                Scan.session_id == ImgSession.id,
                sql.or_(~ScanType.confirmed, ScanType.clinical))
            .exists()))
        .order_by(ImgSession.data_status.desc(), ImgSession.scan_date)).all()

    # Update status of imports that don't have any clinical scans (and all
    # types have been confirmed)
    for img_session in new_missing_scans:
        img_session.data_status = FOUND_NO_CLINICAL

    db.session.commit()  # pylint: disable=no-member

    to_fix = new_missing_scans + to_fix

    if not to_fix:
        flash("There are no more sessions to repair!", "success")
        return redirect(url_for('reporting.index'))

    return render_template("reporting/sessions.html",
                           page_title="Sessions to Repair",
                           sessions=to_fix,
                           form_target=url_for('reporting.repair'),
                           include_status=True,
                           include_subject=True,
                           number_of_rows=len(to_fix),
                           DATA_STATUS=DATA_STATUS)


@mod.route('/repair', methods=['GET', 'POST'])
@register_breadcrumb(mod, '.fix_sessions.repair', 'Repair Session')
@requires_login(ADMIN_ROLE)
def repair():

    form = RepairForm(request.form)

    session_id = form.session_id.data

    # Retrieve session from database
    img_session = ImgSession.query.filter_by(
        id=session_id).first()

    if img_session is None:
        raise Exception(
            "Session corresponding to ID {} was not found".format(
                session_id))

    form.old_status.data = img_session.data_status

    if form.selected_only.data != 'true':  # From sessions page
        if form.validate_on_submit():

            old_xnat_id = img_session.xnat_id

            img_session.data_status = form.status.data
            if form.status.data in (PRESENT, FIX_XNAT):
                img_session.xnat_id = form.xnat_id.data

            # Check to see whether the session is missing clinically relevant
            # scans
            edit_link = ('<a href="javascript:select_session({});">Edit</a>'
                         .format(session_id))

            # flash will display a message to the user
            if img_session.data_status == PRESENT:
                # Add new scan types if required
                if hasattr(form, 'new_scan_types'):
                    # Delete existing scans linked to the session if present
                    (Scan.query
                     .filter_by(session_id=img_session.id)
                     .delete())

                    for scan_type in form.new_scan_types:
                        try:
                            scan_type = ScanType.query.filter_by(
                                name=scan_type).one()
                        except orm.exc.NoResultFound:
                            scan_type = ScanType(scan_type)
                            db.session.add(scan_type)  # noqa pylint: disable=no-member
                        try:
                            Scan.query.filter_by(session_id=img_session.id,
                                                 type_id=scan_type.id).one()
                        except orm.exc.NoResultFound:
                            db.session.add(Scan(img_session, scan_type))  # noqa pylint: disable=no-member

                    missing_scans = bool(
                        Scan.query
                        .join(ScanType)
                        .filter(
                            Scan.session_id == img_session.id,
                            sql.or_(ScanType.clinical,
                                    ~ScanType.confirmed)).count())
                else:
                    missing_scans = False

                if missing_scans:
                    img_session.data_status = FOUND_NO_CLINICAL
                    flash(("{} does not contain and clinically relevant scans."
                           " Status set to '{}', change to '{}' if this is "
                           "expected. {}").format(
                               img_session.xnat_id,
                               DATA_STATUS[FOUND_NO_CLINICAL][0],
                               DATA_STATUS[NOT_REQUIRED][0],
                               edit_link),
                          "warning")
                else:
                    flash(Markup('Repaired {}. {}'
                                 .format(session_id, edit_link)), 'success')
            elif form.status.data != form.old_status.data:
                flash(Markup('Marked {} as "{}". {}'.format(
                    session_id, DATA_STATUS[form.status.data][0], edit_link)),
                      'info')
            elif form.xnat_id.data != old_xnat_id:
                flash(('Updated XNAT ID of {} but didn\'t update status from '
                       '"{}. {}"').format(
                          session_id, DATA_STATUS[form.status.data][0],
                          edit_link),
                      'warning')

            db.session.commit()  # pylint: disable=no-member

            # redirect user to the 'home' method of the user module.
            return redirect(url_for('reporting.fix_sessions'))
        else:
            flash("Invalid inputs", "error")
    else:
        form.xnat_id.data = img_session.xnat_id
        form.status.data = img_session.data_status

    return render_template("reporting/repair.html", session=img_session,
                           form=form, PRESENT=PRESENT, FIX_XNAT=FIX_XNAT,
                           FIX_OPTIONS=FIX_OPTIONS,
                           xnat_url=app.config['SOURCE_XNAT_URL'],
                           xnat_project=form.xnat_id.data.split('_')[0],
                           DATA_STATUS=DATA_STATUS,
                           xnat_subject='_'.join(
                               form.xnat_id.data.split('_')[:2]))


@mod.route('/confirm-scan-types', methods=['GET', 'POST'])
@register_breadcrumb(mod, '.confirm_scan_types', 'Confirm Scan Types')
@requires_login(ADMIN_ROLE)
def confirm_scan_types():

    form = CheckScanTypeForm(request.form)
    # make sure data are valid, but doesn't validate password is right

    if form.is_submitted():
        viewed_scans = json.loads(form.viewed_scan_types.data)

        clinical_scans = form.clinical_scans.data

        # Update the scans are clinically relevant
        (ScanType.query  # pylint: disable=no-member
         .filter(ScanType.id.in_(clinical_scans))
         .update({ScanType.clinical: True}, synchronize_session=False))
        # Update the scans aren't clinically relevant
        (ScanType.query  # pylint: disable=no-member
         .filter(ScanType.id.in_(viewed_scans))
         .filter(~ScanType.id.in_(clinical_scans))
         .update({ScanType.clinical: False}, synchronize_session=False))
        # Mark all viewed scans as confirmed
        (ScanType.query
         .filter(ScanType.id.in_(viewed_scans))
         .update({ScanType.confirmed: True}, synchronize_session=False))

        db.session.commit()  # pylint: disable=no-member
        flash("Confirmed clinical relevance of {} scan types"
              .format(len(viewed_scans)), "success")

    num_unconfirmed = (
        ScanType.query
        .filter_by(confirmed=False)).count()

    scan_types_to_view = (
        ScanType.query
        .filter_by(confirmed=False)
        .order_by(ScanType.name)
        .limit(app.config['NUM_ROWS_PER_PAGE'])).all()

    if not scan_types_to_view:
        flash("All scan types have been reviewed!", "success")
        return redirect(url_for('reporting.index'))

    form.clinical_scans.choices = [
        (t.id, t.name) for t in scan_types_to_view]

    form.clinical_scans.render_kw = {
        'checked': [t.clinical for t in scan_types_to_view]}

    form.viewed_scan_types.data = json.dumps(
        [t.id for t in scan_types_to_view])

    return render_template("reporting/confirm_scan_types.html", form=form,
                           num_showing=(len(scan_types_to_view),
                                        num_unconfirmed))


@mod.route('/import', methods=['GET'])
def import_():
    export_file = app.config['FILEMAKER_EXPORT_FILE']
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
    axis = User.query.filter_by(name='AXIS Reporting').one()
    with xnat_connect(server=app.config['SOURCE_XNAT_URL']) as mbi_xnat:
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
                    scan_type_names = []
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
                                    scan_type_names.append(scan.type)
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
                    for st in scan_type_names:
                        try:
                            scan_type = ScanType.query.filter_by(name=st).one()
                        except orm.exc.NoResultFound:
                            scan_type = ScanType(st)
                            db.session.add(scan_type)  # noqa pylint: disable=no-member
                        db.session.add(Scan(session, scan_type))  # noqa pylint: disable=no-member
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
    return 200, {'imported': imported,
                 'previous': previous,
                 'skipped': skipped}


@mod.route('/export', methods=['GET'])
def export():

    tmp_download_dir = app.config['TEMP_DOWNLOAD_DIR']

    os.makedirs(tmp_download_dir, exist_ok=True)

    with xnat_connect(server=app.config['SOURCE_XNAT_URL']) as mbi_xnat:
        with xnat_connect(server=app.config['TARGET_XNAT_URL']) as alf_xnat:
            alf_project = alf_xnat.projects[app.config['TARGET_XNAT_PROJECT']]  # noqa pylint: disable=no-member
            for session in ImgSession.ready_for_export():
                mbi_session = mbi_xnat.experiments[session.xnat_id]  # noqa pylint: disable=no-member
                try:
                    alf_subject = alf_project.subjects[session.subject.mbi_id]
                except KeyError:
                    alf_subject = alf_xnat.classes.SubjectData(  # noqa pylint: disable=no-member
                        label=session.subject.mbi_id, parent=alf_project)
                alf_session = alf_xnat.classes.MrSessionData(  # noqa pylint: disable=no-member
                    label=session.id, parent=alf_subject)
                already_exported = [
                    s.type for s in alf_session.scans.values()]
                # Loop through clinically relevant scans that haven't been
                # exported and export
                for scan in session.scans:
                    if (scan.type_.clinical and
                            scan.type_.name not in already_exported):
                        mbi_scan = mbi_session.scans[scan.type_.name]
                        tmp_dir = op.join(tmp_download_dir, str(session.id))
                        mbi_scan.download_dir(tmp_dir)
                        alf_scan = alf_xnat.classes.MrScanData(  # noqa pylint: disable=no-member
                            id=mbi_scan.id, type=mbi_scan.type,
                            parent=alf_session)
                        resource = alf_scan.create_resource('DICOM')
                        for fname in os.listdir(glob.glob(op.join(
                            tmp_dir, '*', 'scans', '*', 'resources',
                                'DICOM', 'files'))[0]):
                            resource.upload(op.join(tmp_dir, fname), fname)
                        scan.exported = True
                        db.session.commit()  # pylint: disable=no-member
                # Trigger DICOM information extraction
                alf_xnat.put(alf_session.uri + '?pullDataFromHeaders=true')
