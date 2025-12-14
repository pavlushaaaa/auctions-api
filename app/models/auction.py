from sqlalchemy import Column, Integer, String, Numeric, DateTime, Enum, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.db.base import Base
from datetime import datetime
import enum


class AuctionStatus(str, enum.Enum):
    draft = "draft"
    active = "active"
    closed = "closed"
    frozen = "frozen"


class AuctionType(str, enum.Enum):
    english = "english"
    dutch = "dutch"
    blind = "blind"


class Auction(Base):
    __tablename__ = "auctions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    category = Column(String, nullable=True, index=True)
    starting_price = Column(Numeric(10, 2), nullable=False)
    current_price = Column(Numeric(10, 2), nullable=False)
    bid_step = Column(Numeric(10, 2), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    status = Column(Enum(AuctionStatus), default=AuctionStatus.draft, nullable=False)
    auction_type = Column(Enum(AuctionType), default=AuctionType.english, nullable=False)
    organizer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    winner_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    buyout_price = Column(Numeric(10, 2), nullable=True)
    reserve_price = Column(Numeric(10, 2), nullable=True)
    commission_rate = Column(Numeric(5, 2), default=0.00)

    anti_snipe_enabled = Column(Boolean, default=False)
    anti_snipe_seconds = Column(Integer, default=60)
    anti_snipe_extension = Column(Integer, default=60)
    anti_snipe_max_extensions = Column(Integer, default=3)
    anti_snipe_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    organizer = relationship("User", foreign_keys=[organizer_id])
    winner = relationship("User", foreign_keys=[winner_id])
    bids = relationship("Bid", back_populates="auction")
