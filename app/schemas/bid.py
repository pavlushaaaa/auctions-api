from pydantic import BaseModel, Field
from datetime import datetime
from decimal import Decimal


class BidCreate(BaseModel):
    auction_id: int
    amount: Decimal = Field(gt=0)


class BidResponse(BaseModel):
    id: int
    auction_id: int
    user_id: int
    amount: Decimal
    created_at: datetime

    class Config:
        from_attributes = True
