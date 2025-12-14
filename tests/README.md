# Test Suite Documentation

## Overview
Comprehensive test suite for the Auction API with **95+ test cases** covering all endpoints, models, security, and integration scenarios.

## Test Structure

```
tests/
├── conftest.py                 # Test fixtures and configuration
├── test_auth.py                # Authentication tests (13 tests)
├── test_auctions.py            # Auction CRUD and flow tests (19 tests)
├── test_bids.py                # Bidding functionality tests (17 tests)
├── test_admin.py               # Admin endpoints tests (8 tests)
├── test_permissions.py         # Role-based access control (11 tests)
├── test_validation.py          # Input validation tests (15 tests)
├── test_models.py              # Database models tests (7 tests)
├── test_schemas.py             # Pydantic schemas tests (10 tests)
├── test_security.py            # Security utilities tests (8 tests)
└── test_integration.py         # End-to-end integration tests (7 tests)
```

## Test Categories

### 1. Authentication Tests (`test_auth.py`)
- User registration (participant, organizer, admin)
- Login functionality
- Token validation
- Current user retrieval
- Invalid credentials handling
- Email validation
- Password strength validation

### 2. Auction Tests (`test_auctions.py`)
- Auction CRUD operations
- Auction listing and filtering
- Search functionality
- Close auction endpoint
- Get winner endpoint
- Event logs for auctions
- Authorization checks
- Time validation (start/end times)

### 3. Bid Tests (`test_bids.py`)
- Place bids on active auctions
- Bid amount validation
- Multiple bidders scenario
- Bid history retrieval
- User's bid history
- Auction status validation
- Time-based bid restrictions
- Organizer bid prevention

### 4. Admin Tests (`test_admin.py`)
- Get user by ID
- Event logs retrieval
- Log filtering (by event type, user, auction)
- Pagination
- Access control for admin endpoints

### 5. Permission Tests (`test_permissions.py`)
- Role-based access control
- Participant restrictions
- Organizer restrictions
- Admin privileges
- Cross-user access prevention
- Resource ownership validation

### 6. Validation Tests (`test_validation.py`)
- Input validation
- Edge cases
- Negative values
- Time range validation
- Required fields
- Business logic constraints
- Search and filter functionality

### 7. Model Tests (`test_models.py`)
- User model creation
- Auction model creation
- Bid model creation
- Event log model creation
- Enum validations
- Relationships

### 8. Schema Tests (`test_schemas.py`)
- Pydantic schema validation
- Field type validation
- Required/optional fields
- Email format validation
- Negative value prevention
- Data serialization

### 9. Security Tests (`test_security.py`)
- Password hashing
- Password verification
- Token creation
- Token decoding
- Token expiration
- Invalid token handling
- Hash uniqueness

### 10. Integration Tests (`test_integration.py`)
- Complete auction flow (create → bid → close → winner)
- Multi-bidder scenarios
- User registration flow
- Admin workflow
- Event log generation
- End-to-end scenarios

## Running Tests

### Run all tests
```bash
pytest tests/
```

### Run with coverage
```bash
pytest tests/ --cov=app --cov-report=html
```

### Run specific test file
```bash
pytest tests/test_auctions.py -v
```

### Run specific test
```bash
pytest tests/test_auctions.py::test_create_auction -v
```

### Run with output
```bash
pytest tests/ -v -s
```

## Test Coverage

The test suite covers:
- ✅ All 16 API endpoints
- ✅ Authentication & Authorization
- ✅ Role-based permissions (P/O/A)
- ✅ Input validation
- ✅ Business logic
- ✅ Error handling
- ✅ Database models
- ✅ Security functions
- ✅ Integration flows

## Fixtures

### User Fixtures
- `participant_user` - Participant role user
- `organizer_user` - Organizer role user
- `admin_user` - Admin role user

### Token Fixtures
- `participant_token` - JWT for participant
- `organizer_token` - JWT for organizer
- `admin_token` - JWT for admin

### Infrastructure Fixtures
- `client` - FastAPI test client
- `db` - Test database session

## Test Database

Tests use SQLite in-memory database:
- Isolated per test function
- Automatic setup and teardown
- No interference between tests
- Fast execution

## Assertions

Tests verify:
- HTTP status codes
- Response data structure
- Response data values
- Error messages
- Database state
- Business rule enforcement
- Access control

## Continuous Integration

Tests are designed to run in CI/CD pipelines:
- No external dependencies
- Fast execution (< 30 seconds)
- Deterministic results
- Clear failure messages
