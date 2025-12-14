import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.base import Base, get_db
from app.core.security import create_access_token
from app.models.user import User, UserRole

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def participant_user(db):
    from app.core.security import get_password_hash
    user = User(
        email="participant@test.com",
        hashed_password=get_password_hash("password123"),
        role=UserRole.participant,
        full_name="Test Participant"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def organizer_user(db):
    from app.core.security import get_password_hash
    user = User(
        email="organizer@test.com",
        hashed_password=get_password_hash("password123"),
        role=UserRole.organizer,
        full_name="Test Organizer"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def admin_user(db):
    from app.core.security import get_password_hash
    user = User(
        email="admin@test.com",
        hashed_password=get_password_hash("password123"),
        role=UserRole.admin,
        full_name="Test Admin"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def participant_token(participant_user):
    return create_access_token(data={"sub": participant_user.email, "role": participant_user.role})


@pytest.fixture
def organizer_token(organizer_user):
    return create_access_token(data={"sub": organizer_user.email, "role": organizer_user.role})


@pytest.fixture
def admin_token(admin_user):
    return create_access_token(data={"sub": admin_user.email, "role": admin_user.role})
