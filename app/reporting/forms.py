from flask_wtf import Form
from wtforms import (
    StringField, PasswordField, BooleanField, SelectMultipleField, widgets,
    SelectField, HiddenField, TextAreaField)
from wtforms.validators import DataRequired
from wtforms.validators import Required, EqualTo, Email
from .constants import CONCLUSION


class MultiCheckboxField(SelectMultipleField):
    """
    A multiple-select, except displays a list of checkboxes.

    Iterating the field will produce subfields, allowing custom rendering of
    the enclosed checkbox fields.
    """
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()


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

    findings = TextAreaField('Findings', [])
    conclusion = SelectField(
        'Conclusion',
        choices=[(None, '')] + [(str(i), s)
                                for i, (s, _) in CONCLUSION.items()])
    scan_types = MultiCheckboxField('Scans used', [DataRequired()],
                                    coerce=int)
    session_id = HiddenField('session_id')
