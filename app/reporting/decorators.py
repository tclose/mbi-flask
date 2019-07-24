from functools import wraps
from flask import g, flash, redirect, url_for, request
from app import app
from .models import Role


def requires_login(role_id=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            accepted = False
            if g.user is None:
                flash('You need to be signed in to access that page.',
                      'info')
            elif not g.user.active:
                flash(("Your user account has been created but still needs " +
                       "to be activiated, please contact {}").format(
                           app.config['ADMIN_EMAIL']),
                      'warning')
            elif role_id is not None and not g.user.has_role(role_id):
                flash(("'{}' doesn't have the role '{}', which is required " +
                       "to access this page (they have '{}')").format(
                           g.user.email, Role.query.get(role_id).name,
                           "', '".join(str(r.name) for r in g.user.roles)),
                      'error')
            else:
                accepted = True
            if not accepted:
                return redirect(url_for('reporting.login', next=request.path))
            return f(*args, **kwargs)
        return decorated_function
    return decorator
