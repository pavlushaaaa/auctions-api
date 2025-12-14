"""Test Pydantic schemas and validation"""
import pytest
from datetime import datetime, timedelta


def test_user_create_schema():
    from app.schemas.user import UserCreate
    from app.models.user import UserRole

    user_data = UserCreate(
        email="test@example.com",
        password="password123",
        role=UserRole.participant,
        full_name="Test User"
    )

    assert user_data.email == "test@example.com"
    assert user_data.password == "password123"
    assert user_data.role == UserRole.participant


def test_user_create_schema_invalid_email():
    from app.schemas.user import UserCreate
    from app.models.user import UserRole
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        UserCreate(
            email="invalid-email",
            password="password123",
            role=UserRole.participant
        )


def test_auction_create_schema():
    from app.schemas.auction import AuctionCreate

    start_time = datetime.utcnow() + timedelta(hours=1)
    end_time = start_time + timedelta(hours=2)

    auction_data = AuctionCreate(
        title="Test Auction",
        description="Description",
        starting_price=100.0,
        bid_step=10.0,
        start_time=start_time,
        end_time=end_time
    )

    assert auction_data.title == "Test Auction"
    assert auction_data.starting_price == 100.0


def test_bid_create_schema():
    from app.schemas.bid import BidCreate

    bid_data = BidCreate(
        auction_id=1,
        amount=150.0
    )

    assert bid_data.auction_id == 1
    assert bid_data.amount == 150.0


def test_bid_create_schema_negative_amount():
    from app.schemas.bid import BidCreate
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        BidCreate(
            auction_id=1,
            amount=-50.0
        )


def test_auction_update_schema():
    from app.schemas.auction import AuctionUpdate

    update_data = AuctionUpdate(
        title="Updated Title",
        description="Updated Description"
    )

    assert update_data.title == "Updated Title"
    assert update_data.description == "Updated Description"


def test_user_response_schema():
    from app.schemas.user import UserResponse
    from app.models.user import UserRole
    from datetime import datetime

    user_response = UserResponse(
        id=1,
        email="test@example.com",
        role=UserRole.participant,
        full_name="Test User",
        is_blocked=False,
        created_at=datetime.utcnow()
    )

    assert user_response.id == 1
    assert user_response.email == "test@example.com"


def test_token_schema():
    from app.schemas.user import Token

    token = Token(
        access_token="sample_token_here",
        token_type="bearer"
    )

    assert token.access_token == "sample_token_here"
    assert token.token_type == "bearer"
