from flask import Blueprint, jsonify, request
from sqlalchemy import case, func
from ..extensions import db
from ..models import ListingPurpose, Property, PropertyStatus

market_bp = Blueprint("market", __name__)


def snapshot(city=None):
    filters = [Property.status == PropertyStatus.ACTIVE]
    if city: filters.append(Property.city == city)
    row = db.session.execute(db.select(func.count(Property.id), func.coalesce(func.avg(Property.price), 0), func.coalesce(func.avg(Property.area_sqm), 0), func.coalesce(func.avg(Property.price / Property.area_sqm), 0), func.sum(case((Property.purpose == ListingPurpose.SALE, 1), else_=0)), func.sum(case((Property.purpose == ListingPurpose.RENT, 1), else_=0))).where(*filters)).one()
    common_type = db.session.execute(db.select(Property.property_type, func.count(Property.id).label("count")).where(*filters).group_by(Property.property_type).order_by(func.count(Property.id).desc()).limit(1)).first()
    return {"totalListings": row[0], "averagePrice": round(float(row[1]), 2), "averageArea": round(float(row[2]), 1), "averagePricePerSqm": round(float(row[3]), 2), "forSale": row[4] or 0, "forRent": row[5] or 0, "mostCommonType": common_type[0].value if common_type else None}


@market_bp.get("/overview")
def overview():
    cities = db.session.scalars(db.select(Property.city).where(Property.status == PropertyStatus.ACTIVE).distinct().order_by(Property.city)).all()
    active_city = db.session.execute(db.select(Property.city, func.count(Property.id)).where(Property.status == PropertyStatus.ACTIVE).group_by(Property.city).order_by(func.count(Property.id).desc()).limit(1)).first()
    stats = snapshot(request.args.get("city") or None)
    stats["mostActiveLocation"] = active_city[0] if active_city else None
    stats["cities"] = cities
    return jsonify(stats)


@market_bp.get("/trends")
def trends():
    city = request.args.get("city", "Prishtina")
    base = {"Prishtina": 1220, "Prizren": 930, "Peja": 810, "Ferizaj": 760}.get(city, 880)
    return jsonify({"city": city, "source": "demonstration", "series": [{"year": 2022+i, "averagePricePerSqm": round(base*(1.055**i))} for i in range(5)], "disclaimer": "Demonstration trends are market observations, not financial advice."})

