"""Test input validation and edge cases"""
from datetime import datetime, timedelta


def test_create_auction_end_before_start(client, organizer_token):
    start_time = datetime.utcnow() + timedelta(hours=2)
    end_time = datetime.utcnow() + timedelta(hours=1)

    response = client.post(
        "/api/v1/auctions/",
        json={
            "title": "Invalid Time Auction",
            "starting_price": 100.00,
            "bid_step": 10.00,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        },
        headers={"Authorization": f"Bearer {organizer_token}"}
    )
    assert response.status_code == 400
    assert "after start time" in response.json()["detail"]


def test_create_auction_negative_price(client, organizer_token):
    start_time = datetime.utcnow() + timedelta(hours=1)
    end_time = start_time + timedelta(hours=2)

    response = client.post(
        "/api/v1/auctions/",
        json={
            "title": "Negative Price",
            "starting_price": -100.00,
            "bid_step": 10.00,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        },
        headers={"Authorization": f"Bearer {organizer_token}"}
    )
    assert response.status_code == 422


def test_create_auction_zero_bid_step(client, organizer_token):
    start_time = datetime.utcnow() + timedelta(hours=1)
    end_time = start_time + timedelta(hours=2)

    response = client.post(
        "/api/v1/auctions/",
        json={
            "title": "Zero Bid Step",
            "starting_price": 100.00,
            "bid_step": 0.00,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        },
        headers={"Authorization": f"Bearer {organizer_token}"}
    )
    assert response.status_code == 422


def test_create_auction_missing_required_fields(client, organizer_token):
    response = client.post(
        "/api/v1/auctions/",
        json={
            "title": "Incomplete Auction"
        },
        headers={"Authorization": f"Bearer {organizer_token}"}
    )
    assert response.status_code == 422


def test_update_auction_invalid_end_time(client, db, organizer_user, organizer_token):
    from app.models.auction import Auction, AuctionStatus

    start_time = datetime.utcnow() + timedelta(hours=2)
    end_time = start_time + timedelta(hours=3)

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

    new_end_time = start_time - timedelta(hours=1)

    response = client.put(
        f"/api/v1/auctions/{auction.id}",
        json={"end_time": new_end_time.isoformat()},
        headers={"Authorization": f"Bearer {organizer_token}"}
    )
    assert response.status_code == 400


def test_place_bid_nonexistent_auction(client, participant_token):
    response = client.post(
        "/api/v1/auctions/99999/bids",
        json={
            "auction_id": 99999,
            "amount": 120.00
        },
        headers={"Authorization": f"Bearer {participant_token}"}
    )
    assert response.status_code == 404


def test_get_nonexistent_auction(client):
    response = client.get("/api/v1/auctions/99999")
    assert response.status_code == 404


def test_update_nonexistent_auction(client, organizer_token):
    response = client.put(
        "/api/v1/auctions/99999",
        json={"title": "Updated"},
        headers={"Authorization": f"Bearer {organizer_token}"}
    )
    assert response.status_code == 404


def test_delete_nonexistent_auction(client, organizer_token):
    response = client.delete(
        "/api/v1/auctions/99999",
        headers={"Authorization": f"Bearer {organizer_token}"}
    )
    assert response.status_code == 404


def test_delete_active_auction_fails(client, db, organizer_user, organizer_token):
    from app.models.auction import Auction, AuctionStatus

    start_time = datetime.utcnow() - timedelta(hours=1)
    end_time = start_time + timedelta(hours=2)

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

    response = client.delete(
        f"/api/v1/auctions/{auction.id}",
        headers={"Authorization": f"Bearer {organizer_token}"}
    )
    assert response.status_code == 400
    assert "draft" in response.json()["detail"]


def test_update_closed_auction_fails(client, db, organizer_user, organizer_token):
    from app.models.auction import Auction, AuctionStatus

    start_time = datetime.utcnow() - timedelta(hours=3)
    end_time = start_time + timedelta(hours=2)

    auction = Auction(
        title="Closed Auction",
        starting_price=100.00,
        current_price=100.00,
        bid_step=10.00,
        start_time=start_time,
        end_time=end_time,
        status=AuctionStatus.closed,
        organizer_id=organizer_user.id
    )
    db.add(auction)
    db.commit()
    db.refresh(auction)

    response = client.put(
        f"/api/v1/auctions/{auction.id}",
        json={"title": "Updated"},
        headers={"Authorization": f"Bearer {organizer_token}"}
    )
    assert response.status_code == 400
    assert "closed" in response.json()["detail"]


def test_auction_listing_with_filters(client, db, organizer_user, organizer_token):
    from app.models.auction import Auction, AuctionStatus

    start_time = datetime.utcnow() + timedelta(hours=1)
    end_time = start_time + timedelta(hours=2)

    auction1 = Auction(
        title="Electronics Auction",
        category="electronics",
        starting_price=100.00,
        current_price=100.00,
        bid_step=10.00,
        start_time=start_time,
        end_time=end_time,
        status=AuctionStatus.active,
        organizer_id=organizer_user.id
    )
    auction2 = Auction(
        title="Art Auction",
        category="art",
        starting_price=200.00,
        current_price=200.00,
        bid_step=20.00,
        start_time=start_time,
        end_time=end_time,
        status=AuctionStatus.draft,
        organizer_id=organizer_user.id
    )
    db.add(auction1)
    db.add(auction2)
    db.commit()

    response = client.get("/api/v1/auctions/?category=electronics")
    assert response.status_code == 200
    data = response.json()
    assert all(auction["category"] == "electronics" for auction in data)


def test_auction_search_functionality(client, db, organizer_user, organizer_token):
    from app.models.auction import Auction, AuctionStatus

    start_time = datetime.utcnow() + timedelta(hours=1)
    end_time = start_time + timedelta(hours=2)

    auction = Auction(
        title="Unique Searchable Title",
        description="Special description",
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

    response = client.get("/api/v1/auctions/?search=Searchable")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert any("Searchable" in a["title"] for a in data)
