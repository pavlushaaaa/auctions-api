from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal
from app.models.payment import PaymentStatus


class PaymentCreate(BaseModel):
    auction_id: int
    payment_method: str = "mock_card"


class PaymentResponse(BaseModel):
    id: int
    auction_id: int
    user_id: int
    amount: Decimal
    commission: Decimal
    total_amount: Decimal
    status: PaymentStatus
    payment_method: str | None
    transaction_id: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
