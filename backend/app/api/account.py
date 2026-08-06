import os
import uuid
from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import jwt_required
from ..authz import current_user
from ..errors import ApiError
from ..extensions import db
from ..models import AgentApplication, ApplicationStatus, Conversation, ConversationMessage, Favorite, Property, PropertyStatus, User, UserRole

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


@account_bp.post("/change-password")
@jwt_required()
def change_password():
    user, data = current_user(), request.get_json(silent=True) or {}
    current_password, new_password = str(data.get("currentPassword", "")), str(data.get("newPassword", ""))
    if not user.check_password(current_password):
        raise ApiError("Current password is incorrect.", 400)
    if len(new_password) < 8 or new_password == current_password:
        raise ApiError("New password must be at least 8 characters and different from the current password.")
    user.set_password(new_password)
    db.session.commit()
    return jsonify({"message": "Password changed successfully."})


@account_bp.get("/favorites")
@jwt_required()
def favorites():
    user = current_user()
    query = db.select(Property).join(Favorite).where(Favorite.user_id == user.id, Property.status == PropertyStatus.ACTIVE).order_by(Favorite.created_at.desc())
    return jsonify({"items": [item.to_card_dict() for item in db.session.scalars(query).all()]})


@account_bp.get("/favorite-ids")
@jwt_required()
def favorite_ids():
    user = current_user()
    ids = db.session.scalars(db.select(Favorite.property_id).where(Favorite.user_id == user.id)).all()
    return jsonify({"ids": ids})


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
    if user.id == property_item.agent_id:
        raise ApiError("You cannot start a conversation about your own listing.")
    conversation = db.session.scalar(db.select(Conversation).where(Conversation.user_id == user.id, Conversation.agent_id == property_item.agent_id, Conversation.property_id == property_item.id))
    if not conversation:
        conversation = Conversation(user_id=user.id, agent_id=property_item.agent_id, property_id=property_item.id)
        db.session.add(conversation); db.session.flush()
    entry = ConversationMessage(conversation_id=conversation.id, sender_id=user.id, body=message)
    db.session.add(entry)
    db.session.commit()
    return jsonify({"id": conversation.id, "message": "Your message has been sent."}), 201


def conversation_payload(conversation, viewer_id, include_messages=False):
    prop = db.session.get(Property, conversation.property_id)
    user, agent = db.session.get(User, conversation.user_id), db.session.get(User, conversation.agent_id)
    messages = db.session.scalars(db.select(ConversationMessage).where(ConversationMessage.conversation_id == conversation.id).order_by(ConversationMessage.created_at)).all()
    last = messages[-1] if messages else None
    result = {"id": conversation.id, "user": user.to_dict(), "agent": agent.to_dict(), "property": prop.to_card_dict(), "lastMessage": last.body if last else "", "lastMessageAt": last.created_at.isoformat() if last else conversation.created_at.isoformat(), "unread": sum(not m.is_read and m.sender_id != viewer_id for m in messages)}
    if include_messages:
        result["messages"] = [{"id": m.id, "body": m.body, "senderId": m.sender_id, "createdAt": m.created_at.isoformat(), "isRead": m.is_read} for m in messages]
    return result


@account_bp.get("/conversations")
@jwt_required()
def conversations():
    user = current_user()
    rows = db.session.scalars(db.select(Conversation).where((Conversation.user_id == user.id) | (Conversation.agent_id == user.id)).order_by(Conversation.updated_at.desc())).all()
    return jsonify({"items": [conversation_payload(row, user.id) for row in rows]})


@account_bp.get("/conversations/<int:conversation_id>")
@jwt_required()
def conversation_detail(conversation_id):
    user, conversation = current_user(), db.get_or_404(Conversation, conversation_id)
    if user.id not in (conversation.user_id, conversation.agent_id): raise ApiError("You cannot access this conversation.", 403)
    messages = db.session.scalars(db.select(ConversationMessage).where(ConversationMessage.conversation_id == conversation.id, ConversationMessage.sender_id != user.id, ConversationMessage.is_read.is_(False))).all()
    for message in messages: message.is_read = True
    db.session.commit()
    return jsonify({"conversation": conversation_payload(conversation, user.id, True)})


@account_bp.post("/conversations/<int:conversation_id>/messages")
@jwt_required()
def reply(conversation_id):
    user, conversation = current_user(), db.get_or_404(Conversation, conversation_id)
    if user.id not in (conversation.user_id, conversation.agent_id): raise ApiError("You cannot access this conversation.", 403)
    body = str((request.get_json(silent=True) or {}).get("message", "")).strip()
    if not 1 <= len(body) <= 2000: raise ApiError("Message must be between 1 and 2,000 characters.")
    db.session.add(ConversationMessage(conversation_id=conversation.id, sender_id=user.id, body=body)); db.session.commit()
    return jsonify({"message": "Reply sent."}), 201


@account_bp.get("/unread-count")
@jwt_required()
def unread_count():
    user = current_user()
    count = db.session.scalar(db.select(db.func.count(ConversationMessage.id)).join(Conversation).where(((Conversation.user_id == user.id) | (Conversation.agent_id == user.id)), ConversationMessage.sender_id != user.id, ConversationMessage.is_read.is_(False)))
    return jsonify({"count": count or 0})


@account_bp.post("/agent-application")
@jwt_required()
def apply_agent():
    user = current_user()
    data = request.form if request.form else (request.get_json(silent=True) or {})
    if user.role == UserRole.AGENT: raise ApiError("You are already an approved agent.", 409)
    if user.role == UserRole.ADMIN: raise ApiError("Administrators cannot submit agent applications.", 409)
    existing = db.session.scalar(db.select(AgentApplication).where(AgentApplication.user_id == user.id, AgentApplication.status == ApplicationStatus.PENDING))
    if existing:
        raise ApiError("You already have an application under review.", 409)
    required = ("phone", "city", "message")
    if any(not str(data.get(key, "")).strip() for key in required):
        raise ApiError("Please complete all required application fields.")
    upload = request.files.get("cv")
    storage_name = original_name = mime_type = None
    if upload and upload.filename:
        if not upload.filename.lower().endswith(".pdf") or upload.mimetype != "application/pdf": raise ApiError("CV must be a PDF file.")
        upload.seek(0, 2); size = upload.tell(); upload.seek(0)
        if size > 5 * 1024 * 1024: raise ApiError("CV must be 5 MB or smaller.")
        storage_name, original_name, mime_type = f"{uuid.uuid4().hex}.pdf", os.path.basename(upload.filename)[:255], "application/pdf"
        upload_dir = current_app.config.get("UPLOAD_FOLDER") or os.path.join(current_app.instance_path, "uploads", "cvs")
        os.makedirs(upload_dir, exist_ok=True); upload.save(os.path.join(upload_dir, storage_name))
    application = AgentApplication(user_id=user.id, full_name=user.full_name, email=user.email, phone=data["phone"].strip(), city=data["city"].strip(), agency_name=str(data.get("agencyName", "")).strip() or None, experience=str(data.get("experience", "")).strip() or None, message=data["message"].strip(), cv_storage_name=storage_name, cv_original_name=original_name, cv_mime_type=mime_type)
    db.session.add(application)
    db.session.commit()
    return jsonify({"id": application.id, "status": application.status.value}), 201
