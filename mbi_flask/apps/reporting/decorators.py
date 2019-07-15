from functools import wraps
from flask import g, flash, redirect, url_for, request


def requires_role(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if g.user is None:
                flash('You need to be signed in to access that page.',
                      'warning')
                accepted = False
            elif role not in [r.name for r in g.user.roles]:
                flash("'{}' doesn't have the role '{}', which is required to "
                      " access this page", 'error')
                accepted = False
            else:
                accepted = True
            if not accepted:
                return redirect(url_for('reporting.login', next=request.path))
            return f(*args, **kwargs)
        return decorated_function
    return decorator
