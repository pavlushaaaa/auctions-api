def test_get_user_by_id(client, participant_user, admin_token):
    response = client.get(
        f"/api/v1/users/{participant_user.id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == participant_user.id
    assert data["email"] == participant_user.email
    assert data["role"] == "participant"


def test_get_user_unauthorized(client, participant_user, participant_token):
    response = client.get(
        f"/api/v1/users/{participant_user.id}",
        headers={"Authorization": f"Bearer {participant_token}"}
    )
    assert response.status_code == 403


def test_get_user_not_found(client, admin_token):
    response = client.get(
        "/api/v1/users/99999",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 404


def test_get_event_logs(client, db, admin_user, admin_token):
    from app.models.event_log import EventLog

    event_log = EventLog(
        event_type="test_event",
        user_id=admin_user.id,
        details={"test": "data"}
    )
    db.add(event_log)
    db.commit()

    response = client.get(
        "/api/v1/event-logs",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(log["event_type"] == "test_event" for log in data)


def test_get_event_logs_unauthorized(client, participant_token):
    response = client.get(
        "/api/v1/event-logs",
        headers={"Authorization": f"Bearer {participant_token}"}
    )
    assert response.status_code == 403


def test_get_event_logs_filtered_by_event_type(client, db, admin_user, admin_token):
    from app.models.event_log import EventLog

    event_log1 = EventLog(
        event_type="bid_placed",
        user_id=admin_user.id,
        details={"amount": "100"}
    )
    event_log2 = EventLog(
        event_type="auction_created",
        user_id=admin_user.id,
        details={"title": "Test"}
    )
    db.add(event_log1)
    db.add(event_log2)
    db.commit()

    response = client.get(
        "/api/v1/event-logs?event_type=bid_placed",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert all(log["event_type"] == "bid_placed" for log in data)


def test_get_event_logs_filtered_by_user(client, db, admin_user, participant_user, admin_token):
    from app.models.event_log import EventLog

    event_log1 = EventLog(
        event_type="test_event",
        user_id=admin_user.id,
        details={"test": "admin"}
    )
    event_log2 = EventLog(
        event_type="test_event",
        user_id=participant_user.id,
        details={"test": "participant"}
    )
    db.add(event_log1)
    db.add(event_log2)
    db.commit()

    response = client.get(
        f"/api/v1/event-logs?user_id={participant_user.id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert all(log["user_id"] == participant_user.id for log in data)


def test_get_event_logs_with_pagination(client, db, admin_user, admin_token):
    from app.models.event_log import EventLog

    for i in range(10):
        event_log = EventLog(
            event_type=f"test_event_{i}",
            user_id=admin_user.id,
            details={"index": i}
        )
        db.add(event_log)
    db.commit()

    response = client.get(
        "/api/v1/event-logs?limit=5",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 5
