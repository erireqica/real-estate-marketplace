from datetime import datetime, timezone
from sqlalchemy.orm import Mapped, mapped_column
from ..extensions import db


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), index=True)
    updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class BaseModel(db.Model, TimestampMixin):
    __abstract__ = True
    id: Mapped[int] = mapped_column(primary_key=True)

