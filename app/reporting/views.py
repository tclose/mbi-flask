from flask import (
    Blueprint, request, render_template, flash, g, session,
    redirect, url_for)
from werkzeug import check_password_hash, generate_password_hash  # noqa pylint: disable=no-name-in-module
from app import db
from app.reporting.forms import RegisterForm, LoginForm
from app.reporting.models import Session, Reporter
from app.reporting.decorators import requires_login

mod = Blueprint('reporting', __name__, url_prefix='/reporting')


@mod.before_request
def before_request():
    """
    pull user's profile from the database before every request are treated
    """
    g.user = None
    if 'user_id' in session:
        g.user = Reporter.query.get(session['user_id'])


@mod.route('/login/', methods=['GET', 'POST'])
def login():
    """
    Login form
    """
    form = LoginForm(request.form)
    # make sure data are valid, but doesn't validate password is right
    if form.validate_on_submit():
        reporter = Reporter.query.filter_by(email=form.email.data).first()
        # we use werzeug to validate user's password
        if reporter and check_password_hash(reporter.password,
                                            form.password.data):
            # the session can't be modified as it's signed,
            # it's a safe place to store the user id
            session['reporter_id'] = reporter.id
            flash('Welcome %s' % reporter.name)
            return redirect(url_for('reporting.home'))
        flash('Wrong email or password', 'error-message')
    return render_template("reporting/login.html", form=form)


@mod.route('/register/', methods=['GET', 'POST'])
def register():
    """
    Registration Form
    """
    form = RegisterForm(request.form)
    if form.validate_on_submit():
        # create an user instance not yet stored in the database
        reporter = Reporter(
            name=form.name.data, email=form.email.data,
            password=generate_password_hash(form.password.data))
        # Insert the record in our database and commit it
        db.session.add(reporter)  # pylint: disable=no-member
        db.session.commit()  # pylint: disable=no-member

        # Log the user in, as he now has an id
        session['reporter_id'] = reporter.id

        # flash will display a message to the user
        flash('Thanks for registering')
        # redirect user to the 'home' method of the user module.
        return redirect(url_for('reporting.home'))
    return render_template("reporting/register.html", form=form)
