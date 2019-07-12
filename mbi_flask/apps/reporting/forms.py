from flask_wtf import Form, RecaptchaField
from wtforms import (
    TextField, PasswordField, BooleanField, SelectMultipleField, widgets)
from wtforms.validators import Required, EqualTo, Email


class MultiCheckboxField(SelectMultipleField):
    """
    A multiple-select, except displays a list of checkboxes.

    Iterating the field will produce subfields, allowing custom rendering of
    the enclosed checkbox fields.
    """
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()


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

    scan_types = MultiCheckboxField('Scans used', coerce=int)
    findings = TextField('Findings', [])
    conclusion = TextField('Conclusion', [])
