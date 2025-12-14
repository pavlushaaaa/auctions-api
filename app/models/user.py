from sqlalchemy import Column, Integer, String, Enum, Boolean, DateTime
from app.db.base import Base
from datetime import datetime
import enum


class UserRole(str, enum.Enum):
    participant = "participant"
    organizer = "organizer"
    admin = "admin"
    moderator = "moderator"
    superadmin = "superadmin"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.participant, nullable=False)
    full_name = Column(String, nullable=True)
    is_blocked = Column(Boolean, default=False)
    telegram_id = Column(String, nullable=True, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
