import re
import os.path as op
from datetime import datetime
from app import db, app, signature_images
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import sql, orm
from .constants import (
    SESSION_PRIORITY, REPORTER_STATUS, NEW, LOW, NOT_SCANNED, EXCLUDED,
    PRESENT)

Base = declarative_base()


class User(db.Model):
    """
    User of the application
    """

    __tablename__ = 'user'

    # Fields
    id = db.Column(db.Integer, primary_key=True)  # pylint: disable=no-member
    name = db.Column(db.String(50), unique=True)  # pylint: disable=no-member
    suffixes = db.Column(db.String(30))  # noqa pylint: disable=no-member
    email = db.Column(db.String(120), unique=True)  # pylint: disable=no-member
    password = db.Column(db.String(120))  # pylint: disable=no-member
    active = db.Column(db.Boolean())  # noqa pylint: disable=no-member
    signature = db.Column(db.String(200))  # pylint: disable=no-member

    # Relationships
    reports = db.relationship('Report', back_populates='reporter')  # noqa pylint: disable=no-member
    roles = db.relationship('Role',  # noqa pylint: disable=no-member
                            secondary='user_role_assoc')

    def __init__(self, name, suffixes, email, password, signature=None,
                 roles=[], active=False):
        self.name = name
        self.suffixes = suffixes
        self.email = email
        self.password = password
        self.roles = roles
        self.active = active
        self.signature = signature

    @property
    def status_str(self):
        return REPORTER_STATUS[self.status]

    def __repr__(self):
        return '<User {}>'.format(self.name)

    def has_role(self, role_id):
        """
        Checks whether the user has the required role

        Parameters
        ----------
        role_id : int
            The ID of the required role (i.e. ADMIN_ROLE or REPORTER_ROLE)
        """
        return role_id in [r.id for r in self.roles]

    @property
    def signature_path(self):
        if not self.signature:
            raise Exception("A signature has not been uploaded for '{}'"
                            .format(self.name))
        return signature_images.path(self.signature)


class Role(db.Model):
    """
    Valid user roles (e.g. 'admin' and 'reporter')
    """

    __tablename__ = 'role'

    # Fields
    id = db.Column(db.Integer, primary_key=True)  # pylint: disable=no-member
    name = db.Column(db.String(50), unique=True)  # pylint: disable=no-member

    def __init__(self, id, name):
        self.id = id
        self.name = name


class Project(db.Model):
    """
    A simple representation of the project an imaging session belongs to
    """

    __tablename__ = 'project'

    id = db.Column(db.Integer, primary_key=True)  # noqa pylint: disable=no-member
    mbi_id = db.Column(db.String(10), unique=True)  # noqa pylint: disable=no-member

    # Relationships
    sessions = db.relationship('ImgSession', back_populates='project')  # noqa pylint: disable=no-member

    def __init__(self, mbi_id):
        self.mbi_id = mbi_id


class Subject(db.Model):
    """
    Basic information about the subject of the imaging session. It is
    separated from the imaging session so that we can check for multiple
    in a year (or other arbitrary period) and only provide the latest one.
    """

    __tablename__ = 'subject'

    # Fields
    id = db.Column(db.Integer, primary_key=True)  # pylint: disable=no-member
    mbi_id = db.Column(db.String(10), unique=True)  # noqa pylint: disable=no-member
    first_name = db.Column(db.String(100))  # pylint: disable=no-member
    last_name = db.Column(db.String(100))  # pylint: disable=no-member
    dob = db.Column(db.Date())  # pylint: disable=no-member

    # Relationships
    sessions = db.relationship('ImgSession', back_populates='subject')  # noqa pylint: disable=no-member

    def __init__(self, mbi_id, first_name, last_name, dob):
        self.mbi_id = mbi_id
        self.first_name = first_name
        self.last_name = last_name
        self.dob = dob

    def __repr__(self):
        return '<Subject {}>'.format(self.mbi_id)


class ImgSession(db.Model):
    """
    Details of the imaging session
    """

    __tablename__ = 'session'

    # Fields
    id = db.Column(db.Integer, primary_key=True)  # pylint: disable=no-member
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))  # noqa pylint: disable=no-member
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'))  # noqa pylint: disable=no-member
    xnat_id = db.Column(db.String(50))  # noqa pylint: disable=no-member
    scan_date = db.Column(db.Date())  # pylint: disable=no-member
    priority = db.Column(db.Integer)  # pylint: disable=no-member
    data_status = db.Column(db.Integer)  # pylint: disable=no-member

    # Relationships
    project = db.relationship('Project', back_populates='sessions')  # noqa pylint: disable=no-member
    subject = db.relationship('Subject', back_populates='sessions')  # noqa pylint: disable=no-member
    scans = db.relationship('Scan', back_populates='session')  # noqa pylint: disable=no-member
    reports = db.relationship('Report', back_populates='session')  # noqa pylint: disable=no-member

    def __init__(self, id, project, subject, xnat_id, scan_date,
                 data_status, priority=LOW):
        self.id = id
        self.project = project
        self.subject = subject
        self.xnat_id = xnat_id
        self.scan_date = scan_date
        self.data_status = data_status
        self.priority = priority

    def __repr__(self):
        return '<Session {}>'.format(self.xnat_id)

    @property
    def priority_str(self):
        return SESSION_PRIORITY[self.priority]

    @classmethod
    def require_report(cls):
        """
        Returns a query that selects all imaging sessions that still need to be
        reported
        """
        # Create an alias of the ImgSession model so we can search within
        # its table for more recent sessions and earlier sessions that have
        # been reported
        S = orm.aliased(ImgSession)

        # Create query for sessions that still need to be reported
        require_report = (
            db.session.query(ImgSession)  # pylint: disable=no-member
            # Filter out "ignored" sessions that are to be reported by AXIS
            .filter(~ImgSession.data_status.in_([NOT_SCANNED, EXCLUDED]))
            # Filter out sessions of subjects that have a more recent session
            .filter(~(
                db.session.query(S)  # pylint: disable=no-member
                .filter(
                    S.subject_id == ImgSession.subject_id,
                    S.scan_date > ImgSession.scan_date,
                    ~S.data_status.in_([NOT_SCANNED, EXCLUDED]))
                .exists()))
            # Filter out sessions of subjects that have been reported on less
            # than the REPORT_INTERVAL (e.g. 365 days) beforehand
            .filter(~(
                db.session.query(S)  # pylint: disable=no-member
                .join(Report)  # Only select sessions with a report
                .filter(
                    S.subject_id == ImgSession.subject_id,
                    (sql.func.abs(
                        sql.func.julianday(ImgSession.scan_date) -
                        sql.func.julianday(S.scan_date)) <=
                     app.config['REPORT_INTERVAL']))
                .exists())))
        return require_report

    @classmethod
    def ready_for_export(cls):
        return (
            cls.require_report()
            # Get sessions where the data is present on XNAT
            .filter_by(data_status=PRESENT)
            # Filter out any sessions where there are scan types that haven't
            # been confirmed as clinically or not-clinically relevant
            .filter(~(
                Scan.query
                .filter(
                    Scan.session_id == ImgSession.id,
                    ~Scan.exported)
                .join(ScanType)
                .filter(~ScanType.confirmed).exists())))

    @property
    def target_xnat_uri(self):
        return '{}/data/projects/{}/experiments/{}'.format(
            app.config['TARGET_XNAT_URL'], app.config['TARGET_XNAT_PROJECT'],
            self.xnat_id)

    @property
    def source_xnat_uri(self):
        return '{}/data/projects/{}/experiments/{}'.format(
            app.config['SOURCE_XNAT_URL'], self.xnat_id.split('_')[0],
            self.xnat_id)


class Report(db.Model):
    """
    A report entered by a radiologist
    """

    __tablename__ = 'report'

    # Fields
    id = db.Column(db.Integer, primary_key=True)  # pylint: disable=no-member
    date = db.Column(db.Date())  # pylint: disable=no-member
    session_id = db.Column(db.Integer, db.ForeignKey('session.id'))  # noqa pylint: disable=no-member
    reporter_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # noqa pylint: disable=no-member
    findings = db.Column(db.Text)  # pylint: disable=no-member
    conclusion = db.Column(db.Integer)  # pylint: disable=no-member
    exported = db.Column(db.Boolean)  # pylint: disable=no-member
    modality = db.Column(db.Integer)  # pylint: disable=no-member
    # Whether the report was automatically added from FM import
    dummy = db.Column(db.Boolean)  # pylint: disable=no-member

    # Relationships
    session = db.relationship('ImgSession', back_populates='reports')  # noqa pylint: disable=no-member
    reporter = db.relationship('User', back_populates='reports')  # noqa pylint: disable=no-member
    used_scans = db.relationship(  # noqa pylint: disable=no-member
        'Scan', secondary='report_scan_assoc')

    def __init__(self, session_id, reporter_id, findings, conclusion,
                 used_scans, modality, exported=False,
                 date=datetime.today(), dummy=False):
        self.session_id = session_id
        self.reporter_id = reporter_id
        self.findings = findings
        self.conclusion = conclusion
        self.used_scans = used_scans
        self.exported = exported
        self.date = date
        self.modality = modality
        self.dummy = dummy


class Scan(db.Model):
    """
    The type of (clinically relevant) scans in the session
    """

    __tablename__ = 'scan'

    # Fields
    id = db.Column(db.Integer, primary_key=True)  # pylint: disable=no-member
    session_id = db.Column(db.Integer, db.ForeignKey('session.id'))  # noqa pylint: disable=no-member
    type_id = db.Column(db.Integer, db.ForeignKey('scantype.id'))  # noqa pylint: disable=no-member
    exported = db.Column(db.Boolean)  # noqa pylint: disable=no-member

    # Relationships
    type_ = db.relationship('ScanType', back_populates='scans')   # noqa pylint: disable=no-member
    session = db.relationship('ImgSession', back_populates='scans')  # noqa pylint: disable=no-member
    reports = db.relationship('Report', secondary='report_scan_assoc')  # noqa pylint: disable=no-member

    def __init__(self, session, type_, exported=False):
        self.session = session
        self.type_ = type_
        self.exported = exported

    def __repr__(self):
        return "<ScanType {}>".format(self.name)


class ScanType(db.Model):
    """
    The type of (clinically relevant) scans in the session
    """

    __tablename__ = 'scantype'

    is_clinical_res = [re.compile(s) for s in (
        r'(?!.*kspace.*).*(?<![a-zA-Z])(?i)(t1).*',
        r'(?!.*kspace.*).*(?<![a-zA-Z])(?i)(t2).*',
        r'(?!.*kspace.*).*(?i)(mprage).*',
        r'(?!.*kspace.*).*(?i)(qsm).*',
        r'(?!.*kspace.*).*(?i)(flair).*',
        r'(?!.*kspace.*).*(?i)(fl3d).*')]

    # Fields
    id = db.Column(db.Integer, primary_key=True)  # pylint: disable=no-member
    name = db.Column(db.String(150), unique=True)  # noqa pylint: disable=no-member
    clinical = db.Column(db.Boolean)  # pylint: disable=no-member
    confirmed = db.Column(db.Boolean)  # pylint: disable=no-member

    # Relationships
    scans = db.relationship('Scan', back_populates='type_')  # noqa pylint: disable=no-member

    def __init__(self, name, confirmed=False):
        self.name = name
        self.clinical = any(r.match(name) for r in self.is_clinical_res)
        self.confirmed = confirmed

    def __repr__(self):
        return "<ScanType {}>".format(self.name)


# Many-to-many association tables

user_role_assoc_table = db.Table(  # pylint: disable=no-member
    'user_role_assoc', db.Model.metadata,  # noqa pylint: disable=no-member
    db.Column('id', db.Integer, primary_key=True),  # noqa pylint: disable=no-member
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),  # noqa pylint: disable=no-member
    db.Column('role_id', db.Integer, db.ForeignKey('role.id')))  # noqa pylint: disable=no-member


report_scan_assoc_table = db.Table(  # pylint: disable=no-member
    'report_scan_assoc', db.Model.metadata,  # noqa pylint: disable=no-member
    db.Column('id', db.Integer, primary_key=True),  # noqa pylint: disable=no-member
    db.Column('report_id', db.Integer, db.ForeignKey('report.id')),  # noqa pylint: disable=no-member
    db.Column('scan_id', db.Integer, db.ForeignKey('scan.id')))  # noqa pylint: disable=no-member
