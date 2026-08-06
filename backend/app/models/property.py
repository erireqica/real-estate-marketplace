import enum
from decimal import Decimal
from sqlalchemy import Boolean, CheckConstraint, Enum, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import BaseModel


class ListingPurpose(str, enum.Enum):
    SALE = "sale"
    RENT = "rent"


class PropertyType(str, enum.Enum):
    APARTMENT = "apartment"
    HOUSE = "house"
    VILLA = "villa"
    COMMERCIAL = "commercial"
    LAND = "land"


class PropertyStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class Property(BaseModel):
    __tablename__ = "properties"
    __table_args__ = (
        CheckConstraint("price > 0", name="positive_price"),
        CheckConstraint("area_sqm > 0", name="positive_area"),
        CheckConstraint("bedrooms IS NULL OR bedrooms >= 0", name="nonnegative_bedrooms"),
        CheckConstraint("bathrooms IS NULL OR bathrooms >= 0", name="nonnegative_bathrooms"),
    )
    agent_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(180), index=True)
    slug: Mapped[str] = mapped_column(String(220), unique=True, index=True)
    description: Mapped[str] = mapped_column(Text)
    price: Mapped[Decimal] = mapped_column(Numeric(14, 2), index=True)
    purpose: Mapped[ListingPurpose] = mapped_column(Enum(ListingPurpose), index=True)
    property_type: Mapped[PropertyType] = mapped_column(Enum(PropertyType), index=True)
    status: Mapped[PropertyStatus] = mapped_column(Enum(PropertyStatus), default=PropertyStatus.ACTIVE, index=True)
    city: Mapped[str] = mapped_column(String(100), index=True)
    address: Mapped[str] = mapped_column(String(220))
    bedrooms: Mapped[int | None]
    bathrooms: Mapped[int | None]
    area_sqm: Mapped[Decimal] = mapped_column(Numeric(10, 2), index=True)
    parking_spaces: Mapped[int | None]
    floor: Mapped[int | None]
    year_built: Mapped[int | None]
    views: Mapped[int] = mapped_column(default=0)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    agent = relationship("User", back_populates="properties")
    images = relationship("PropertyImage", back_populates="property", cascade="all, delete-orphan", order_by="PropertyImage.position")
    amenities = relationship("Amenity", secondary="property_amenities", back_populates="properties")

    def to_card_dict(self):
        return {"id": self.id, "slug": self.slug, "title": self.title, "price": float(self.price), "purpose": self.purpose.value, "propertyType": self.property_type.value, "city": self.city, "address": self.address, "bedrooms": self.bedrooms, "bathrooms": self.bathrooms, "areaSqm": float(self.area_sqm), "isFeatured": self.is_featured, "imageUrl": self.images[0].url if self.images else None}


class PropertyImage(BaseModel):
    __tablename__ = "property_images"
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id", ondelete="CASCADE"), index=True)
    url: Mapped[str] = mapped_column(String(700))
    alt_text: Mapped[str | None] = mapped_column(String(220))
    position: Mapped[int] = mapped_column(default=0)
    property = relationship("Property", back_populates="images")


class Amenity(BaseModel):
    __tablename__ = "amenities"
    name: Mapped[str] = mapped_column(String(80), unique=True)
    slug: Mapped[str] = mapped_column(String(90), unique=True)
    properties = relationship("Property", secondary="property_amenities", back_populates="amenities")


class PropertyAmenity(BaseModel):
    __tablename__ = "property_amenities"
    __table_args__ = (UniqueConstraint("property_id", "amenity_id"),)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id", ondelete="CASCADE"))
    amenity_id: Mapped[int] = mapped_column(ForeignKey("amenities.id", ondelete="CASCADE"))


class Favorite(BaseModel):
    __tablename__ = "favorites"
    __table_args__ = (UniqueConstraint("user_id", "property_id"),)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id", ondelete="CASCADE"), index=True)
