from flask_wtf import Form, RecaptchaField
from wtforms import (
    TextField, PasswordField, BooleanField, SelectMultipleField, widgets)
from wtforms.validators import Required, EqualTo, Email


class LoginForm(Form):
    email = TextField('Email address', [Required(), Email()])
    password = PasswordField('Password', [Required()])


class RegisterForm(Form):
    name = TextField(
        'Full name and title to appear on reports (e.g. Dr Jane E. Doe)',
        [Required()])
    suffixes = TextField('Suffixes (e.g. MBBS FRANZCR)', [Required()])
    email = TextField('Email address', [Required(), Email()])
    password = PasswordField('Password', [Required()])
    confirm = PasswordField('Repeat password', [
        Required(),
        EqualTo('password', message='Passwords must match')
        ])


class ReportForm(Form):

    findings = TextField('Findings', [])
    conclusion = TextField('Conclusion', [])
