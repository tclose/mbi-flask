from app import db
from app.reporting.constants import REPORTER_STATUS, NEW


class Reporter(db.Model):

    __tablename__ = 'reporting_reporter'
    id = db.Column(db.Integer, primary_key=True)  # pylint: disable=no-member
    name = db.Column(db.String(50), unique=True)  # pylint: disable=no-member
    title = db.Column(db.String(20), unique=True)  # pylint: disable=no-member
    email = db.Column(db.String(120), unique=True)  # pylint: disable=no-member
    password = db.Column(db.String(120))  # pylint: disable=no-member
    status = db.Column(db.SmallInteger, default=NEW)  # noqa pylint: disable=no-member

    def __init__(self, name, title=None, email=None, password=None):
        self.name = name
        self.title = title
        self.email = email
        self.password = password

    @property
    def get_status(self):
        return REPORTER_STATUS[self.status]

    def __repr__(self):
        return '<Reporter %r>' % (self.name)


class Session(db.Model):

    __tablename__ = 'reporting_session'
    id = db.Column(db.Integer, primary_key=True)  # pylint: disable=no-member
    subject_id = db.Column(db.String(10), unique=True)  # noqa pylint: disable=no-member
    xnat_id = db.Column(db.String(6), unique=True)  # noqa pylint: disable=no-member
    priority = db.Column(db.Integer)  # pylint: disable=no-member
    dob = db.Column(db.Date())  # pylint: disable=no-member
    scan_date = db.Column(db.Date())  # pylint: disable=no-member
    report_date = db.Column(db.Date())  # pylint: disable=no-member
    clinical_notes = db.Column(db.Text)  # pylint: disable=no-member
    technique = db.Column(db.Text)  # pylint: disable=no-member
    findings = db.Column(db.Text)  # pylint: disable=no-member
    conclusion = db.Column(db.Integer)  # pylint: disable=no-member
    reported_by = db.Column(db.String(200))  # pylint: disable=no-member

    def __init__(self, subject_id, project_id, priority=0):
        self.subject_id = subject_id
        self.project_id = project_id
        self.priority = priority

    def __repr__(self):
        return '<Session %r>' % (self.name)
