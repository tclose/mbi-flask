from mbi_flask import db
from .constants import (
    SESSION_PRIORITY, REPORTER_STATUS, NEW, LOW)


class Reporter(db.Model):

    __tablename__ = 'reporting_reporter'

    id = db.Column(db.Integer, primary_key=True)  # pylint: disable=no-member
    name = db.Column(db.String(50), unique=True)  # pylint: disable=no-member
    suffixes = db.Column(db.String(30), unique=True)  # noqa pylint: disable=no-member
    email = db.Column(db.String(120), unique=True)  # pylint: disable=no-member
    password = db.Column(db.String(120))  # pylint: disable=no-member
    status = db.Column(db.SmallInteger, default=NEW)  # noqa pylint: disable=no-member

    def __init__(self, name, suffixes=None, email=None, password=None,
                 status=NEW):
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


class Subject(db.Model):

    __tablename__ = 'reporting_subject'

    id = db.Column(db.Integer, primary_key=True)  # pylint: disable=no-member
    subject_id = db.Column(db.String(10), unique=True)  # noqa pylint: disable=no-member
    dob = db.Column(db.Date())  # pylint: disable=no-member

    def __init__(self, subject_id, dob):
        self.subject_id = subject_id
        self.dob = dob


class Session(db.Model):

    __tablename__ = 'reporting_session'

    id = db.Column(db.Integer, primary_key=True)  # pylint: disable=no-member
    study_id = db.Column(db.String(10), unique=True)  # noqa pylint: disable=no-member
    subject_id = db.Column(db.Integer, db.ForeignKey('reporting_subject.id'))  # noqa pylint: disable=no-member
    xnat_id = db.Column(db.String(6), unique=True)  # noqa pylint: disable=no-member
    scan_date = db.Column(db.Date())  # pylint: disable=no-member
    priority = db.Column(db.Integer)  # pylint: disable=no-member
    report_date = db.Column(db.Date())  # pylint: disable=no-member
    reported_by = db.Column(db.Integer, db.ForeignKey('reporting_reporter.id'))  # noqa pylint: disable=no-member
    findings = db.Column(db.Text)  # pylint: disable=no-member
    conclusion = db.Column(db.Integer)  # pylint: disable=no-member

    def __init__(self, study_id, subject_id, xnat_id, scan_date, priority=LOW,
                 report_date=None, reported_by=None, findings=None,
                 conclusion=None):
        self.study_id = study_id
        self.subject_id = subject_id
        self.xnat_id = xnat_id
        self.scan_date = scan_date
        self.priority = priority
        if report_date is not None:
            self.report_date = report_date
        if reported_by is not None:
            self.reported_by = reported_by
        if findings is not None:
            self.findings = findings
        if conclusion is not None:
            self.conclusion = conclusion

    def __repr__(self):
        return '<Session {}>'.format(self.xnat_id)

    @property
    def priority_str(self):
        return SESSION_PRIORITY[self.priority]
