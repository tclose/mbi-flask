from flask_wtf import Form, RecaptchaField
from wtforms import TextField, PasswordField, BooleanField
from wtforms.validators import Required, EqualTo, Email


class LoginForm(Form):
    email = TextField('Email address', [Required(), Email()])
    password = PasswordField('Password', [Required()])


class RegisterForm(Form):
    name = TextField('Full Name and Title (e.g. Dr John Smith)', [Required()])
    suffixes = TextField('Suffixes (e.g. MBBS FRANZCR)', [Required()])
    email = TextField('Email address', [Required(), Email()])
    password = PasswordField('Password', [Required()])
    confirm = PasswordField('Repeat Password', [
        Required(),
        EqualTo('password', message='Passwords must match')
        ])


class ReportForm(Form):

    technique = TextField('Technique', [Required()])
    findings = TextField('Findings', [])
    conclusion = TextField('Conclusion', [])
    reported_by = TextField('Reported by', [Required()])
