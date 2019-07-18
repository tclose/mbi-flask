from datetime import datetime
from mbi_flask import db
from sqlalchemy.ext.declarative import declarative_base
from .constants import (
    SESSION_PRIORITY, REPORTER_STATUS, NEW, LOW)

Base = declarative_base()


class User(db.Model):
    """
    User of the application
    """

    __tablename__ = 'reporting_user'

    # Fields
    id = db.Column(db.Integer, primary_key=True)  # pylint: disable=no-member
    name = db.Column(db.String(50), unique=True)  # pylint: disable=no-member
    suffixes = db.Column(db.String(30), unique=True)  # noqa pylint: disable=no-member
    email = db.Column(db.String(120), unique=True)  # pylint: disable=no-member
    password = db.Column(db.String(120))  # pylint: disable=no-member
    active = db.Column(db.Boolean())  # noqa pylint: disable=no-member

    # Relationships
    reports = db.relationship('Report', back_populates='reporter')  # noqa pylint: disable=no-member
    roles = db.relationship('Role',  # noqa pylint: disable=no-member
                            secondary='reporting_user_role_assoc')

    def __init__(self, name, suffixes, email, password, roles=(),
                 active=False):
        self.name = name
        self.suffixes = suffixes
        self.email = email
        self.password = password
        self.roles = roles
        self.active = active

    @property
    def status_str(self):
        return REPORTER_STATUS[self.status]

    def __repr__(self):
        return '<User {}>'.format(self.name)

    def has_role(self, role):
        return role in [r.name for r in self.roles]


class Role(db.Model):
    """
    Valid user roles (e.g. 'admin' and 'reporter')
    """

    __tablename__ = 'reporting_role'

    # Fields
    id = db.Column(db.Integer, primary_key=True)  # pylint: disable=no-member
    name = db.Column(db.String(50), unique=True)  # pylint: disable=no-member

    def __init__(self, name):
        self.name = name


class Subject(db.Model):
    """
    Basic information about the subject of the imaging session. It is
    separated from the imaging session so that we can check for multiple
    in a year (or other arbitrary period) and only provide the latest one.
    """

    __tablename__ = 'reporting_subject'

    # Fields
    id = db.Column(db.Integer, primary_key=True)  # pylint: disable=no-member
    mbi_id = db.Column(db.String(10), unique=True)  # noqa pylint: disable=no-member
    dob = db.Column(db.Date())  # pylint: disable=no-member

    # Relationships
    sessions = db.relationship('ImagingSession', back_populates='subject')  # noqa pylint: disable=no-member

    def __init__(self, mbi_id, dob):
        self.mbi_id = mbi_id
        self.dob = dob

    def __repr__(self):
        return '<Subject {}>'.format(self.mbi_id)


class ImagingSession(db.Model):
    """
    Details of the imaging session to report on
    """

    __tablename__ = 'reporting_session'

    # Fields
    id = db.Column(db.Integer, primary_key=True)  # pylint: disable=no-member
    subject_id = db.Column(db.Integer, db.ForeignKey('reporting_subject.id'))  # noqa pylint: disable=no-member
    xnat_id = db.Column(db.String(50))  # noqa pylint: disable=no-member
    xnat_uri = db.Column(db.String(200))  # noqa pylint: disable=no-member
    scan_date = db.Column(db.Date())  # pylint: disable=no-member
    priority = db.Column(db.Integer)  # pylint: disable=no-member

    # Relationships
    subject = db.relationship('Subject', back_populates='sessions')  # noqa pylint: disable=no-member
    reports = db.relationship('Report', back_populates='session')  # noqa pylint: disable=no-member
    avail_scan_types = db.relationship(  # noqa pylint: disable=no-member
        'ScanType',  # noqa pylint: disable=no-member
        secondary='reporting_session_scantype_assoc')

    def __init__(self, id, subject_id, xnat_id, xnat_uri, scan_date,
                 avail_scan_types, priority=LOW):
        self.id = id
        self.subject_id = subject_id
        self.xnat_id = xnat_id
        self.xnat_uri = xnat_uri
        self.scan_date = scan_date
        self.avail_scan_types = avail_scan_types
        self.priority = priority

    def __repr__(self):
        return '<Session {}>'.format(self.xnat_id)

    @property
    def priority_str(self):
        return SESSION_PRIORITY[self.priority]


class Report(db.Model):
    """
    A report entered by a radiologist
    """

    __tablename__ = 'reporting_report'

    # Fields
    id = db.Column(db.Integer, primary_key=True)  # pylint: disable=no-member
    date = db.Column(db.Date())  # pylint: disable=no-member
    session_id = db.Column(db.Integer, db.ForeignKey('reporting_session.id'))  # noqa pylint: disable=no-member
    reporter_id = db.Column(db.Integer, db.ForeignKey('reporting_user.id'))  # noqa pylint: disable=no-member
    findings = db.Column(db.Text)  # pylint: disable=no-member
    conclusion = db.Column(db.Integer)  # pylint: disable=no-member
    exported = db.Column(db.Boolean)  # pylint: disable=no-member

    # Relationships
    session = db.relationship('ImagingSession', back_populates='reports')  # noqa pylint: disable=no-member
    reporter = db.relationship('User', back_populates='reports')  # noqa pylint: disable=no-member
    used_scan_types = db.relationship(  # noqa pylint: disable=no-member
        'ScanType',  # noqa pylint: disable=no-member
        secondary='reporting_report_scantype_assoc')

    def __init__(self, session_id, reporter_id, findings, conclusion,
                 used_scan_types, date=datetime.today()):
        self.session_id = session_id
        self.reporter_id = reporter_id
        self.findings = findings
        self.conclusion = conclusion
        self.used_scan_types = used_scan_types
        self.date = date


class ScanType(db.Model):
    """
    The type of (clinically relevant) scans in the session
    """

    __tablename__ = 'reporting_scantype'

    # Fields
    id = db.Column(db.Integer, primary_key=True)  # pylint: disable=no-member
    name = db.Column(db.String(150), unique=True)  # noqa pylint: disable=no-member
    alias = db.Column(db.Integer)  # pylint: disable=no-member

    def __init__(self, name, alias=None):
        self.name = name
        self.alias = alias

    def __repr__(self):
        return "<ScanType {}>".format(self.name)


# Many-to-many association tables

user_role_assoc_table = db.Table(  # pylint: disable=no-member
    'reporting_user_role_assoc', db.Model.metadata,  # noqa pylint: disable=no-member
    db.Column('id', db.Integer, primary_key=True),  # noqa pylint: disable=no-member
    db.Column('user_id', db.Integer, db.ForeignKey('reporting_user.id')),  # noqa pylint: disable=no-member
    db.Column('role_id', db.Integer, db.ForeignKey('reporting_role.id')))  # noqa pylint: disable=no-member


session_scantype_assoc_table = db.Table(  # pylint: disable=no-member
    'reporting_session_scantype_assoc', db.Model.metadata,  # noqa pylint: disable=no-member
    db.Column('id', db.Integer, primary_key=True),  # noqa pylint: disable=no-member
    db.Column('session_id', db.Integer, db.ForeignKey('reporting_session.id')),  # noqa pylint: disable=no-member
    db.Column('scantype_id', db.Integer,  # noqa pylint: disable=no-member
              db.ForeignKey('reporting_scantype.id')))  # noqa pylint: disable=no-member


report_scantype_assoc_table = db.Table(  # pylint: disable=no-member
    'reporting_report_scantype_assoc', db.Model.metadata,  # noqa pylint: disable=no-member
    db.Column('id', db.Integer, primary_key=True),  # noqa pylint: disable=no-member
    db.Column('report_id', db.Integer, db.ForeignKey('reporting_report.id')),  # noqa pylint: disable=no-member
    db.Column('scantype_id', db.Integer, db.ForeignKey('reporting_scantype.id')))  # noqa pylint: disable=no-member
