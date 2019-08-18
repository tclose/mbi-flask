import os.path as op
import os
import re
import json
import shutil
from datetime import datetime
from lxml import etree
from tqdm import tqdm
import glob
from flask import (
    Blueprint, request, render_template, flash, g, redirect, url_for, Markup)
from sqlalchemy import sql, orm
import xnat
from app import db, app
from .forms import ReportForm, RepairForm, CheckScanTypeForm
from ..views import get_user
from ..models import (
    Project, Subject, ImgSession, Report, Scan, ScanType, ContactInfo)
from ..decorators import requires_login
from ..utils import xnat_id_re
from ..constants import (
    MRI, PATHOLOGIES, REPORTER_ROLE, ADMIN_ROLE,
    DATA_STATUS, FIX_XNAT, PRESENT, NOT_FOUND, UNIMELB_DARIS,
    INVALID_LABEL, CRITICAL, NONURGENT, FIX_OPTIONS,
    FOUND_NO_CLINICAL, NOT_REQUIRED, LOW)
from flask_breadcrumbs import register_breadcrumb, default_breadcrumb_root


mod = Blueprint('reporting', __name__, url_prefix='/reporting')
default_breadcrumb_root(mod, '.reporting')

daris_id_re = re.compile(r'1008\.2\.(\d+)\.(\d+)(?:\.1\.(\d+))?.*')
FM = '{http://www.filemaker.com/fmpxmlresult}'


@mod.before_request
def before_request():
    get_user()


@mod.route('/', methods=['GET'])
@register_breadcrumb(mod, '.', 'Incidental Reporting')
@requires_login()
def index():
    # This should be edited to be a single jumping off page instead of
    # redirects
    return render_template("reporting/index.html",
                           is_reporter=g.user.has_role(REPORTER_ROLE),
                           is_admin=g.user.has_role(ADMIN_ROLE))


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
        # Only show sessions that have exported scans
        .filter(
            Scan.query
            .filter(Scan.session_id == ImgSession.id,
                    Scan.exported)
            .exists())
        # Don't show sessions that have unexported scans or scans of
        # unconfirmed clinicaly relevance
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
        (s.id, str(s)) for s in img_session.scans if s.exported]

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
            "Session corresponding to ID '{}' was not found".format(
                session_id))

    form.old_status.data = img_session.data_status

    if form.selected_only.data != 'true':  # From sessions page
        if form.validate_on_submit():

            old_xnat_id = img_session.xnat_id

            if form.status.data in (PRESENT, FIX_XNAT):
                project_id, xnat_subj_id, xnat_visit_id = xnat_id_re.match(
                    form.xnat_id.data).groups()
                try:
                    project = Project.query.filter_by(mbi_id=project_id).one()
                except orm.exc.NoResultFound:
                    with xnat.connect(
                        server=app.config['SOURCE_XNAT_URL'],
                        user=app.config['SOURCE_XNAT_USER'],
                        password=app.config['SOURCE_XNAT_PASSWORD']
                    ) as mbi_xnat:
                        title = mbi_xnat.projects[project_id].description
                    project = Project(project_id, title)
                    db.session.add(project)  # noqa pylint: disable=no-member
                img_session.project = project
                img_session.xnat_subject_id = xnat_subj_id
                img_session.xnat_visit_id = xnat_visit_id

            if form.status.data == PRESENT:
                img_session.check_data_status()
            else:
                img_session.data_status = form.status.data

            # Check to see whether the session is missing clinically relevant
            # scans
            edit_link = ('<a href="javascript:select_session({});">Edit</a>'
                         .format(session_id))

            # flash will display a message to the user
            if img_session.data_status == PRESENT:
                flash(Markup('Repaired {}. {}'.format(session_id, edit_link)),
                      'success')
            elif img_session.data_status == FOUND_NO_CLINICAL:
                flash(Markup((
                    "{} does not contain and clinically relevant scans."
                    " Status set to '{}', change to '{}' if this is "
                    "expected. {}").format(
                        img_session.xnat_id,
                        DATA_STATUS[FOUND_NO_CLINICAL][0],
                        DATA_STATUS[NOT_REQUIRED][0],
                        edit_link)), "warning")
            elif form.status.data != form.old_status.data:
                flash(Markup('Marked {} as "{}". {}'.format(
                    session_id, DATA_STATUS[form.status.data][0], edit_link)),
                      'info')
            elif form.xnat_id.data != old_xnat_id:
                flash(Markup((
                    'Updated XNAT ID of {} but didn\'t update status from '
                    '"{}. {}"').format(
                        session_id, DATA_STATUS[form.status.data][0],
                        edit_link)), 'warning')

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
         .update({ScanType.clinical: True,
                  ScanType.confirmed: True}, synchronize_session=False))
        # Update the scans aren't clinically relevant
        (ScanType.query  # pylint: disable=no-member
         .filter(ScanType.id.in_(viewed_scans))
         .filter(~ScanType.id.in_(clinical_scans))
         .update({ScanType.clinical: False,
                  ScanType.confirmed: True}, synchronize_session=False))

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


@mod.route('/sync-filemaker', methods=['GET'])
def sync_filemaker():
    project_data = parse_fm_export_file('project.xml')
    num_new_projects = 0
    for row in tqdm(project_data, "Syncing project data"):
        try:
            project = Project.query.filter_by(
                mbi_id=row['MBI Project Number']).one()
        except orm.exc.NoResultFound:
            db.session.add(Project(  # noqa pylint: disable=no-member
                mbi_id=row['MBI Project Number'],
                title=row['Running Title']))
            num_new_projects += 1
        else:
            project.title = row['Running Title']
    db.session.commit()  # pylint: disable=no-member
    app.logger.info("Imported {} projects ({} new)".format(  # noqa pylint: disable=no-member
        len(project_data), num_new_projects))
    subject_data = parse_fm_export_file('subject.xml')
    num_new_subjects = 0
    for row in tqdm(subject_data, "Syncing subject data"):
        dob = (datetime.strptime(
            row['Date of Birth'].replace('.', '/').replace('/00', '/0'),
            '%d/%m/%Y') if row['Date of Birth'] is not None else None)
        try:
            subject = Subject.query.filter_by(
                mbi_id=row['MBI Subject ID']).one()
        except orm.exc.NoResultFound:
            db.session.add(Subject(  # noqa pylint: disable=no-member
                mbi_id=row['MBI Subject ID'],
                first_name=row['First Name'],
                last_name=row['Last Name'],
                middle_name=row['Middle Name'],
                gender=row['Gender'],
                dob=dob,
                animal_id=row['Animal ID']))
            num_new_subjects += 1
        else:
            subject.mbi_id = row['MBI Subject ID']
            subject.first_name = row['First Name']
            subject.last_name = row['Last Name']
            subject.middle_name = row['Middle Name']
            subject.gender = row['Gender']
            subject.dob = dob
            subject.animal_id = row['Animal ID']
    db.session.commit()  # pylint: disable=no-member
    app.logger.info("Imported {} subjects ({} new)".format(  # noqa pylint: disable=no-member
        len(subject_data), num_new_subjects))
    contact_info_data = parse_fm_export_file('contact.xml')
    num_new_contact_infos = 0
    for row in tqdm(contact_info_data, "Syncing contact info"):
        date = (
            datetime.strptime(
                row['Subject_Details::Date'].replace('.', '/'), '%d/%m/%Y')
            if row['Subject_Details::Date'] is not None else None)
        try:
            subject = Subject.query.filter_by(
                mbi_id=row['Subjects::MBI Subject ID']).one()
        except orm.exc.NoResultFound:
            app.logger.info(  # pylint: disable=no-member
                "Skipping row in ContactInfo with no subject ID: {}"
                .format(row))
            continue
        try:
            contact_info = ContactInfo.query.filter_by(date=date,
                                                       subject_id=subject.id)
        except orm.exc.NoResultFound:
            db.session.add(ContactInfo(  # noqa pylint: disable=no-member
                date=date,
                subject=subject,
                street=row['Subject_Details::Address Street'],
                suburb=row['Subject_Details::Address Suburb'],
                postcode=row['Subject_Details::Address Postcode'],
                country=row['Subject_Details::Others'],
                mobile_phone=row['Subject_Details::Mobile Phone'],
                work_phone=row['Subject_Details::Work Phone']))
            num_new_contact_infos += 1
        else:
            contact_info.street = row['Subject_Details::Address Street']
            contact_info.suburb = row['Subject_Details::Address Suburb']
            contact_info.postcode = row['Subject_Details::Address Postcode']
            contact_info.country = row['Subject_Details::Others']
            contact_info.mobile_phone = row['Subject_Details::Mobile Phone']
            contact_info.work_phone = row['Subject_Details::Work Phone']
    db.session.commit()  # pylint: disable=no-member
    app.logger.info("Imported {} contact-info ({} new)".format(  # noqa pylint: disable=no-member
        len(contact_info_data), num_new_contact_infos))
    contact_info_data = parse_fm_export_file('contact.xml')
    img_session_data = parse_fm_export_file('session.xml')
    num_new_sessions = 0
    for row in tqdm(img_session_data, "Syncing imaging sessions"):
        try:
            project = Project.query.filter_by(
                mbi_id=row['MBI Project ID']).one()
            subject = Subject.query.filter_by(
                mbi_id=row['MBI Subject ID']).one()
        except orm.exc.NoResultFound:
            app.logger.info(  # pylint: disable=no-member
                "Skipping row in ImgSession with no subject and/or project "
                "ID: {}".format(row))
            continue
        scan_date = row['Date Scanned']
        if scan_date is not None:
            scan_date = datetime.strptime(
                scan_date.replace('.', '/'), '%d/%m/%Y')
        daris_code = row['DaRIS code']
        data_status = PRESENT
        if daris_code:
            match = daris_id_re.match(daris_code)
            if match is not None:
                _, xnat_subject_id, xnat_visit_id = match.groups()
                if xnat_visit_id is None:
                    xnat_visit_id = '1'
            else:
                xnat_subject_id = xnat_visit_id = ''
                if daris_code.startswith('1.5.'):
                    data_status = UNIMELB_DARIS
                else:
                    data_status = INVALID_LABEL
        else:
            try:
                xnat_subject_id = row['Study Specific Subject Number']
            except (KeyError, AttributeError):
                xnat_subject_id = None
            try:
                xnat_visit_id = row['Session ID']
            except (KeyError, AttributeError):
                xnat_visit_id = None
            if None in (xnat_subject_id, xnat_visit_id):
                data_status = INVALID_LABEL
        if project.mbi_id.startswith('MMH'):
            visit_prefix = 'MRPT'
        else:
            visit_prefix = 'MR'
        # Get the visit part of the XNAT ID
        try:
            numeral, suffix = re.match(r'(\d+)(.*)', xnat_visit_id).groups()
            xnat_visit_id = '{}{:02}{}'.format(
                visit_prefix, int(numeral),
                (suffix if suffix is not None else ''))
        except (ValueError, TypeError, AttributeError):
            data_status = INVALID_LABEL
        height = row['Height']
        if height is not None:
            if height.endswith('cm'):
                height = height[:-2]
            if "'" in height:
                feet, inches = height.split("'")[:2]
                height = ((float(feet) * 12) + float(inches)) * 2.54
            height = float(height)
            if height < 3.0:
                height *= 100.0  # Convert metres into centremetres
        try:
            img_session = ImgSession.query.filter_by(
                id=row['STUDY ID']).one()
        except orm.exc.NoResultFound:
            img_session = ImgSession(  # noqa pylint: disable=no-member
                id=row['STUDY ID'],
                subject=subject,
                project=project,
                xnat_subject_id=xnat_subject_id,
                xnat_visit_id=xnat_visit_id,
                daris_code=daris_code,
                scan_date=scan_date,
                priority=LOW,
                data_status=data_status,
                height=height,
                weight=row['Weight'],
                notes=row['Radiographer Notes'])
            db.session.add(img_session)  # pylint: disable=no-member
            img_session.check_data_status()
            num_new_sessions += 1
        else:
            recheck_status = (
                xnat_subject_id != img_session.xnat_subject_id or
                xnat_visit_id != img_session.xnat_visit_id)
            img_session.subject = subject
            img_session.project = project
            img_session.id = row['STUDY ID']
            img_session.subject = subject
            img_session.project = project
            img_session.xnat_subject_id = xnat_subject_id
            img_session.xnat_visit_id = xnat_visit_id
            img_session.daris_code = daris_code
            img_session.scan_date = scan_date
            img_session.priority = LOW
            img_session.data_status = data_status
            img_session.height = height
            img_session.weight = row['Weight']
            img_session.notes = row['Radiographer Notes']
            if recheck_status:
                img_session.check_data_status()
    app.logger.info("Imported {} sessions ({} new)".format(  # noqa pylint: disable=no-member
        len(img_session_data), num_new_sessions))
    db.session.commit()  # pylint: disable=no-member
    return 200, {}


def parse_fm_export_file(fname):
    with open(op.join(app.config['FILEMAKER_EXPORT_DIR'], fname)) as f:
        tree = etree.parse(f).getroot()
    fields = [e.attrib['NAME'] for e in tree.findall(
        FM + 'METADATA')[0].findall(FM + 'FIELD')]
    data = []
    for row in tree.findall(FM + 'RESULTSET')[0].findall(FM + 'ROW'):
        row_data = [e.find(FM + 'DATA') for e in row.findall(FM + 'COL')]
        row_data = [(d.text.strip() if (d is not None and d.text is not None)
                     else None) for d in row_data]
        data.append(dict(zip(fields, row_data)))
    return data


@mod.route('/sync-alfred', methods=['GET'])
def sync_alfred():

    tmp_download_dir = app.config['TEMP_DOWNLOAD_DIR']

    os.makedirs(tmp_download_dir, exist_ok=True)

    exported = set()
    with xnat.connect(server=app.config['SOURCE_XNAT_URL'],
                      user=app.config['SOURCE_XNAT_USER'],
                      password=app.config['SOURCE_XNAT_PASSWORD']) as mbi_xnat:
        with xnat.connect(server=app.config['TARGET_XNAT_URL'],
                          user=app.config['TARGET_XNAT_USER'],
                          password=app.config[
                              'TARGET_XNAT_PASSWORD']) as alf_xnat:
            alf_project = alf_xnat.projects[app.config['TARGET_XNAT_PROJECT']]  # noqa pylint: disable=no-member
            for img_session in ImgSession.ready_for_export():
                mbi_session = mbi_xnat.experiments[img_session.xnat_id]  # noqa pylint: disable=no-member
                try:
                    alf_subject = alf_project.subjects[
                        img_session.subject.mbi_id]
                except KeyError:
                    alf_subject = alf_xnat.classes.SubjectData(  # noqa pylint: disable=no-member
                        label=img_session.subject.mbi_id, parent=alf_project)
                alf_session = alf_xnat.classes.MrSessionData(  # noqa pylint: disable=no-member
                    label=img_session.id, parent=alf_subject)
                prev_exported = list(alf_session.scans.keys())
                # Loop through clinically relevant scans that haven't been
                # exported and export
                for scan in img_session.scans:
                    if scan.is_clinical:
                        if str(scan.xnat_id) not in prev_exported:
                            mbi_scan = mbi_session.scans[str(scan.xnat_id)]
                            tmp_dir = op.join(tmp_download_dir,
                                              str(img_session.id))
                            mbi_scan.download_dir(tmp_dir)
                            alf_scan = alf_xnat.classes.MrScanData(  # noqa pylint: disable=no-member
                                id=mbi_scan.id, type=mbi_scan.type,
                                parent=alf_session)
                            resource = alf_scan.create_resource('DICOM')
                            files_dir = glob.glob(op.join(
                                tmp_dir, '*', 'scans', '*', 'resources',
                                'DICOM', 'files'))[0]
                            for fname in os.listdir(files_dir):
                                resource.upload(op.join(files_dir, fname),
                                                fname)
                            mbi_checksums = _get_checksums(mbi_xnat, mbi_scan)
                            alf_checksums = _get_checksums(alf_xnat, alf_scan)
                            if (mbi_checksums != alf_checksums):
                                raise Exception(
                                    "Checksums do not match for uploaded scan "
                                    "{} from {} (to {}) XNAT session".format(
                                        mbi_scan.type, mbi_session.label,
                                        alf_session.label))
                            shutil.rmtree(tmp_dir)
                            exported.add(img_session)
                        scan.exported = True
                        db.session.commit()  # pylint: disable=no-member
                # Trigger DICOM information extraction
                if not app.config.get('TEST', False):
                    alf_xnat.put('/data/experiments/' + alf_session.id +  # noqa pylint: disable=no-member
                                '?pullDataFromHeaders=true')
                db.session.commit()  # pylint: disable=no-member
    flash("Successfully sync'd {} sessions with the Alfred XNAT"
          .format(len(exported)), "success")
    return redirect(url_for('reporting.index'))


def _get_checksums(login, scan):
    files_json = login.get_json(scan.uri + '/files')['ResultSet']['Result']
    return {r['Name']: r['digest'] for r in files_json
            if r['Name'].endswith('.dcm')}
