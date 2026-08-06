from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from ..authz import current_user
from ..errors import ApiError
from ..extensions import db
from ..models import AgentApplication, ApplicationStatus, Favorite, Inquiry, Property, PropertyStatus, UserRole

account_bp = Blueprint("account", __name__)


@account_bp.patch("/profile")
@jwt_required()
def update_profile():
    user, data = current_user(), request.get_json(silent=True) or {}
    for source, target in (("firstName", "first_name"), ("lastName", "last_name"), ("phone", "phone"), ("avatarUrl", "avatar_url")):
        if source in data:
            value = str(data[source]).strip() or None
            if source in ("firstName", "lastName") and not value:
                raise ApiError("First and last name are required.")
            setattr(user, target, value)
    db.session.commit()
    return jsonify({"user": user.to_dict()})


@account_bp.get("/favorites")
@jwt_required()
def favorites():
    user = current_user()
    query = db.select(Property).join(Favorite).where(Favorite.user_id == user.id, Property.status == PropertyStatus.ACTIVE).order_by(Favorite.created_at.desc())
    return jsonify({"items": [item.to_card_dict() for item in db.session.scalars(query).all()]})


@account_bp.put("/favorites/<int:property_id>")
@jwt_required()
def save_favorite(property_id):
    user = current_user()
    db.get_or_404(Property, property_id)
    favorite = db.session.scalar(db.select(Favorite).where(Favorite.user_id == user.id, Favorite.property_id == property_id))
    if not favorite:
        db.session.add(Favorite(user_id=user.id, property_id=property_id))
    db.session.commit()
    return jsonify({"saved": True})


@account_bp.delete("/favorites/<int:property_id>")
@jwt_required()
def remove_favorite(property_id):
    user = current_user()
    favorite = db.session.scalar(db.select(Favorite).where(Favorite.user_id == user.id, Favorite.property_id == property_id))
    if favorite:
        db.session.delete(favorite)
        db.session.commit()
    return "", 204


@account_bp.post("/inquiries")
@jwt_required()
def create_inquiry():
    user, data = current_user(), request.get_json(silent=True) or {}
    message = str(data.get("message", "")).strip()
    if len(message) < 10 or len(message) > 2000:
        raise ApiError("Your message must be between 10 and 2,000 characters.")
    property_item = db.get_or_404(Property, data.get("propertyId"))
    inquiry = Inquiry(sender_id=user.id, agent_id=property_item.agent_id, property_id=property_item.id, message=message)
    db.session.add(inquiry)
    db.session.commit()
    return jsonify({"id": inquiry.id, "message": "Your inquiry has been sent."}), 201


@account_bp.post("/agent-application")
@jwt_required()
def apply_agent():
    user, data = current_user(), request.get_json(silent=True) or {}
    if user.role != UserRole.USER:
        raise ApiError("Only standard user accounts can submit an agent application.", 409)
    existing = db.session.scalar(db.select(AgentApplication).where(AgentApplication.user_id == user.id, AgentApplication.status == ApplicationStatus.PENDING))
    if existing:
        raise ApiError("You already have an application under review.", 409)
    required = ("fullName", "email", "phone", "city", "message")
    if any(not str(data.get(key, "")).strip() for key in required):
        raise ApiError("Please complete all required application fields.")
    application = AgentApplication(user_id=user.id, full_name=data["fullName"].strip(), email=data["email"].strip(), phone=data["phone"].strip(), city=data["city"].strip(), agency_name=str(data.get("agencyName", "")).strip() or None, experience=str(data.get("experience", "")).strip() or None, message=data["message"].strip())
    db.session.add(application)
    db.session.commit()
    return jsonify({"id": application.id, "status": application.status.value}), 201
