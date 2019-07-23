from flask_wtf import Form
from wtforms import (
    StringField, PasswordField, BooleanField, SelectMultipleField, widgets,
    SelectField, HiddenField, TextAreaField)
from wtforms.validators import DataRequired
from wtforms.validators import Required, EqualTo, Email
from .constants import CONCLUSION


class DivWidget(object):
    """
    Renders a list of fields in separate <div> blocks
    """

    def __init__(self, html_tag='ul', prefix_label=True):
        assert html_tag in ('ol', 'ul')
        self.html_tag = html_tag
        self.prefix_label = prefix_label

    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)
        html = ['<div {}>'.format(widgets.html_params(**kwargs))]
        for subfield in field:
            html.append(
                '<div class="inline-field">{} {}</div>'.format(subfield(),
                                                               subfield.label))
        html.append('</div>')
        return widgets.HTMLString(''.join(html))


class MultiCheckboxField(SelectMultipleField):
    """
    A multiple-select, except displays a list of checkboxes.

    Iterating the field will produce subfields, allowing custom rendering of
    the enclosed checkbox fields.
    """
    widget = DivWidget()
    option_widget = widgets.CheckboxInput()


class LoginForm(Form):
    email = StringField('Email address', [Required(), Email()])
    password = PasswordField('Password', [Required()])


class RegisterForm(Form):
    name = StringField(
        'Full name & title (e.g. Dr Jane E. Doe)',
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
    selected_only = HiddenField('selected_only', default=False)
