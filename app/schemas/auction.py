from pydantic import BaseModel, Field
from datetime import datetime
from decimal import Decimal
from app.models.auction import AuctionStatus, AuctionType


class AuctionBase(BaseModel):
    title: str
    description: str | None = None
    category: str | None = None
    starting_price: Decimal = Field(gt=0)
    bid_step: Decimal = Field(gt=0)
    start_time: datetime
    end_time: datetime


class AuctionCreate(AuctionBase):
    auction_type: AuctionType = AuctionType.english
    buyout_price: Decimal | None = None
    reserve_price: Decimal | None = None
    commission_rate: Decimal = Decimal("0.00")
    anti_snipe_enabled: bool = False
    anti_snipe_seconds: int = 60
    anti_snipe_extension: int = 60
    anti_snipe_max_extensions: int = 3


class AuctionUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    category: str | None = None
    starting_price: Decimal | None = Field(None, gt=0)
    bid_step: Decimal | None = Field(None, gt=0)
    start_time: datetime | None = None
    end_time: datetime | None = None
    status: AuctionStatus | None = None
    buyout_price: Decimal | None = None
    reserve_price: Decimal | None = None


class AuctionResponse(AuctionBase):
    id: int
    current_price: Decimal
    status: AuctionStatus
    auction_type: AuctionType
    organizer_id: int
    winner_id: int | None = None
    buyout_price: Decimal | None = None
    reserve_price: Decimal | None = None
    commission_rate: Decimal
    anti_snipe_enabled: bool
    anti_snipe_seconds: int
    anti_snipe_extension: int
    anti_snipe_max_extensions: int
    anti_snipe_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AuctionListResponse(BaseModel):
    id: int
    title: str
    category: str | None = None
    current_price: Decimal
    status: AuctionStatus
    auction_type: AuctionType
    start_time: datetime
    end_time: datetime

    class Config:
        from_attributes = True
