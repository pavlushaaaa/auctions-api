from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, Boolean, Text
from app.db.base import Base
from datetime import datetime
import enum


class NotificationType(str, enum.Enum):
    outbid = "outbid"
    won = "won"
    auction_ended = "auction_ended"
    payment_required = "payment_required"
    payment_received = "payment_received"


class NotificationChannel(str, enum.Enum):
    email = "email"
    telegram = "telegram"
    websocket = "websocket"


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    auction_id = Column(Integer, ForeignKey("auctions.id"), nullable=True)
    notification_type = Column(Enum(NotificationType), nullable=False)
    channel = Column(Enum(NotificationChannel), nullable=False)
    subject = Column(String, nullable=True)
    message = Column(Text, nullable=False)
    sent = Column(Boolean, default=False)
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
