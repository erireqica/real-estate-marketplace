import enum
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import BaseModel


class UserRole(str, enum.Enum):
    USER = "user"
    AGENT = "agent"
    ADMIN = "admin"


class User(BaseModel):
    __tablename__ = "users"
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    first_name: Mapped[str] = mapped_column(String(80))
    last_name: Mapped[str] = mapped_column(String(80))
    phone: Mapped[str | None] = mapped_column(String(40))
    avatar_url: Mapped[str | None] = mapped_column(String(500))
    agency_name: Mapped[str | None] = mapped_column(String(160))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.USER, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    properties = relationship("Property", back_populates="agent", cascade="all, delete-orphan")

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {"id": self.id, "email": self.email, "firstName": self.first_name, "lastName": self.last_name, "fullName": self.full_name, "phone": self.phone, "avatarUrl": self.avatar_url, "agencyName": self.agency_name, "role": self.role.value}

