def test_register_user(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@test.com",
            "password": "password123",
            "role": "participant",
            "full_name": "New User"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@test.com"
    assert data["role"] == "participant"
    assert "id" in data


def test_register_duplicate_email(client, participant_user):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": participant_user.email,
            "password": "password123",
            "role": "participant"
        }
    )
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


def test_login(client, participant_user):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": participant_user.email,
            "password": "password123"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client, participant_user):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": participant_user.email,
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 401


def test_get_current_user(client, participant_user, participant_token):
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {participant_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == participant_user.email
    assert data["id"] == participant_user.id


def test_get_current_user_unauthorized(client):
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 403


def test_register_organizer(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "organizer2@test.com",
            "password": "password123",
            "role": "organizer",
            "full_name": "Test Organizer 2"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "organizer2@test.com"
    assert data["role"] == "organizer"


def test_register_without_full_name(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "minimal@test.com",
            "password": "password123",
            "role": "participant"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "minimal@test.com"


def test_login_nonexistent_user(client):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "nonexistent@test.com",
            "password": "password123"
        }
    )
    assert response.status_code == 401


def test_register_invalid_email(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "not-an-email",
            "password": "password123",
            "role": "participant"
        }
    )
    assert response.status_code == 422


def test_register_short_password(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@test.com",
            "password": "123",
            "role": "participant"
        }
    )
    assert response.status_code in [400, 422]


def test_get_current_user_with_invalid_token(client):
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid_token_here"}
    )
    assert response.status_code == 401
