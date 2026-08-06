from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity, jwt_required
from ..errors import ApiError
from ..extensions import db
from ..models import User

auth_bp = Blueprint("auth", __name__)


def auth_payload(user):
    claims, identity = {"role": user.role.value}, str(user.id)
    return {"user": user.to_dict(), "accessToken": create_access_token(identity=identity, additional_claims=claims), "refreshToken": create_refresh_token(identity=identity, additional_claims=claims)}


@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    required = ("email", "password", "firstName", "lastName")
    missing = [key for key in required if not str(data.get(key, "")).strip()]
    if missing:
        raise ApiError("Please complete all required fields.", details={"missing": missing})
    email = data["email"].strip().lower()
    if "@" not in email or len(data["password"]) < 8:
        raise ApiError("Enter a valid email and a password of at least 8 characters.")
    if db.session.scalar(db.select(User).where(User.email == email)):
        raise ApiError("An account with this email already exists.", 409)
    user = User(email=email, first_name=data["firstName"].strip(), last_name=data["lastName"].strip())
    user.set_password(data["password"])
    db.session.add(user)
    db.session.commit()
    return jsonify(auth_payload(user)), 201


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    user = db.session.scalar(db.select(User).where(User.email == str(data.get("email", "")).strip().lower()))
    if not user or not user.check_password(str(data.get("password", ""))) or not user.is_active:
        raise ApiError("Incorrect email or password.", 401)
    return jsonify(auth_payload(user))


@auth_bp.get("/me")
@jwt_required()
def me():
    user = db.session.get(User, int(get_jwt_identity()))
    if not user or not user.is_active:
        raise ApiError("Account unavailable.", 401)
    return jsonify({"user": user.to_dict()})


@auth_bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    user = db.session.get(User, int(get_jwt_identity()))
    if not user or not user.is_active:
        raise ApiError("Account unavailable.", 401)
    return jsonify({"accessToken": create_access_token(identity=str(user.id), additional_claims={"role": user.role.value})})
