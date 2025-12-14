"""Test models and database schemas"""
from datetime import datetime, timedelta


def test_user_model_creation(db):
    from app.models.user import User, UserRole
    from app.core.security import get_password_hash

    user = User(
        email="model@test.com",
        hashed_password=get_password_hash("password"),
        role=UserRole.participant,
        full_name="Model Test"
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    assert user.id is not None
    assert user.email == "model@test.com"
    assert user.role == UserRole.participant


def test_auction_model_creation(db, organizer_user):
    from app.models.auction import Auction, AuctionStatus

    start_time = datetime.utcnow()
    end_time = start_time + timedelta(hours=2)

    auction = Auction(
        title="Model Test Auction",
        description="Test Description",
        starting_price=100.00,
        current_price=100.00,
        bid_step=10.00,
        start_time=start_time,
        end_time=end_time,
        organizer_id=organizer_user.id,
        status=AuctionStatus.draft
    )
    db.add(auction)
    db.commit()
    db.refresh(auction)

    assert auction.id is not None
    assert auction.title == "Model Test Auction"
    assert auction.status == AuctionStatus.draft


def test_bid_model_creation(db, organizer_user, participant_user):
    from app.models.auction import Auction, AuctionStatus
    from app.models.bid import Bid

    start_time = datetime.utcnow()
    end_time = start_time + timedelta(hours=2)

    auction = Auction(
        title="Test Auction",
        starting_price=100.00,
        current_price=100.00,
        bid_step=10.00,
        start_time=start_time,
        end_time=end_time,
        organizer_id=organizer_user.id,
        status=AuctionStatus.active
    )
    db.add(auction)
    db.commit()
    db.refresh(auction)

    bid = Bid(
        auction_id=auction.id,
        user_id=participant_user.id,
        amount=120.00
    )
    db.add(bid)
    db.commit()
    db.refresh(bid)

    assert bid.id is not None
    assert bid.amount == 120.00
    assert bid.auction_id == auction.id


def test_event_log_model_creation(db, participant_user):
    from app.models.event_log import EventLog

    event = EventLog(
        event_type="test_event",
        user_id=participant_user.id,
        details={"key": "value"}
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    assert event.id is not None
    assert event.event_type == "test_event"
    assert event.details["key"] == "value"


def test_user_role_enum():
    from app.models.user import UserRole

    assert UserRole.participant.value == "participant"
    assert UserRole.organizer.value == "organizer"
    assert UserRole.admin.value == "admin"


def test_auction_status_enum():
    from app.models.auction import AuctionStatus

    assert AuctionStatus.draft.value == "draft"
    assert AuctionStatus.active.value == "active"
    assert AuctionStatus.closed.value == "closed"
