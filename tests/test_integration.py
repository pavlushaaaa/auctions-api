"""Integration tests for complete user flows"""
from datetime import datetime, timedelta


def test_complete_auction_flow(client, db, organizer_user, participant_user, organizer_token, participant_token):
    """Test complete flow: create auction -> place bids -> close auction -> get winner"""
    from app.models.auction import Auction, AuctionStatus

    # 1. Organizer creates auction
    start_time = datetime.utcnow() - timedelta(hours=1)
    end_time = datetime.utcnow() + timedelta(hours=1)

    create_response = client.post(
        "/api/v1/auctions/",
        json={
            "title": "Integration Test Auction",
            "description": "Full flow test",
            "starting_price": 100.00,
            "bid_step": 10.00,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        },
        headers={"Authorization": f"Bearer {organizer_token}"}
    )
    assert create_response.status_code == 201
    auction_id = create_response.json()["id"]

    # 2. Activate auction
    auction = db.query(Auction).filter(Auction.id == auction_id).first()
    auction.status = AuctionStatus.active
    db.commit()

    # 3. Participant places bid
    bid_response = client.post(
        f"/api/v1/auctions/{auction_id}/bids",
        json={
            "auction_id": auction_id,
            "amount": 110.00
        },
        headers={"Authorization": f"Bearer {participant_token}"}
    )
    assert bid_response.status_code == 201

    # 4. Check auction updated price
    auction_response = client.get(f"/api/v1/auctions/{auction_id}")
    assert auction_response.status_code == 200
    assert float(auction_response.json()["current_price"]) == 110.00

    # 5. Close auction
    close_response = client.post(
        f"/api/v1/auctions/{auction_id}/close",
        headers={"Authorization": f"Bearer {organizer_token}"}
    )
    assert close_response.status_code == 200

    # 6. Get winner
    winner_response = client.get(f"/api/v1/auctions/{auction_id}/winner")
    assert winner_response.status_code == 200
    winner_data = winner_response.json()
    assert winner_data["winner"]["id"] == participant_user.id


def test_multi_bidder_auction_flow(client, db, organizer_user, participant_user, organizer_token, participant_token):
    """Test auction with multiple bidders"""
    from app.models.auction import Auction, AuctionStatus
    from app.models.user import User, UserRole
    from app.core.security import get_password_hash, create_access_token

    # Create second participant
    participant2 = User(
        email="participant2@integration.com",
        hashed_password=get_password_hash("password123"),
        role=UserRole.participant,
        full_name="Participant 2"
    )
    db.add(participant2)
    db.commit()
    db.refresh(participant2)

    participant2_token = create_access_token(data={"sub": participant2.email, "role": participant2.role})

    # Create active auction
    start_time = datetime.utcnow() - timedelta(hours=1)
    end_time = datetime.utcnow() + timedelta(hours=1)

    auction = Auction(
        title="Multi Bidder Auction",
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

    # First participant bids
    client.post(
        f"/api/v1/auctions/{auction.id}/bids",
        json={"auction_id": auction.id, "amount": 110.00},
        headers={"Authorization": f"Bearer {participant_token}"}
    )

    # Second participant bids higher
    client.post(
        f"/api/v1/auctions/{auction.id}/bids",
        json={"auction_id": auction.id, "amount": 130.00},
        headers={"Authorization": f"Bearer {participant2_token}"}
    )

    # First participant bids even higher
    client.post(
        f"/api/v1/auctions/{auction.id}/bids",
        json={"auction_id": auction.id, "amount": 150.00},
        headers={"Authorization": f"Bearer {participant_token}"}
    )

    # Check bids
    bids_response = client.get(f"/api/v1/auctions/{auction.id}/bids")
    assert bids_response.status_code == 200
    bids = bids_response.json()
    assert len(bids) == 3

    # Close and verify winner
    client.post(
        f"/api/v1/auctions/{auction.id}/close",
        headers={"Authorization": f"Bearer {organizer_token}"}
    )

    winner_response = client.get(f"/api/v1/auctions/{auction.id}/winner")
    winner_data = winner_response.json()
    assert winner_data["winner"]["id"] == participant_user.id
    assert winner_data["winning_bid"] == "150.0"


def test_user_registration_and_auction_participation(client, db):
    """Test new user registration and immediate participation"""

    # 1. Register new user
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@integration.com",
            "password": "password123",
            "role": "participant",
            "full_name": "New User"
        }
    )
    assert register_response.status_code == 201

    # 2. Login
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "newuser@integration.com",
            "password": "password123"
        }
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    # 3. Get user info
    me_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert me_response.status_code == 200
    user_data = me_response.json()
    assert user_data["email"] == "newuser@integration.com"


def test_admin_workflow(client, db, organizer_user, participant_user, admin_token):
    """Test admin viewing logs and user information"""

    # 1. Admin views all event logs
    logs_response = client.get(
        "/api/v1/event-logs",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert logs_response.status_code == 200

    # 2. Admin gets specific user info
    user_response = client.get(
        f"/api/v1/users/{participant_user.id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert user_response.status_code == 200
    user_data = user_response.json()
    assert user_data["id"] == participant_user.id


def test_auction_lifecycle_with_events(client, db, organizer_user, participant_user, organizer_token, participant_token, admin_token):
    """Test complete auction lifecycle generates correct event logs"""
    from app.models.auction import Auction, AuctionStatus

    # Create auction
    start_time = datetime.utcnow() - timedelta(hours=1)
    end_time = datetime.utcnow() + timedelta(hours=1)

    create_response = client.post(
        "/api/v1/auctions/",
        json={
            "title": "Event Log Test Auction",
            "starting_price": 100.00,
            "bid_step": 10.00,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        },
        headers={"Authorization": f"Bearer {organizer_token}"}
    )
    auction_id = create_response.json()["id"]

    # Activate auction
    auction = db.query(Auction).filter(Auction.id == auction_id).first()
    auction.status = AuctionStatus.active
    db.commit()

    # Place bid
    client.post(
        f"/api/v1/auctions/{auction_id}/bids",
        json={"auction_id": auction_id, "amount": 110.00},
        headers={"Authorization": f"Bearer {participant_token}"}
    )

    # Update auction
    client.put(
        f"/api/v1/auctions/{auction_id}",
        json={"description": "Updated description"},
        headers={"Authorization": f"Bearer {organizer_token}"}
    )

    # Close auction
    client.post(
        f"/api/v1/auctions/{auction_id}/close",
        headers={"Authorization": f"Bearer {organizer_token}"}
    )

    # Check event logs for this auction
    logs_response = client.get(
        f"/api/v1/auctions/{auction_id}/event-logs",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert logs_response.status_code == 200
    logs = logs_response.json()
    assert len(logs) >= 3

    event_types = [log["event_type"] for log in logs]
    assert "auction_created" in event_types
    assert "bid_placed" in event_types
    assert "auction_closed" in event_types
