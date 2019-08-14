import re
from datetime import datetime
from flask import (
    request, render_template, flash, g, session, redirect, url_for)
from flask_mail import Message
# from sqlalchemy import sql, orm
from sqlalchemy.exc import IntegrityError
from werkzeug import (  # noqa pylint: disable=no-name-in-module
    check_password_hash, generate_password_hash,
    secure_filename)
from app import db, templates_dir, static_dir, app, signature_images, mail
from .forms import RegisterForm, LoginForm
from .models import User, Role
from .decorators import requires_login


@app.before_request
def before_request():
    """
    pull user's profile from the database before every request are treated
    """
    g.user = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user is None:
            g.user = None
            session.pop('time_of_last_activity', None)
            return
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


@app.route('/login/', methods=['GET', 'POST'])
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
    return render_template("login.html", form=form)


@app.route('/logout/', methods=['GET', 'POST'])
def logout():
    """
    Logout page
    """
    if g.user is not None:
        user = g.user
        g.user = None
        flash('Logged out {}'.format(user.name), 'info')
    session.pop('user_id', None)
    return redirect(url_for('login'))


@app.route('/register/', methods=['GET', 'POST'])
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
            title=form.title.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            middle_name=form.last_name.data,
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
            return redirect(url_for('login'))
    return render_template("register.html", form=form)
