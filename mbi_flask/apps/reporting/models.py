from datetime import datetime
from mbi_flask import db
from sqlalchemy.ext.declarative import declarative_base
from .constants import (
    SESSION_PRIORITY, REPORTER_STATUS, NEW, LOW)

Base = declarative_base()


class Subject(db.Model):

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


scantype_session_assoc_table = db.Table(  # pylint: disable=no-member
    'scantype_session_assoc', db.Model.metadata,  # noqa pylint: disable=no-member
    db.Column('id', db.Integer, primary_key=True),  # noqa pylint: disable=no-member
    db.Column('session_id', db.Integer, db.ForeignKey('reporting_session.id')),  # noqa pylint: disable=no-member
    db.Column('scantype_id', db.Integer, db.ForeignKey('reporting_scantype.id'))  # noqa pylint: disable=no-member
)


scantype_report_assoc_table = db.Table(  # pylint: disable=no-member
    'scantype_report_assoc', db.Model.metadata,  # noqa pylint: disable=no-member
    db.Column('id', db.Integer, primary_key=True),  # noqa pylint: disable=no-member
    db.Column('report_id', db.Integer, db.ForeignKey('reporting_report.id')),  # noqa pylint: disable=no-member
    db.Column('scantype_id', db.Integer, db.ForeignKey('reporting_scantype.id'))  # noqa pylint: disable=no-member
)


class ImagingSession(db.Model):

    __tablename__ = 'reporting_session'

    # Fields
    id = db.Column(db.Integer, primary_key=True)  # pylint: disable=no-member
    subject_id = db.Column(db.Integer, db.ForeignKey('reporting_subject.id'))  # noqa pylint: disable=no-member
    xnat_id = db.Column(db.String(6))  # noqa pylint: disable=no-member
    scan_date = db.Column(db.Date())  # pylint: disable=no-member
    priority = db.Column(db.Integer)  # pylint: disable=no-member

    # Relationships
    subject = db.relationship('Subject', back_populates='sessions')  # noqa pylint: disable=no-member
    reports = db.relationship('Report', back_populates='session')  # noqa pylint: disable=no-member
    avail_scan_types = db.relationship('ScanType', secondary=scantype_session_assoc_table)  # noqa pylint: disable=no-member

    def __init__(self, id, subject_id, xnat_id, scan_date, priority=LOW):
        self.id = id
        self.subject_id = subject_id
        self.xnat_id = xnat_id
        self.scan_date = scan_date
        self.priority = priority

    def __repr__(self):
        return '<Session {}>'.format(self.xnat_id)

    @property
    def priority_str(self):
        return SESSION_PRIORITY[self.priority]


class Report(db.Model):

    __tablename__ = 'reporting_report'

    # Fields
    id = db.Column(db.Integer, primary_key=True)  # pylint: disable=no-member
    date = db.Column(db.Date())  # pylint: disable=no-member
    session_id = db.Column(db.Integer, db.ForeignKey('reporting_session.id'))  # noqa pylint: disable=no-member
    user_id = db.Column(db.Integer, db.ForeignKey('reporting_user.id'))  # noqa pylint: disable=no-member
    findings = db.Column(db.Text)  # pylint: disable=no-member
    conclusion = db.Column(db.Integer)  # pylint: disable=no-member

    # Relationships
    session = db.relationship('ImagingSession', back_populates='reports')  # noqa pylint: disable=no-member
    user = db.relationship('User', back_populates='reports')  # noqa pylint: disable=no-member
    scan_types = db.relationship('ScanType', secondary=scantype_report_assoc_table)  # noqa pylint: disable=no-member

    def __init__(self, session_id, user_id, findings, conclusion,
                 scan_types, date=datetime.today()):
        self.session_id = session_id
        self.user_id = user_id
        self.findings = findings
        self.conclusion = conclusion
        self.scan_types = scan_types
        self.date = date


class ScanType(db.Model):

    __tablename__ = 'reporting_scantype'

    # Fields
    id = db.Column(db.Integer, primary_key=True)  # pylint: disable=no-member
    scan_type = db.Column(db.String(150), unique=True)  # noqa pylint: disable=no-member
    alias = db.Column(db.Integer)  # pylint: disable=no-member

    def __init__(self, scan_type, alias=None):
        self.scan_type = scan_type
        self.alias = alias


class User(db.Model):

    __tablename__ = 'reporting_user'

    # Fields
    id = db.Column(db.Integer, primary_key=True)  # pylint: disable=no-member
    name = db.Column(db.String(50), unique=True)  # pylint: disable=no-member
    suffixes = db.Column(db.String(30), unique=True)  # noqa pylint: disable=no-member
    email = db.Column(db.String(120), unique=True)  # pylint: disable=no-member
    password = db.Column(db.String(120))  # pylint: disable=no-member
    status = db.Column(db.SmallInteger, default=NEW)  # noqa pylint: disable=no-member

    # Relationships
    reports = db.relationship('Report', back_populates='user')  # noqa pylint: disable=no-member

    def __init__(self, name, suffixes, email, password, status=NEW):
        self.name = name
        self.suffixes = suffixes
        self.email = email
        self.password = password
        self.status = status

    @property
    def status_str(self):
        return REPORTER_STATUS[self.status]

    def __repr__(self):
        return '<User {}>'.format(self.name)
