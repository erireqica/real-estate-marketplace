import re
from flask import Blueprint, jsonify, request
from ..authz import current_user, roles_required
from ..errors import ApiError
from ..extensions import db
from ..models import Amenity, Conversation, ConversationMessage, ListingPurpose, Property, PropertyImage, PropertyStatus, PropertyType, User, UserRole

agent_bp = Blueprint("agent", __name__)


def property_payload(item):
    return item.to_card_dict() | {"description": item.description, "amenities": [amenity.name for amenity in item.amenities], "parkingSpaces": item.parking_spaces, "floor": item.floor, "yearBuilt": item.year_built, "images": [{"id": image.id, "url": image.url, "altText": image.alt_text} for image in item.images], "status": item.status.value, "views": item.views, "createdAt": item.created_at.isoformat()}


@agent_bp.get("/overview")
@roles_required(UserRole.AGENT, UserRole.ADMIN)
def overview():
    user = current_user()
    properties = db.session.scalars(db.select(Property).where(Property.agent_id == user.id).order_by(Property.created_at.desc())).all()
    conversations = db.session.scalars(db.select(Conversation).where(Conversation.agent_id == user.id)).all()
    unread = db.session.scalar(db.select(db.func.count(ConversationMessage.id)).join(Conversation).where(Conversation.agent_id == user.id, ConversationMessage.sender_id != user.id, ConversationMessage.is_read.is_(False))) or 0
    return jsonify({"totalListings": len(properties), "activeListings": sum(p.status == PropertyStatus.ACTIVE for p in properties), "totalViews": sum(p.views for p in properties), "inquiries": len(conversations), "unreadInquiries": unread, "recentProperties": [property_payload(p) for p in properties[:4]]})


@agent_bp.get("/properties")
@roles_required(UserRole.AGENT, UserRole.ADMIN)
def my_properties():
    user = current_user()
    return jsonify({"items": [property_payload(p) for p in db.session.scalars(db.select(Property).where(Property.agent_id == user.id).order_by(Property.created_at.desc())).all()]})


def populate_property(item, data):
    required = ("title", "description", "price", "purpose", "propertyType", "city", "address", "areaSqm")
    if any(data.get(key) in (None, "") for key in required):
        raise ApiError("Please complete all required property fields.")
    item.title, item.description = str(data["title"]).strip(), str(data["description"]).strip()
    item.price, item.area_sqm = float(data["price"]), float(data["areaSqm"])
    if item.price <= 0 or item.area_sqm <= 0: raise ApiError("Price and area must be greater than zero.")
    try: item.purpose, item.property_type = ListingPurpose(data["purpose"]), PropertyType(data["propertyType"])
    except ValueError: raise ApiError("Invalid listing purpose or property type.")
    item.city, item.address = str(data["city"]).strip(), str(data["address"]).strip()
    for source, target in (("bedrooms", "bedrooms"), ("bathrooms", "bathrooms"), ("parkingSpaces", "parking_spaces"), ("floor", "floor"), ("yearBuilt", "year_built")):
        setattr(item, target, int(data[source]) if data.get(source) not in (None, "") else None)
    if "status" in data:
        try: item.status = PropertyStatus(data["status"])
        except ValueError: raise ApiError("Invalid listing status.")


def populate_amenities(item, data):
    if "amenities" not in data:
        return
    selected = []
    for raw_name in data.get("amenities", []):
        name = str(raw_name).strip()
        if not name:
            continue
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
        amenity = db.session.scalar(db.select(Amenity).where(Amenity.slug == slug))
        if not amenity:
            amenity = Amenity(name=name[:80], slug=slug[:90]); db.session.add(amenity)
        selected.append(amenity)
    item.amenities = selected


def create_property_for_agent(agent_id, data):
    base = re.sub(r"[^a-z0-9]+", "-", str(data.get("title", "")).lower()).strip("-") or "property"
    item = Property(agent_id=agent_id, slug=f"{base}-{agent_id}-{Property.query.count()+1}")
    populate_property(item, data)
    populate_amenities(item, data)
    db.session.add(item)
    db.session.flush()
    for position, url in enumerate(data.get("images", [])):
        if str(url).startswith(("http://", "https://")):
            db.session.add(PropertyImage(property_id=item.id, url=url, position=position, alt_text=item.title))
    return item


@agent_bp.post("/properties")
@roles_required(UserRole.AGENT, UserRole.ADMIN)
def create_property():
    user, data = current_user(), request.get_json(silent=True) or {}
    item = create_property_for_agent(user.id, data)
    db.session.commit()
    return jsonify({"property": property_payload(item)}), 201


@agent_bp.patch("/properties/<int:property_id>")
@roles_required(UserRole.AGENT, UserRole.ADMIN)
def update_property(property_id):
    user, item = current_user(), db.get_or_404(Property, property_id)
    if item.agent_id != user.id and user.role != UserRole.ADMIN: raise ApiError("You can only edit your own listings.", 403)
    data = request.get_json(silent=True) or {}
    if "agentId" in data:
        if user.role != UserRole.ADMIN: raise ApiError("Only administrators can reassign listing ownership.", 403)
        new_agent = db.session.get(User, int(data["agentId"]))
        if not new_agent or new_agent.role != UserRole.AGENT or not new_agent.is_active:
            raise ApiError("Assigned owner must be an active Agent account.")
        if item.agent_id != new_agent.id:
            item.agent_id = new_agent.id
            for conversation in db.session.scalars(db.select(Conversation).where(Conversation.property_id == item.id)).all():
                conversation.agent_id = new_agent.id
    populate_property(item, data)
    populate_amenities(item, data)
    if "images" in data:
        item.images.clear()
        for position, url in enumerate(data.get("images", [])):
            if str(url).startswith(("http://", "https://")): item.images.append(PropertyImage(url=url, position=position, alt_text=item.title))
    db.session.commit()
    return jsonify({"property": property_payload(item)})


@agent_bp.delete("/properties/<int:property_id>")
@roles_required(UserRole.AGENT, UserRole.ADMIN)
def delete_property(property_id):
    user, item = current_user(), db.get_or_404(Property, property_id)
    if item.agent_id != user.id and user.role != UserRole.ADMIN: raise ApiError("You can only delete your own listings.", 403)
    db.session.delete(item); db.session.commit()
    return "", 204


@agent_bp.get("/inquiries")
@roles_required(UserRole.AGENT, UserRole.ADMIN)
def agent_inquiries():
    user = current_user()
    rows = db.session.scalars(db.select(Conversation).where(Conversation.agent_id == user.id).order_by(Conversation.updated_at.desc())).all()
    items = []
    for conversation in rows:
        sender, prop = db.session.get(User, conversation.user_id), db.session.get(Property, conversation.property_id)
        last = db.session.scalar(db.select(ConversationMessage).where(ConversationMessage.conversation_id == conversation.id).order_by(ConversationMessage.created_at.desc()).limit(1))
        if last: items.append({"id": conversation.id, "message": last.body, "isRead": last.is_read, "createdAt": last.created_at.isoformat(), "sender": sender.to_dict(), "property": prop.to_card_dict()})
    return jsonify({"items": items})


@agent_bp.patch("/inquiries/<int:inquiry_id>")
@roles_required(UserRole.AGENT, UserRole.ADMIN)
def mark_inquiry(inquiry_id):
    user, conversation = current_user(), db.get_or_404(Conversation, inquiry_id)
    if conversation.agent_id != user.id: raise ApiError("This inquiry does not belong to you.", 403)
    value = bool((request.get_json(silent=True) or {}).get("isRead", True))
    messages = db.session.scalars(db.select(ConversationMessage).where(ConversationMessage.conversation_id == inquiry_id, ConversationMessage.sender_id != user.id)).all()
    for message in messages: message.is_read = value
    db.session.commit(); return jsonify({"isRead": value})
