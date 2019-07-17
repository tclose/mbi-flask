import os.path as op
from flask import (
    Blueprint, request, render_template, flash, g, session,
    redirect, url_for)
from flask_breadcrumbs import Breadcrumbs, register_breadcrumb
from sqlalchemy import sql
from werkzeug import check_password_hash, generate_password_hash  # noqa pylint: disable=no-name-in-module
from mbi_flask import db, templates_dir, static_dir
from .forms import RegisterForm, LoginForm, ReportForm
from .models import ImagingSession, User, Report, ScanType
from .decorators import requires_login
from flask_breadcrumbs import register_breadcrumb, default_breadcrumb_root

mod = Blueprint('reporting', __name__, url_prefix='/reporting')
default_breadcrumb_root(mod, '.')

@mod.before_request
def before_request():
    """
    pull user's profile from the database before every request are treated
    """
    g.user = None
    if 'user_id' in session:
        g.user = User.query.get(session['user_id'])


@mod.route('/', methods=['GET'])
@register_breadcrumb(mod, '.', 'Home')
@requires_login()
def index():
    # This should be edited to be a single jumping off page instead of
    # redirects
    if g.user.has_role('admin'):
        return redirect(url_for('reporting.admin'))
    elif g.user.has_role('reporter'):
        return redirect(url_for('reporting.sessions'))
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
            flash('Welcome {}'.format(user.name), 'success')
            return redirect(url_for('reporting.index'))
        flash('Wrong email or password', 'error')
    return render_template("reporting/login.html", form=form)


@mod.route('/logout/', methods=['GET', 'POST'])
def logout():
    """
    Logout page
    """
    user = g.user
    g.user = None
    del session['user_id']
    flash('Logged out {}'.format(user.name), 'info')
    return redirect(url_for('reporting.login'))


@mod.route('/register/', methods=['GET', 'POST'])
def register():
    """
    Registration Form
    """
    form = RegisterForm(request.form)
    if form.validate_on_submit():
        # create an user instance not yet stored in the database
        user = User(
            name=form.name.data,
            suffixes=form.suffixes.data,
            email=form.email.data,
            password=generate_password_hash(form.password.data))
        # Insert the record in our database and commit it
        db.session.add(user)  # pylint: disable=no-member
        db.session.commit()  # pylint: disable=no-member

        # Log the user in, as he now has an id
        session['user_id'] = user.id

        # flash will display a message to the user
        flash('Thanks for registering', 'success')
        # redirect user to the 'home' method of the user module.
        return redirect(url_for('reporting.sessions'))
    return render_template("reporting/register.html", form=form)


@mod.route('/sessions', methods=['GET'])
@register_breadcrumb(mod, '.sessions', 'Unreported Sessions')
@requires_login('reporter')
def sessions():
    """
    Display all sessions that still need to be reported
    """
    unreported_sessions = (
        ImagingSession.query
        .filter(~Report.query.filter_by(session_id=ImagingSession.id).exists())
        .order_by(ImagingSession.priority.desc(),
                  ImagingSession.scan_date))
    return render_template("reporting/sessions.html",
                           sessions=unreported_sessions)


@mod.route('/report', methods=['GET', 'POST'])
@register_breadcrumb(mod, '.sessions.report', 'Submit Report')
@requires_login('reporter')
def report():
    """
    Enter report
    """

    form = ReportForm(request.form)

    try:
        session_id = request.args['session_id']
    except KeyError:
        if form.is_submitted():
            session_id = form.session_id.data
        else:
            raise Exception("session_id was not provided in request url")

    # Retrieve session from database
    img_session = ImagingSession.query.filter_by(
        id=session_id).first()

    if img_session is None:
        raise Exception(
            "Session corresponding to ID {} was not found".format(
                session_id))

    # Dynamically set form fields
    form.session_id.data = session_id
    form.scan_types.choices = [
        (t.id, t.name) for t in img_session.avail_scan_types]

    if form.validate_on_submit():

        # create an report instance not yet stored in the database
        report = Report(
            session_id=session_id,
            reporter_id=g.user.id,
            findings=form.findings.data,
            conclusion=form.conclusion.data,
            used_scan_types=ScanType.query.filter(
                ScanType.id.in_(form.scan_types.data)).all())

        # Insert the record in our database and commit it
        db.session.add(report)  # pylint: disable=no-member
        db.session.commit()  # pylint: disable=no-member

        # flash will display a message to the user
        flash('Report submitted for {}'.format(session_id), 'success')
        # redirect user to the 'home' method of the user module.
        return redirect(url_for('reporting.sessions'))
    elif form.is_submitted():
        flash("Some of the submitted values were invalid", "error")
    return render_template("reporting/report.html", session=img_session,
                           form=form)
