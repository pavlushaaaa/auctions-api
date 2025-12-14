"""Test role-based permissions and access control"""
from datetime import datetime, timedelta


def test_participant_cannot_create_auction(client, participant_token):
    start_time = datetime.utcnow() + timedelta(hours=1)
    end_time = start_time + timedelta(hours=2)

    response = client.post(
        "/api/v1/auctions/",
        json={
            "title": "Forbidden Auction",
            "starting_price": 100.00,
            "bid_step": 10.00,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        },
        headers={"Authorization": f"Bearer {participant_token}"}
    )
    assert response.status_code == 403


def test_participant_cannot_update_auction(client, db, organizer_user, participant_token):
    from app.models.auction import Auction, AuctionStatus

    start_time = datetime.utcnow() + timedelta(hours=1)
    end_time = start_time + timedelta(hours=2)

    auction = Auction(
        title="Test Auction",
        starting_price=100.00,
        current_price=100.00,
        bid_step=10.00,
        start_time=start_time,
        end_time=end_time,
        status=AuctionStatus.draft,
        organizer_id=organizer_user.id
    )
    db.add(auction)
    db.commit()
    db.refresh(auction)

    response = client.put(
        f"/api/v1/auctions/{auction.id}",
        json={"title": "Hacked Title"},
        headers={"Authorization": f"Bearer {participant_token}"}
    )
    assert response.status_code == 403


def test_participant_cannot_delete_auction(client, db, organizer_user, participant_token):
    from app.models.auction import Auction, AuctionStatus

    start_time = datetime.utcnow() + timedelta(hours=1)
    end_time = start_time + timedelta(hours=2)

    auction = Auction(
        title="Test Auction",
        starting_price=100.00,
        current_price=100.00,
        bid_step=10.00,
        start_time=start_time,
        end_time=end_time,
        status=AuctionStatus.draft,
        organizer_id=organizer_user.id
    )
    db.add(auction)
    db.commit()
    db.refresh(auction)

    response = client.delete(
        f"/api/v1/auctions/{auction.id}",
        headers={"Authorization": f"Bearer {participant_token}"}
    )
    assert response.status_code == 403


def test_organizer_cannot_update_other_organizer_auction(client, db, organizer_user):
    from app.models.auction import Auction, AuctionStatus
    from app.models.user import User, UserRole
    from app.core.security import get_password_hash, create_access_token

    organizer2 = User(
        email="organizer2@test.com",
        hashed_password=get_password_hash("password123"),
        role=UserRole.organizer,
        full_name="Organizer 2"
    )
    db.add(organizer2)
    db.commit()
    db.refresh(organizer2)

    organizer2_token = create_access_token(data={"sub": organizer2.email, "role": organizer2.role})

    start_time = datetime.utcnow() + timedelta(hours=1)
    end_time = start_time + timedelta(hours=2)

    auction = Auction(
        title="Test Auction",
        starting_price=100.00,
        current_price=100.00,
        bid_step=10.00,
        start_time=start_time,
        end_time=end_time,
        status=AuctionStatus.draft,
        organizer_id=organizer_user.id
    )
    db.add(auction)
    db.commit()
    db.refresh(auction)

    response = client.put(
        f"/api/v1/auctions/{auction.id}",
        json={"title": "Hacked Title"},
        headers={"Authorization": f"Bearer {organizer2_token}"}
    )
    assert response.status_code == 403


def test_admin_can_update_any_auction(client, db, organizer_user, admin_token):
    from app.models.auction import Auction, AuctionStatus

    start_time = datetime.utcnow() + timedelta(hours=1)
    end_time = start_time + timedelta(hours=2)

    auction = Auction(
        title="Test Auction",
        starting_price=100.00,
        current_price=100.00,
        bid_step=10.00,
        start_time=start_time,
        end_time=end_time,
        status=AuctionStatus.draft,
        organizer_id=organizer_user.id
    )
    db.add(auction)
    db.commit()
    db.refresh(auction)

    response = client.put(
        f"/api/v1/auctions/{auction.id}",
        json={"title": "Admin Updated"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Admin Updated"


def test_admin_can_delete_any_auction(client, db, organizer_user, admin_token):
    from app.models.auction import Auction, AuctionStatus

    start_time = datetime.utcnow() + timedelta(hours=1)
    end_time = start_time + timedelta(hours=2)

    auction = Auction(
        title="Test Auction",
        starting_price=100.00,
        current_price=100.00,
        bid_step=10.00,
        start_time=start_time,
        end_time=end_time,
        status=AuctionStatus.draft,
        organizer_id=organizer_user.id
    )
    db.add(auction)
    db.commit()
    db.refresh(auction)

    response = client.delete(
        f"/api/v1/auctions/{auction.id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 204


def test_participant_cannot_access_event_logs(client, participant_token):
    response = client.get(
        "/api/v1/event-logs",
        headers={"Authorization": f"Bearer {participant_token}"}
    )
    assert response.status_code == 403


def test_participant_cannot_access_user_info(client, participant_user, participant_token):
    response = client.get(
        f"/api/v1/users/{participant_user.id}",
        headers={"Authorization": f"Bearer {participant_token}"}
    )
    assert response.status_code == 403


def test_organizer_cannot_access_event_logs(client, organizer_token):
    response = client.get(
        "/api/v1/event-logs",
        headers={"Authorization": f"Bearer {organizer_token}"}
    )
    assert response.status_code == 403
