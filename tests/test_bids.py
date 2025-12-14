from datetime import datetime, timedelta
from app.models.auction import AuctionStatus


def test_place_bid(client, db, organizer_user, participant_user, participant_token):
    from app.models.auction import Auction

    start_time = datetime.utcnow() - timedelta(hours=1)
    end_time = datetime.utcnow() + timedelta(hours=1)

    auction = Auction(
        title="Active Auction",
        description="Test",
        starting_price=100.00,
        current_price=100.00,
        bid_step=10.00,
        start_time=start_time,
        end_time=end_time,
        status=AuctionStatus.active,
        organizer_id=organizer_user.id
    )
    db.add(auction)
    db.commit()
    db.refresh(auction)

    response = client.post(
        f"/api/v1/auctions/{auction.id}/bids",
        json={
            "auction_id": auction.id,
            "amount": 120.00
        },
        headers={"Authorization": f"Bearer {participant_token}"}
    )
    assert response.status_code == 201
    data = response.json()
    assert float(data["amount"]) == 120.00
    assert data["auction_id"] == auction.id


def test_place_bid_too_low(client, db, organizer_user, participant_user, participant_token):
    from app.models.auction import Auction

    start_time = datetime.utcnow() - timedelta(hours=1)
    end_time = datetime.utcnow() + timedelta(hours=1)

    auction = Auction(
        title="Active Auction",
        starting_price=100.00,
        current_price=100.00,
        bid_step=10.00,
        start_time=start_time,
        end_time=end_time,
        status=AuctionStatus.active,
        organizer_id=organizer_user.id
    )
    db.add(auction)
    db.commit()
    db.refresh(auction)

    response = client.post(
        f"/api/v1/auctions/{auction.id}/bids",
        json={
            "auction_id": auction.id,
            "amount": 105.00
        },
        headers={"Authorization": f"Bearer {participant_token}"}
    )
    assert response.status_code == 400
    assert "at least" in response.json()["detail"]


def test_place_bid_on_inactive_auction(client, db, organizer_user, participant_user, participant_token):
    from app.models.auction import Auction

    start_time = datetime.utcnow() + timedelta(hours=1)
    end_time = start_time + timedelta(hours=2)

    auction = Auction(
        title="Draft Auction",
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

    response = client.post(
        f"/api/v1/auctions/{auction.id}/bids",
        json={
            "auction_id": auction.id,
            "amount": 120.00
        },
        headers={"Authorization": f"Bearer {participant_token}"}
    )
    assert response.status_code == 400
    assert "not active" in response.json()["detail"]


def test_organizer_cannot_bid(client, db, organizer_user, organizer_token):
    from app.models.auction import Auction

    start_time = datetime.utcnow() - timedelta(hours=1)
    end_time = datetime.utcnow() + timedelta(hours=1)

    auction = Auction(
        title="Active Auction",
        starting_price=100.00,
        current_price=100.00,
        bid_step=10.00,
        start_time=start_time,
        end_time=end_time,
        status=AuctionStatus.active,
        organizer_id=organizer_user.id
    )
    db.add(auction)
    db.commit()
    db.refresh(auction)

    response = client.post(
        f"/api/v1/auctions/{auction.id}/bids",
        json={
            "auction_id": auction.id,
            "amount": 120.00
        },
        headers={"Authorization": f"Bearer {organizer_token}"}
    )
    assert response.status_code == 400
    assert "cannot bid on their own" in response.json()["detail"]


def test_get_auction_bids(client, db, organizer_user, participant_user, participant_token):
    from app.models.auction import Auction
    from app.models.bid import Bid

    start_time = datetime.utcnow() - timedelta(hours=1)
    end_time = datetime.utcnow() + timedelta(hours=1)

    auction = Auction(
        title="Active Auction",
        starting_price=100.00,
        current_price=100.00,
        bid_step=10.00,
        start_time=start_time,
        end_time=end_time,
        status=AuctionStatus.active,
        organizer_id=organizer_user.id
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

    response = client.get(f"/api/v1/auctions/{auction.id}/bids")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert float(data[0]["amount"]) == 120.00


def test_get_my_bids(client, db, organizer_user, participant_user, participant_token):
    from app.models.auction import Auction
    from app.models.bid import Bid

    start_time = datetime.utcnow() - timedelta(hours=1)
    end_time = datetime.utcnow() + timedelta(hours=1)

    auction = Auction(
        title="Active Auction",
        starting_price=100.00,
        current_price=100.00,
        bid_step=10.00,
        start_time=start_time,
        end_time=end_time,
        status=AuctionStatus.active,
        organizer_id=organizer_user.id
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

    response = client.get(
        f"/api/v1/users/{participant_user.id}/bids",
        headers={"Authorization": f"Bearer {participant_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert float(data[0]["amount"]) == 120.00


def test_get_other_user_bids_forbidden(client, db, organizer_user, participant_user, organizer_token, participant_token):
    from app.models.auction import Auction
    from app.models.bid import Bid

    start_time = datetime.utcnow() - timedelta(hours=1)
    end_time = datetime.utcnow() + timedelta(hours=1)

    auction = Auction(
        title="Active Auction",
        starting_price=100.00,
        current_price=100.00,
        bid_step=10.00,
        start_time=start_time,
        end_time=end_time,
        status=AuctionStatus.active,
        organizer_id=organizer_user.id
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

    response = client.get(
        f"/api/v1/users/{participant_user.id}/bids",
        headers={"Authorization": f"Bearer {organizer_token}"}
    )
    assert response.status_code == 403


def test_bid_auction_id_mismatch(client, db, organizer_user, participant_user, participant_token):
    from app.models.auction import Auction

    start_time = datetime.utcnow() - timedelta(hours=1)
    end_time = datetime.utcnow() + timedelta(hours=1)

    auction = Auction(
        title="Active Auction",
        starting_price=100.00,
        current_price=100.00,
        bid_step=10.00,
        start_time=start_time,
        end_time=end_time,
        status=AuctionStatus.active,
        organizer_id=organizer_user.id
    )
    db.add(auction)
    db.commit()
    db.refresh(auction)

    response = client.post(
        f"/api/v1/auctions/{auction.id}/bids",
        json={
            "auction_id": 99999,
            "amount": 120.00
        },
        headers={"Authorization": f"Bearer {participant_token}"}
    )
    assert response.status_code == 400
    assert "mismatch" in response.json()["detail"]


def test_bid_on_auction_not_started(client, db, organizer_user, participant_user, participant_token):
    from app.models.auction import Auction

    start_time = datetime.utcnow() + timedelta(hours=1)
    end_time = datetime.utcnow() + timedelta(hours=3)

    auction = Auction(
        title="Future Auction",
        starting_price=100.00,
        current_price=100.00,
        bid_step=10.00,
        start_time=start_time,
        end_time=end_time,
        status=AuctionStatus.active,
        organizer_id=organizer_user.id
    )
    db.add(auction)
    db.commit()
    db.refresh(auction)

    response = client.post(
        f"/api/v1/auctions/{auction.id}/bids",
        json={
            "auction_id": auction.id,
            "amount": 120.00
        },
        headers={"Authorization": f"Bearer {participant_token}"}
    )
    assert response.status_code == 400
    assert "not started" in response.json()["detail"]


def test_bid_on_ended_auction(client, db, organizer_user, participant_user, participant_token):
    from app.models.auction import Auction

    start_time = datetime.utcnow() - timedelta(hours=3)
    end_time = datetime.utcnow() - timedelta(hours=1)

    auction = Auction(
        title="Ended Auction",
        starting_price=100.00,
        current_price=100.00,
        bid_step=10.00,
        start_time=start_time,
        end_time=end_time,
        status=AuctionStatus.active,
        organizer_id=organizer_user.id
    )
    db.add(auction)
    db.commit()
    db.refresh(auction)

    response = client.post(
        f"/api/v1/auctions/{auction.id}/bids",
        json={
            "auction_id": auction.id,
            "amount": 120.00
        },
        headers={"Authorization": f"Bearer {participant_token}"}
    )
    assert response.status_code == 400
    assert "ended" in response.json()["detail"]


def test_multiple_bids_update_current_price(client, db, organizer_user, participant_user, participant_token):
    from app.models.auction import Auction
    from app.models.user import User, UserRole
    from app.core.security import get_password_hash, create_access_token

    start_time = datetime.utcnow() - timedelta(hours=1)
    end_time = datetime.utcnow() + timedelta(hours=1)

    auction = Auction(
        title="Active Auction",
        starting_price=100.00,
        current_price=100.00,
        bid_step=10.00,
        start_time=start_time,
        end_time=end_time,
        status=AuctionStatus.active,
        organizer_id=organizer_user.id
    )
    db.add(auction)
    db.commit()
    db.refresh(auction)

    client.post(
        f"/api/v1/auctions/{auction.id}/bids",
        json={
            "auction_id": auction.id,
            "amount": 110.00
        },
        headers={"Authorization": f"Bearer {participant_token}"}
    )

    participant2 = User(
        email="participant2@test.com",
        hashed_password=get_password_hash("password123"),
        role=UserRole.participant,
        full_name="Participant 2"
    )
    db.add(participant2)
    db.commit()
    db.refresh(participant2)

    participant2_token = create_access_token(data={"sub": participant2.email, "role": participant2.role})

    response = client.post(
        f"/api/v1/auctions/{auction.id}/bids",
        json={
            "auction_id": auction.id,
            "amount": 130.00
        },
        headers={"Authorization": f"Bearer {participant2_token}"}
    )
    assert response.status_code == 201

    get_response = client.get(f"/api/v1/auctions/{auction.id}")
    assert get_response.status_code == 200
    auction_data = get_response.json()
    assert float(auction_data["current_price"]) == 130.00


def test_get_bids_for_nonexistent_auction(client):
    response = client.get("/api/v1/auctions/99999/bids")
    assert response.status_code == 404


def test_place_bid_unauthorized(client, db, organizer_user):
    from app.models.auction import Auction

    start_time = datetime.utcnow() - timedelta(hours=1)
    end_time = datetime.utcnow() + timedelta(hours=1)

    auction = Auction(
        title="Active Auction",
        starting_price=100.00,
        current_price=100.00,
        bid_step=10.00,
        start_time=start_time,
        end_time=end_time,
        status=AuctionStatus.active,
        organizer_id=organizer_user.id
    )
    db.add(auction)
    db.commit()
    db.refresh(auction)

    response = client.post(
        f"/api/v1/auctions/{auction.id}/bids",
        json={
            "auction_id": auction.id,
            "amount": 120.00
        }
    )
    assert response.status_code == 403
