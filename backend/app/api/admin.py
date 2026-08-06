from flask import Blueprint, jsonify, request
from sqlalchemy import func
from ..authz import current_user, roles_required
from ..errors import ApiError
from ..extensions import db
from ..models import AgentApplication, ApplicationStatus, Property, User, UserRole

admin_bp = Blueprint("admin", __name__)


@admin_bp.get("/overview")
@roles_required(UserRole.ADMIN)
def overview():
    return jsonify({"totalUsers": db.session.scalar(db.select(func.count(User.id))), "totalAgents": db.session.scalar(db.select(func.count(User.id)).where(User.role == UserRole.AGENT)), "totalListings": db.session.scalar(db.select(func.count(Property.id))), "pendingApplications": db.session.scalar(db.select(func.count(AgentApplication.id)).where(AgentApplication.status == ApplicationStatus.PENDING))})


@admin_bp.get("/users")
@roles_required(UserRole.ADMIN)
def users():
    items = db.session.scalars(db.select(User).order_by(User.created_at.desc())).all()
    return jsonify({"items": [u.to_dict() | {"isActive": u.is_active, "createdAt": u.created_at.isoformat()} for u in items]})


@admin_bp.patch("/users/<int:user_id>")
@roles_required(UserRole.ADMIN)
def update_user(user_id):
    admin, user, data = current_user(), db.get_or_404(User, user_id), request.get_json(silent=True) or {}
    if user.id == admin.id and data.get("isActive") is False: raise ApiError("You cannot disable your own account.")
    if "isActive" in data: user.is_active = bool(data["isActive"])
    db.session.commit(); return jsonify({"user": user.to_dict() | {"isActive": user.is_active}})


@admin_bp.get("/properties")
@roles_required(UserRole.ADMIN)
def properties():
    rows = db.session.execute(db.select(Property, User).join(User, Property.agent_id == User.id).order_by(Property.created_at.desc())).all()
    return jsonify({"items": [p.to_card_dict() | {"description": p.description, "parkingSpaces": p.parking_spaces, "floor": p.floor, "yearBuilt": p.year_built, "images": [{"id": image.id, "url": image.url, "altText": image.alt_text} for image in p.images], "status": p.status.value, "agent": u.to_dict()} for p,u in rows]})


@admin_bp.get("/agent-applications")
@roles_required(UserRole.ADMIN)
def applications():
    rows = db.session.execute(db.select(AgentApplication, User).join(User, AgentApplication.user_id == User.id).order_by(AgentApplication.created_at.desc())).all()
    return jsonify({"items": [{"id": a.id, "fullName": a.full_name, "email": a.email, "phone": a.phone, "city": a.city, "agencyName": a.agency_name, "experience": a.experience, "message": a.message, "status": a.status.value, "createdAt": a.created_at.isoformat(), "user": u.to_dict()} for a,u in rows]})


@admin_bp.patch("/agent-applications/<int:application_id>")
@roles_required(UserRole.ADMIN)
def review_application(application_id):
    admin, application, data = current_user(), db.get_or_404(AgentApplication, application_id), request.get_json(silent=True) or {}
    if application.status != ApplicationStatus.PENDING: raise ApiError("This application has already been reviewed.", 409)
    try: status = ApplicationStatus(data.get("status"))
    except ValueError: raise ApiError("Status must be approved or rejected.")
    if status == ApplicationStatus.PENDING: raise ApiError("Status must be approved or rejected.")
    application.status, application.reviewed_by_id = status, admin.id
    if status == ApplicationStatus.APPROVED:
        user = db.session.get(User, application.user_id); user.role = UserRole.AGENT; user.agency_name = application.agency_name
    db.session.commit(); return jsonify({"status": application.status.value})
