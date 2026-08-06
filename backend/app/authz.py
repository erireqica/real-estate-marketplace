from functools import wraps
from flask_jwt_extended import get_jwt_identity, jwt_required
from .errors import ApiError
from .extensions import db
from .models import User, UserRole


def current_user() -> User:
    user = db.session.get(User, int(get_jwt_identity()))
    if not user or not user.is_active:
        raise ApiError("Account unavailable.", 401)
    return user


def roles_required(*roles: UserRole):
    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapped(*args, **kwargs):
            if current_user().role not in roles:
                raise ApiError("You do not have permission to perform this action.", 403)
            return fn(*args, **kwargs)
        return wrapped
    return decorator

