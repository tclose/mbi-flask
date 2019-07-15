import os.path as op
from flask import (
    Blueprint, request, render_template, flash, g, session,
    redirect, url_for)
from werkzeug import check_password_hash, generate_password_hash  # noqa pylint: disable=no-name-in-module
from mbi_flask import db, templates_dir, static_dir
from .forms import RegisterForm, LoginForm, ReportForm
from .models import ImagingSession, User, Report, ScanType
from .decorators import requires_login

mod = Blueprint('reporting', __name__, url_prefix='/reporting')


@mod.before_request
def before_request():
    """
    pull user's profile from the database before every request are treated
    """
    g.reporter = None
    if 'reporter_id' in session:
        g.reporter = User.query.get(session['reporter_id'])


@mod.route('/', methods=['GET'])
def index():
    """
    Display all sessions that still need to be reported
    """
    if g.reporter is None:
        return redirect(url_for('reporting.login'))
    else:
        return redirect(url_for('reporting.sessions'))


@mod.route('/login/', methods=['GET', 'POST'])
def login():
    """
    Login form
    """
    if g.reporter is not None:
        return redirect(url_for('reporting.sessions'))
    form = LoginForm(request.form)
    # make sure data are valid, but doesn't validate password is right
    if form.validate_on_submit():
        reporter = User.query.filter_by(email=form.email.data).first()
        # we use werzeug to validate user's password
        if reporter and check_password_hash(reporter.password,
                                            form.password.data):
            # the session can't be modified as it's signed,
            # it's a safe place to store the user id
            session['reporter_id'] = reporter.id
            flash('Welcome {}'.format(reporter.name), 'success')
            return redirect(url_for('reporting.sessions'))
        flash('Wrong email or password', 'error')
    return render_template("reporting/login.html", form=form)


@mod.route('/logout/', methods=['GET', 'POST'])
def logout():
    """
    Logout page
    """
    reporter = g.reporter
    g.reporter = None
    del session['reporter_id']
    flash('Logged out {}'.format(reporter.name), 'info')
    return redirect(url_for('reporting.login'))


@mod.route('/register/', methods=['GET', 'POST'])
def register():
    """
    Registration Form
    """
    form = RegisterForm(request.form)
    if form.validate_on_submit():
        # create an user instance not yet stored in the database
        reporter = User(
            name=form.name.data,
            suffixes=form.suffixes.data,
            email=form.email.data,
            password=generate_password_hash(form.password.data))
        # Insert the record in our database and commit it
        db.session.add(reporter)  # pylint: disable=no-member
        db.session.commit()  # pylint: disable=no-member

        # Log the user in, as he now has an id
        session['reporter_id'] = reporter.id

        # flash will display a message to the user
        flash('Thanks for registering', 'success')
        # redirect user to the 'home' method of the user module.
        return redirect(url_for('reporting.sessions'))
    return render_template("reporting/register.html", form=form)


@mod.route('/sessions', methods=['GET'])
@requires_login
def sessions():
    """
    Display all sessions that still need to be reported
    """
    unreported_sessions = (
        ImagingSession.query
        .order_by(ImagingSession.priority, ImagingSession.scan_date))  # noqa
    return render_template("reporting/sessions.html",
                           sessions=unreported_sessions)


@mod.route('/report', methods=['GET', 'POST'])
@requires_login
def report():
    """
    Enter report
    """

    form = ReportForm(request.form)

    # Retrieve scan types from XNAT
    avail_scan_types = ['t1_mprage_sag_p3_iso_1_ADNI',
                        't2_space_sag_p2_iso']

    form.scan_types.choices = list(enumerate(avail_scan_types))

    if 'session' in request.args:
        img_session_id = request.args['session']
    else:
        img_session_id = form.session_id.data

    # Retrieve session from database
    img_session = ImagingSession.query.filter_by(
        id=img_session_id).first()

    if form.validate_on_submit():

        # Retrieve scan types from XNAT
        scan_type_names = ['mprage', 'flair']
        scan_types = []

        for scan_type_name in scan_type_names:
            try:
                scan_type = ScanType.query.filter_by(
                    type=scan_type_name).first()
            except Exception as e:
                print(e)
                scan_type = ScanType(scan_type_name)
                db.session.add(scan_type)  # pylint: disable=no-member
            scan_types.append(scan_type)

        # create an report instance not yet stored in the database
        report = Report(
            session_id=img_session_id,
            reporter_id=form.reporter_id.data,
            findings=form.findings.data,
            conclusion=form.conclusion.data,
            scan_types=scan_types)

        # Insert the record in our database and commit it
        db.session.add(report)  # pylint: disable=no-member
        db.session.commit()  # pylint: disable=no-member

        # flash will display a message to the user
        flash('Report submitted for {}'.format(img_session_id), 'success')
        # redirect user to the 'home' method of the user module.
        return redirect(url_for('reporting.sessions'))
    return render_template("reporting/report.html", session=img_session,
                           form=form)


@mod.route('/import')
def import_():
    """
    Imports session information from FileMaker database export into in SQL lite
    DB
    """
