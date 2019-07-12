from datetime import datetime
from mbi_flask import db
from .constants import (
    SESSION_PRIORITY, REPORTER_STATUS, NEW, LOW)


class Subject(db.Model):

    __tablename__ = 'reporting_subject'

    # Fields
    id = db.Column(db.Integer, primary_key=True)  # pylint: disable=no-member
    subject_id = db.Column(db.String(10), unique=True)  # noqa pylint: disable=no-member
    dob = db.Column(db.Date())  # pylint: disable=no-member

    # Relationships
    sessions = db.relationship('ImagingSession', back_populates='subject')  # noqa pylint: disable=no-member

    def __init__(self, subject_id, dob):
        self.subject_id = subject_id
        self.dob = dob

    def __repr__(self):
        return '<Subject {}>'.format(self.subject_id)


class ImagingSession(db.Model):

    __tablename__ = 'reporting_session'

    # Fields
    id = db.Column(db.Integer, primary_key=True)  # pylint: disable=no-member
    subject_id = db.Column(db.Integer, db.ForeignKey('reporting_subject.id'))  # noqa pylint: disable=no-member
    xnat_id = db.Column(db.String(6), unique=True)  # noqa pylint: disable=no-member
    date = db.Column(db.Date())  # pylint: disable=no-member
    priority = db.Column(db.Integer)  # pylint: disable=no-member

    # Relationships
    subject = db.relationship('Subject', back_populates='sessions')  # noqa pylint: disable=no-member
    reports = db.relationship('Report', back_populates='session')  # noqa pylint: disable=no-member

    def __init__(self, id, subject_id, xnat_id, date, priority=LOW):
        self.id = id
        self.subject_id = subject_id
        self.xnat_id = xnat_id
        self.date = date
        self.priority = priority

    def __repr__(self):
        return '<Session {}>'.format(self.xnat_id)

    @property
    def priority_str(self):
        return SESSION_PRIORITY[self.priority]


scan_type_assoc_table = db.Table(  # pylint: disable=no-member
    'reporting_scan_type_assoc', db.Base.metadata,  # noqa pylint: disable=no-member
    db.Column('left_id', db.Integer, db.ForeignKey('left.id')),  # noqa pylint: disable=no-member
    db.Column('right_id', db.Integer, db.ForeignKey('right.id'))  # noqa pylint: disable=no-member
)


class Report(db.Model):

    __tablename__ = 'reporting_report'

    # Fields
    id = db.Column(db.Integer, primary_key=True)  # pylint: disable=no-member
    date = db.Column(db.Date())  # pylint: disable=no-member
    session_id = db.Column(db.Integer, db.ForeignKey('reporting_session.id'))  # noqa pylint: disable=no-member
    reporter_id = db.Column(db.Integer, db.ForeignKey('reporting_reporter.id'))  # noqa pylint: disable=no-member
    findings = db.Column(db.Text)  # pylint: disable=no-member
    conclusion = db.Column(db.Integer)  # pylint: disable=no-member

    # Relationships
    session = db.relationship('ImagingSession', back_populates='reports')  # noqa pylint: disable=no-member
    reporter = db.relationship('Reporter', back_populates='reports')  # noqa pylint: disable=no-member
    scan_types = db.relationship('ScanType', secondary=scan_type_assoc_table)  # noqa pylint: disable=no-member

    def __init__(self, session_id, reporter_id, findings, conclusion,
                 scan_types, date=datetime.today()):
        self.session_id = session_id
        self.reporter_id = reporter_id
        self.findings = findings
        self.conclusion = conclusion
        self.scan_types = scan_types
        self.date = date


class Reporter(db.Model):

    __tablename__ = 'reporting_reporter'

    # Fields
    id = db.Column(db.Integer, primary_key=True)  # pylint: disable=no-member
    name = db.Column(db.String(50), unique=True)  # pylint: disable=no-member
    suffixes = db.Column(db.String(30), unique=True)  # noqa pylint: disable=no-member
    email = db.Column(db.String(120), unique=True)  # pylint: disable=no-member
    password = db.Column(db.String(120))  # pylint: disable=no-member
    status = db.Column(db.SmallInteger, default=NEW)  # noqa pylint: disable=no-member

    # Relationships
    reports = db.relationship('Report', back_populates='reporter')  # noqa pylint: disable=no-member

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
        return '<Reporter {}>'.format(self.name)


class ScanType(db.Model):

    __tablename__ = 'reporting_scantype'

    # Fields
    id = db.Column(db.Integer, primary_key=True)  # pylint: disable=no-member
    type = db.Column(db.String(150), unique=True)  # pylint: disable=no-member
    alias = db.Column(db.Integer)  # pylint: disable=no-member

    def __init__(type, alias=None):
        self.type = type
        self.alias = alias
