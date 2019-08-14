from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, RadioField)
from flask_wtf.file import FileField, FileAllowed
from wtforms.validators import (
    ValidationError, Required, EqualTo, Email)
from .constants import ADMIN_ROLE, REPORTER_ROLE
from app import signature_images


class LoginForm(FlaskForm):
    email = StringField('Email address', [Required(), Email()])
    password = PasswordField('Password', [Required()])


class RegisterForm(FlaskForm):
    title = StringField('Title (e.g. Dr.)')
    first_name = StringField('First name', [Required()])
    last_name = StringField('Last name', [Required()])
    middle_name = StringField('Middle name or initial (optional)')
    suffixes = StringField('Suffixes (e.g. MBBS FRANZCR)')
    email = StringField('Email address', [Required(), Email()])
    password = PasswordField('Password', [Required()])
    confirm = PasswordField('Repeat password', [
        Required(), EqualTo('password', message='Passwords must match')])
    role = RadioField('Requested role', [Required()], coerce=int,
                      choices=[(REPORTER_ROLE, 'Reporter'),
                               (ADMIN_ROLE, 'Administrator')])
    signature = FileField(
        "Electronic signature image (Reporters only)",
        validators=[FileAllowed(signature_images,
                                'JPEG, PNG and GIF images only')])

    def validate_signature(self, field):
        if self.role.data == REPORTER_ROLE and field.data is None:
            raise ValidationError("An electronic signature must be provided "
                                  "for reporter accounts")

    def validate_title(self, field):
        if self.role.data == REPORTER_ROLE and field.data is None:
            raise ValidationError("A title is required for reporter users")

    def validate_suffixes(self, field):
        if self.role.data == REPORTER_ROLE and field.data is None:
            raise ValidationError("Suffixes are required for reporter users")
