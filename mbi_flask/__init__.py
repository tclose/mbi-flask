import os.path as op
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy

apps_root = op.join(op.dirname(__file__), 'apps')

templates_dir = op.join(apps_root, 'templates')
static_dir = op.join(apps_root, 'static')

app = Flask(__name__, template_folder=templates_dir, static_folder=static_dir)
app.config.from_object('config')

db = SQLAlchemy(app)


@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

from .apps.reporting.views import mod as reportingModule  # noqa
app.register_blueprint(reportingModule)
