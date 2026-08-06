from flask import Blueprint, jsonify, request
from sqlalchemy import or_
from ..extensions import db
from ..models import Property, PropertyStatus

properties_bp = Blueprint("properties", __name__)


@properties_bp.get("")
def list_properties():
    query = db.select(Property).where(Property.status == PropertyStatus.ACTIVE)
    search = request.args.get("search", "").strip()
    if search:
        pattern = f"%{search}%"
        query = query.where(or_(Property.title.ilike(pattern), Property.city.ilike(pattern), Property.address.ilike(pattern)))
    for arg, column in (("city", Property.city), ("purpose", Property.purpose), ("propertyType", Property.property_type)):
        if value := request.args.get(arg):
            query = query.where(column == value)
    if value := request.args.get("minPrice", type=float): query = query.where(Property.price >= value)
    if value := request.args.get("maxPrice", type=float): query = query.where(Property.price <= value)
    if value := request.args.get("bedrooms", type=int): query = query.where(Property.bedrooms >= value)
    if value := request.args.get("bathrooms", type=int): query = query.where(Property.bathrooms >= value)
    if value := request.args.get("minArea", type=float): query = query.where(Property.area_sqm >= value)
    sort_map = {"price_asc": Property.price.asc(), "price_desc": Property.price.desc(), "area_desc": Property.area_sqm.desc(), "newest": Property.created_at.desc()}
    query = query.order_by(sort_map.get(request.args.get("sort"), Property.created_at.desc()))
    page = max(request.args.get("page", 1, type=int), 1)
    per_page = max(1, min(request.args.get("perPage", 12, type=int), 48))
    result = db.paginate(query, page=page, per_page=per_page, error_out=False)
    return jsonify({"items": [item.to_card_dict() for item in result.items], "pagination": {"page": result.page, "pages": result.pages, "total": result.total}})


@properties_bp.get("/<string:slug>")
def property_detail(slug):
    item = db.first_or_404(db.select(Property).where(Property.slug == slug, Property.status == PropertyStatus.ACTIVE))
    item.views += 1
    db.session.commit()
    data = item.to_card_dict() | {"description": item.description, "parkingSpaces": item.parking_spaces, "floor": item.floor, "yearBuilt": item.year_built, "views": item.views, "images": [{"id": image.id, "url": image.url, "altText": image.alt_text} for image in item.images], "amenities": [amenity.name for amenity in item.amenities], "agent": item.agent.to_dict()}
    return jsonify({"property": data})
