import re
from flask import Blueprint, jsonify, request
from ..authz import current_user, roles_required
from ..errors import ApiError
from ..extensions import db
from ..models import Amenity, Inquiry, ListingPurpose, Property, PropertyImage, PropertyStatus, PropertyType, User, UserRole

agent_bp = Blueprint("agent", __name__)


def property_payload(item):
    return item.to_card_dict() | {"description": item.description, "amenities": [amenity.name for amenity in item.amenities], "parkingSpaces": item.parking_spaces, "floor": item.floor, "yearBuilt": item.year_built, "images": [{"id": image.id, "url": image.url, "altText": image.alt_text} for image in item.images], "status": item.status.value, "views": item.views, "createdAt": item.created_at.isoformat()}


@agent_bp.get("/overview")
@roles_required(UserRole.AGENT, UserRole.ADMIN)
def overview():
    user = current_user()
    properties = db.session.scalars(db.select(Property).where(Property.agent_id == user.id)).all()
    inquiries = db.session.scalars(db.select(Inquiry).where(Inquiry.agent_id == user.id).order_by(Inquiry.created_at.desc())).all()
    return jsonify({"activeListings": sum(p.status == PropertyStatus.ACTIVE for p in properties), "totalViews": sum(p.views for p in properties), "inquiries": len(inquiries), "unreadInquiries": sum(not i.is_read for i in inquiries), "recentProperties": [property_payload(p) for p in properties[-4:]]})


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


@agent_bp.post("/properties")
@roles_required(UserRole.AGENT, UserRole.ADMIN)
def create_property():
    user, data = current_user(), request.get_json(silent=True) or {}
    base = re.sub(r"[^a-z0-9]+", "-", str(data.get("title", "")).lower()).strip("-") or "property"
    item = Property(agent_id=user.id, slug=f"{base}-{user.id}-{Property.query.count()+1}")
    populate_property(item, data)
    populate_amenities(item, data)
    db.session.add(item)
    db.session.flush()
    for position, url in enumerate(data.get("images", [])):
        if str(url).startswith(("http://", "https://")): db.session.add(PropertyImage(property_id=item.id, url=url, position=position, alt_text=item.title))
    db.session.commit()
    return jsonify({"property": property_payload(item)}), 201


@agent_bp.patch("/properties/<int:property_id>")
@roles_required(UserRole.AGENT, UserRole.ADMIN)
def update_property(property_id):
    user, item = current_user(), db.get_or_404(Property, property_id)
    if item.agent_id != user.id and user.role != UserRole.ADMIN: raise ApiError("You can only edit your own listings.", 403)
    data = request.get_json(silent=True) or {}
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
    rows = db.session.execute(db.select(Inquiry, User, Property).join(User, Inquiry.sender_id == User.id).join(Property, Inquiry.property_id == Property.id).where(Inquiry.agent_id == user.id).order_by(Inquiry.created_at.desc())).all()
    return jsonify({"items": [{"id": i.id, "message": i.message, "isRead": i.is_read, "createdAt": i.created_at.isoformat(), "sender": u.to_dict(), "property": p.to_card_dict()} for i,u,p in rows]})


@agent_bp.patch("/inquiries/<int:inquiry_id>")
@roles_required(UserRole.AGENT, UserRole.ADMIN)
def mark_inquiry(inquiry_id):
    user, inquiry = current_user(), db.get_or_404(Inquiry, inquiry_id)
    if inquiry.agent_id != user.id: raise ApiError("This inquiry does not belong to you.", 403)
    inquiry.is_read = bool((request.get_json(silent=True) or {}).get("isRead", True)); db.session.commit()
    return jsonify({"isRead": inquiry.is_read})
