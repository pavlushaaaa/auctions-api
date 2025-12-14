from datetime import datetime, timedelta


def test_create_auction(client, organizer_token):
    start_time = datetime.utcnow() + timedelta(hours=1)
    end_time = start_time + timedelta(hours=2)

    response = client.post(
        "/api/v1/auctions/",
        json={
            "title": "Test Auction",
            "description": "Test Description",
            "starting_price": 100.00,
            "bid_step": 10.00,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        },
        headers={"Authorization": f"Bearer {organizer_token}"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Auction"
    assert float(data["starting_price"]) == 100.00
    assert data["status"] == "draft"


def test_create_auction_participant_forbidden(client, participant_token):
    start_time = datetime.utcnow() + timedelta(hours=1)
    end_time = start_time + timedelta(hours=2)

    response = client.post(
        "/api/v1/auctions/",
        json={
            "title": "Test Auction",
            "starting_price": 100.00,
            "bid_step": 10.00,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        },
        headers={"Authorization": f"Bearer {participant_token}"}
    )
    assert response.status_code == 403


def test_list_auctions(client, organizer_token):
    start_time = datetime.utcnow() + timedelta(hours=1)
    end_time = start_time + timedelta(hours=2)

    client.post(
        "/api/v1/auctions/",
        json={
            "title": "Auction 1",
            "starting_price": 100.00,
            "bid_step": 10.00,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        },
        headers={"Authorization": f"Bearer {organizer_token}"}
    )

    response = client.get("/api/v1/auctions/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1


def test_get_auction(client, organizer_token):
    start_time = datetime.utcnow() + timedelta(hours=1)
    end_time = start_time + timedelta(hours=2)

    create_response = client.post(
        "/api/v1/auctions/",
        json={
            "title": "Test Auction",
            "starting_price": 100.00,
            "bid_step": 10.00,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        },
        headers={"Authorization": f"Bearer {organizer_token}"}
    )
    auction_id = create_response.json()["id"]

    response = client.get(f"/api/v1/auctions/{auction_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == auction_id
    assert data["title"] == "Test Auction"


def test_update_auction(client, organizer_token):
    start_time = datetime.utcnow() + timedelta(hours=1)
    end_time = start_time + timedelta(hours=2)

    create_response = client.post(
        "/api/v1/auctions/",
        json={
            "title": "Original Title",
            "starting_price": 100.00,
            "bid_step": 10.00,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        },
        headers={"Authorization": f"Bearer {organizer_token}"}
    )
    auction_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/auctions/{auction_id}",
        json={"title": "Updated Title"},
        headers={"Authorization": f"Bearer {organizer_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"


def test_delete_auction(client, organizer_token):
    start_time = datetime.utcnow() + timedelta(hours=1)
    end_time = start_time + timedelta(hours=2)

    create_response = client.post(
        "/api/v1/auctions/",
        json={
            "title": "To Delete",
            "starting_price": 100.00,
            "bid_step": 10.00,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        },
        headers={"Authorization": f"Bearer {organizer_token}"}
    )
    auction_id = create_response.json()["id"]

    response = client.delete(
        f"/api/v1/auctions/{auction_id}",
        headers={"Authorization": f"Bearer {organizer_token}"}
    )
    assert response.status_code == 204

    get_response = client.get(f"/api/v1/auctions/{auction_id}")
    assert get_response.status_code == 404


def test_close_auction(client, db, organizer_user, participant_user, organizer_token, participant_token):
    from app.models.auction import Auction, AuctionStatus
    from app.models.bid import Bid

    start_time = datetime.utcnow() - timedelta(hours=2)
    end_time = datetime.utcnow() - timedelta(hours=1)

    auction = Auction(
        title="Auction to Close",
        description="Test",
        starting_price=100.00,
        current_price=120.00,
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

    response = client.post(
        f"/api/v1/auctions/{auction.id}/close",
        headers={"Authorization": f"Bearer {organizer_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "closed"
    assert data["winner_id"] == participant_user.id


def test_close_auction_unauthorized(client, db, organizer_user, participant_user, participant_token):
    from app.models.auction import Auction, AuctionStatus

    start_time = datetime.utcnow() - timedelta(hours=2)
    end_time = datetime.utcnow() - timedelta(hours=1)

    auction = Auction(
        title="Auction to Close",
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
        f"/api/v1/auctions/{auction.id}/close",
        headers={"Authorization": f"Bearer {participant_token}"}
    )
    assert response.status_code == 403


def test_close_already_closed_auction(client, db, organizer_user, organizer_token):
    from app.models.auction import Auction, AuctionStatus

    start_time = datetime.utcnow() - timedelta(hours=2)
    end_time = datetime.utcnow() - timedelta(hours=1)

    auction = Auction(
        title="Already Closed",
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

    response = client.post(
        f"/api/v1/auctions/{auction.id}/close",
        headers={"Authorization": f"Bearer {organizer_token}"}
    )
    assert response.status_code == 400
    assert "already closed" in response.json()["detail"]


def test_get_auction_winner(client, db, organizer_user, participant_user):
    from app.models.auction import Auction, AuctionStatus

    start_time = datetime.utcnow() - timedelta(hours=2)
    end_time = datetime.utcnow() - timedelta(hours=1)

    auction = Auction(
        title="Closed Auction",
        starting_price=100.00,
        current_price=150.00,
        bid_step=10.00,
        start_time=start_time,
        end_time=end_time,
        status=AuctionStatus.closed,
        organizer_id=organizer_user.id,
        winner_id=participant_user.id
    )
    db.add(auction)
    db.commit()
    db.refresh(auction)

    response = client.get(f"/api/v1/auctions/{auction.id}/winner")
    assert response.status_code == 200
    data = response.json()
    assert data["auction_id"] == auction.id
    assert data["winner"]["id"] == participant_user.id
    assert data["winning_bid"] == "150.0"


def test_get_winner_auction_not_closed(client, db, organizer_user):
    from app.models.auction import Auction, AuctionStatus

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

    response = client.get(f"/api/v1/auctions/{auction.id}/winner")
    assert response.status_code == 400
    assert "not closed" in response.json()["detail"]


def test_get_winner_no_winner(client, db, organizer_user):
    from app.models.auction import Auction, AuctionStatus

    start_time = datetime.utcnow() - timedelta(hours=2)
    end_time = datetime.utcnow() - timedelta(hours=1)

    auction = Auction(
        title="Closed No Winner",
        starting_price=100.00,
        current_price=100.00,
        bid_step=10.00,
        start_time=start_time,
        end_time=end_time,
        status=AuctionStatus.closed,
        organizer_id=organizer_user.id,
        winner_id=None
    )
    db.add(auction)
    db.commit()
    db.refresh(auction)

    response = client.get(f"/api/v1/auctions/{auction.id}/winner")
    assert response.status_code == 200
    data = response.json()
    assert data["winner"] is None
    assert "No winner" in data["message"]


def test_get_auction_event_logs(client, db, organizer_user, admin_token):
    from app.models.auction import Auction, AuctionStatus
    from app.models.event_log import EventLog

    start_time = datetime.utcnow() - timedelta(hours=1)
    end_time = datetime.utcnow() + timedelta(hours=1)

    auction = Auction(
        title="Test Auction",
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

    event_log = EventLog(
        event_type="auction_created",
        user_id=organizer_user.id,
        auction_id=auction.id,
        details={"title": auction.title}
    )
    db.add(event_log)
    db.commit()

    response = client.get(
        f"/api/v1/auctions/{auction.id}/event-logs",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["event_type"] == "auction_created"
    assert data[0]["auction_id"] == auction.id


def test_get_auction_event_logs_unauthorized(client, db, organizer_user, participant_token):
    from app.models.auction import Auction, AuctionStatus

    start_time = datetime.utcnow() - timedelta(hours=1)
    end_time = datetime.utcnow() + timedelta(hours=1)

    auction = Auction(
        title="Test Auction",
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

    response = client.get(
        f"/api/v1/auctions/{auction.id}/event-logs",
        headers={"Authorization": f"Bearer {participant_token}"}
    )
    assert response.status_code == 403
