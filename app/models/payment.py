from sqlalchemy import Column, Integer, String, Numeric, DateTime, Enum, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.base import Base
from datetime import datetime
import enum


class PaymentStatus(str, enum.Enum):
    pending = "pending"
    held = "held"
    paid = "paid"
    refunded = "refunded"
    failed = "failed"


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    auction_id = Column(Integer, ForeignKey("auctions.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    commission = Column(Numeric(10, 2), default=0.00)
    total_amount = Column(Numeric(10, 2), nullable=False)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.pending, nullable=False)
    payment_method = Column(String, nullable=True)
    transaction_id = Column(String, nullable=True, unique=True)
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    auction = relationship("Auction")
    user = relationship("User")
