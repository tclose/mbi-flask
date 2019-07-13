from flask_wtf import Form
from wtforms import (
    StringField, PasswordField, BooleanField, SelectMultipleField, widgets,
    SelectField)
from wtforms.validators import Required, EqualTo, Email
from .constants import CONCLUSION


class LoginForm(Form):
    email = StringField('Email address', [Required(), Email()])
    password = PasswordField('Password', [Required()])


class RegisterForm(Form):
    name = StringField(
        'Full name and title to appear on reports (e.g. Dr Jane E. Doe)',
        [Required()])
    suffixes = StringField('Suffixes (e.g. MBBS FRANZCR)', [Required()])
    email = StringField('Email address', [Required(), Email()])
    password = PasswordField('Password', [Required()])
    confirm = PasswordField('Repeat password', [
        Required(),
        EqualTo('password', message='Passwords must match')
        ])


class ReportForm(Form):

    findings = StringField('Findings', [])
    conclusion = SelectField(
        'Conclusion', choices=[(i, s) for i, (s, _) in CONCLUSION.items()])
