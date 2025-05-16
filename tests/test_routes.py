import pytest
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from fastapi import HTTPException
from unittest.mock import patch, AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from shared.db.connection import get_session
from app.models import MemberDB

# Helper class to track async function calls
class AsyncFunctionTracker:
    def __init__(self, func):
        self.func = func
        self.called = False
        self.call_count = 0

    async def __call__(self, *args, **kwargs):
        self.called = True
        self.call_count += 1
        return await self.func(*args, **kwargs)

@pytest.mark.asyncio
async def test_create_and_get_member(async_client):
    # Create
    response = await async_client.post("/members", json={
        "first_name": "Test",
        "last_name": "User",
        "login": "testuser",
        "avatar_url": None,
        "followers": 10,
        "following": 5,
        "title": "Dev",
        "email": "test@example.com"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["login"] == "testuser"

    # Get
    response = await async_client.get("/members")
    assert response.status_code == 200
    members = response.json()
    assert isinstance(members, list)
    assert any(m["login"] == "testuser" for m in members)

@pytest.mark.asyncio
async def test_create_duplicate_member(async_client):
    # Create first member
    await async_client.post("/members", json={
        "first_name": "Test",
        "last_name": "User",
        "login": "testuser",
        "email": "test@example.com"
    })

    # Try to create member with same login
    response = await async_client.post("/members", json={
        "first_name": "Another",
        "last_name": "User",
        "login": "testuser",  # Same login
        "email": "another@example.com"
    })
    assert response.status_code == 400
    assert response.json()["detail"] == "Login already exists"

    # Try to create member with same email
    response = await async_client.post("/members", json={
        "first_name": "Another",
        "last_name": "User",
        "login": "anotheruser",
        "email": "test@example.com"  # Same email
    })
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already exists"

@pytest.mark.asyncio
async def test_create_member_database_error(async_client, app):
    # Create a mock session with all necessary methods
    mock_session = AsyncMock(spec=AsyncSession)

    # Set up the mock methods
    mock_session.add = MagicMock()  # Use MagicMock for synchronous add
    mock_session.commit = AsyncMock(side_effect=SQLAlchemyError("Database error"))
    mock_session.rollback = AsyncMock()
    mock_session.refresh = AsyncMock()

    # Override the get_session dependency
    async def get_mock_session():
        yield mock_session

    app.dependency_overrides[get_session] = get_mock_session

    try:
        response = await async_client.post("/members", json={
            "first_name": "Test",
            "last_name": "User",
            "login": "testuser",
            "email": "test@example.com"
        })
        assert response.status_code == 400
        assert response.json()["detail"] == "Database error"

        # Verify that rollback was called
        mock_session.rollback.assert_awaited_once()
    finally:
        app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_create_member_integrity_error(async_client, app):
    # Create a mock session
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.add = MagicMock()

    # Test login key violation with exact error message format
    mock_session.commit = AsyncMock(side_effect=IntegrityError(
        statement="INSERT INTO members",
        params={},
        orig="duplicate key value violates unique constraint members_login_key"
    ))
    mock_session.rollback = AsyncMock()

    async def get_mock_session():
        yield mock_session

    app.dependency_overrides[get_session] = get_mock_session

    try:
        response = await async_client.post("/members", json={
            "first_name": "Test",
            "last_name": "User",
            "login": "testuser",
            "email": "test@example.com"
        })
        assert response.status_code == 400
        assert response.json()["detail"] == "Login already exists"
        mock_session.rollback.assert_awaited_once()
    finally:
        app.dependency_overrides.clear()

    # Reset mocks for email test
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.add = MagicMock()

    # Test email key violation with exact error message format
    mock_session.commit = AsyncMock(side_effect=IntegrityError(
        statement="INSERT INTO members",
        params={},
        orig="duplicate key value violates unique constraint members_email_key"
    ))
    mock_session.rollback = AsyncMock()

    app.dependency_overrides[get_session] = get_mock_session

    try:
        response = await async_client.post("/members", json={
            "first_name": "Test",
            "last_name": "User",
            "login": "anotheruser",
            "email": "test@example.com"
        })
        assert response.status_code == 400
        assert response.json()["detail"] == "Email already exists"
        mock_session.rollback.assert_awaited_once()
    finally:
        app.dependency_overrides.clear()

    # Test with different error message format for login
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock(side_effect=IntegrityError(
        statement="INSERT INTO members",
        params={},
        orig="duplicate key value violates unique constraint \"members_login_key\""
    ))
    mock_session.rollback = AsyncMock()

    app.dependency_overrides[get_session] = get_mock_session

    try:
        response = await async_client.post("/members", json={
            "first_name": "Test",
            "last_name": "User",
            "login": "testuser",
            "email": "test@example.com"
        })
        assert response.status_code == 400
        assert response.json()["detail"] == "Login already exists"
        mock_session.rollback.assert_awaited_once()
    finally:
        app.dependency_overrides.clear()

    # Test with different error message format for email
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock(side_effect=IntegrityError(
        statement="INSERT INTO members",
        params={},
        orig="duplicate key value violates unique constraint \"members_email_key\""
    ))
    mock_session.rollback = AsyncMock()

    app.dependency_overrides[get_session] = get_mock_session

    try:
        response = await async_client.post("/members", json={
            "first_name": "Test",
            "last_name": "User",
            "login": "anotheruser",
            "email": "test@example.com"
        })
        assert response.status_code == 400
        assert response.json()["detail"] == "Email already exists"
        mock_session.rollback.assert_awaited_once()
    finally:
        app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_get_members_database_error(async_client, app):
    # Create a mock session
    mock_session = AsyncMock(spec=AsyncSession)

    # Set up the mock execute method to raise SQLAlchemyError
    mock_session.execute = AsyncMock(side_effect=SQLAlchemyError("Database error"))

    # Override the get_session dependency
    async def get_mock_session():
        yield mock_session

    app.dependency_overrides[get_session] = get_mock_session

    try:
        response = await async_client.get("/members")
        assert response.status_code == 500
        assert response.json()["detail"] == "Failed to fetch members"
    finally:
        app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_soft_delete_members(async_client):
    # Create a member first
    await async_client.post("/members", json={
        "first_name": "Test",
        "last_name": "User",
        "login": "testuser",
        "email": "test@example.com"
    })

    # Soft delete all members
    response = await async_client.delete("/members")
    assert response.status_code == 200
    assert response.json()["message"] == "Members soft deleted"

    # Verify member is not returned in get
    response = await async_client.get("/members")
    assert response.status_code == 200
    members = response.json()
    assert len(members) == 0  # Member should be soft deleted

@pytest.mark.asyncio
async def test_soft_delete_members_database_error(async_client, app):
    # Create a mock session
    mock_session = AsyncMock(spec=AsyncSession)

    # Set up the mock methods
    mock_session.execute = AsyncMock(side_effect=SQLAlchemyError("Database error"))
    mock_session.rollback = AsyncMock()

    # Override the get_session dependency
    async def get_mock_session():
        yield mock_session

    app.dependency_overrides[get_session] = get_mock_session

    try:
        response = await async_client.delete("/members")
        assert response.status_code == 500
        assert response.json()["detail"] == "Failed to delete members"

        # Verify that rollback was called
        mock_session.rollback.assert_awaited_once()
    finally:
        app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_create_member_generic_integrity_error(async_client, app):
    # Create a mock session
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.add = MagicMock()

    # Test generic integrity error (not login or email)
    mock_session.commit = AsyncMock(side_effect=IntegrityError(
        statement="INSERT INTO members",
        params={},
        orig="some other constraint violation"
    ))
    mock_session.rollback = AsyncMock()

    async def get_mock_session():
        yield mock_session

    app.dependency_overrides[get_session] = get_mock_session

    try:
        response = await async_client.post("/members", json={
            "first_name": "Test",
            "last_name": "User",
            "login": "testuser",
            "email": "test@example.com"
        })
        assert response.status_code == 400
        assert response.json()["detail"] == "Database error"
        mock_session.rollback.assert_awaited_once()
    finally:
        app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_get_members_generic_error(async_client, app):
    # Create a mock session
    mock_session = AsyncMock(spec=AsyncSession)

    # Test generic exception (not SQLAlchemyError)
    mock_session.execute = AsyncMock(side_effect=Exception("Some other error"))

    async def get_mock_session():
        yield mock_session

    app.dependency_overrides[get_session] = get_mock_session

    try:
        response = await async_client.get("/members")
        assert response.status_code == 500
        assert response.json()["detail"] == "Failed to fetch members"
    finally:
        app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_soft_delete_members_generic_error(async_client, app):
    # Create a mock session
    mock_session = AsyncMock(spec=AsyncSession)

    # Test generic exception (not SQLAlchemyError)
    mock_session.execute = AsyncMock(side_effect=Exception("Some other error"))
    mock_session.rollback = AsyncMock()

    async def get_mock_session():
        yield mock_session

    app.dependency_overrides[get_session] = get_mock_session

    try:
        response = await async_client.delete("/members")
        assert response.status_code == 500
        assert response.json()["detail"] == "Failed to delete members"
        mock_session.rollback.assert_awaited_once()
    finally:
        app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_create_member_success(async_client, app):
    # Create a mock session that successfully adds and commits
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()

    # Create a member object that will be returned
    member = MemberDB(
        id=1,
        first_name="Test",
        last_name="User",
        login="testuser",
        email="test@example.com",
        avatar_url=None,
        followers=0,
        following=0,
        title=None,
        deleted=False
    )

    # Mock refresh to set the member object
    async def mock_refresh(member_obj):
        member_obj.id = 1
    mock_session.refresh = AsyncMock(side_effect=mock_refresh)

    async def get_mock_session():
        yield mock_session

    app.dependency_overrides[get_session] = get_mock_session

    try:
        response = await async_client.post("/members", json={
            "first_name": "Test",
            "last_name": "User",
            "login": "testuser",
            "email": "test@example.com"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["login"] == "testuser"
        mock_session.add.assert_called_once()
        mock_session.commit.assert_awaited_once()
        mock_session.refresh.assert_awaited_once()
    finally:
        app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_get_members_exception(async_client, app):
    # Create a mock session that raises an exception during execute
    mock_session = AsyncMock(spec=AsyncSession)

    # Mock the execute method to raise an exception that will be caught by the handler
    async def mock_execute(*args, **kwargs):
        raise RuntimeError("Database connection lost")
    mock_session.execute = AsyncMock(side_effect=mock_execute)

    async def get_mock_session():
        yield mock_session

    app.dependency_overrides[get_session] = get_mock_session

    try:
        response = await async_client.get("/members")
        assert response.status_code == 500
        assert response.json()["detail"] == "Failed to fetch members"
        mock_session.execute.assert_awaited_once()
    finally:
        app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_soft_delete_members_success(async_client, app):
    # Create a mock session that successfully executes and commits
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.execute = AsyncMock()
    mock_session.commit = AsyncMock()

    async def get_mock_session():
        yield mock_session

    app.dependency_overrides[get_session] = get_mock_session

    try:
        response = await async_client.delete("/members")
        assert response.status_code == 200
        assert response.json()["message"] == "Members soft deleted"
        mock_session.execute.assert_awaited_once()
        mock_session.commit.assert_awaited_once()
    finally:
        app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_soft_delete_single_member(async_client):
    # Create a member first
    response = await async_client.post("/members", json={
        "first_name": "Test",
        "last_name": "User",
        "login": "testuser",
        "email": "test@example.com"
    })
    assert response.status_code == 200
    member_id = response.json()["id"]

    # Delete the member
    response = await async_client.delete(f"/members/{member_id}")
    assert response.status_code == 200
    assert response.json()["message"] == f"Member {member_id} soft deleted"

    # Verify member is not in get response
    response = await async_client.get("/members")
    assert response.status_code == 200
    members = response.json()
    assert not any(m["id"] == member_id for m in members)

@pytest.mark.asyncio
async def test_soft_delete_single_member_not_found(async_client):
    # Try to delete non-existent member
    response = await async_client.delete("/members/99999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Member not found"

@pytest.mark.asyncio
async def test_soft_delete_single_member_database_error(async_client, app):
    # Create a mock session
    mock_session = AsyncMock(spec=AsyncSession)
    mock_session.execute = AsyncMock(side_effect=SQLAlchemyError("Database error"))
    mock_session.rollback = AsyncMock()

    async def get_mock_session():
        yield mock_session

    app.dependency_overrides[get_session] = get_mock_session

    try:
        response = await async_client.delete("/members/1")
        assert response.status_code == 500
        assert response.json()["detail"] == "Failed to delete member"
        mock_session.rollback.assert_awaited_once()
    finally:
        app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_soft_delete_single_member_already_deleted(async_client):
    # Create a member first
    response = await async_client.post("/members", json={
        "first_name": "Test",
        "last_name": "User",
        "login": "testuser",
        "email": "test@example.com"
    })
    assert response.status_code == 200
    member_id = response.json()["id"]

    # Delete the member first time
    response = await async_client.delete(f"/members/{member_id}")
    assert response.status_code == 200

    # Try to delete the same member again
    response = await async_client.delete(f"/members/{member_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Member not found"

@pytest.mark.asyncio
async def test_soft_delete_single_member_generic_error(async_client, app):
    # Create a mock session
    mock_session = AsyncMock(spec=AsyncSession)

    # Test generic exception (not SQLAlchemyError)
    mock_session.execute = AsyncMock(side_effect=Exception("Some other error"))
    mock_session.rollback = AsyncMock()

    async def get_mock_session():
        yield mock_session

    app.dependency_overrides[get_session] = get_mock_session

    try:
        response = await async_client.delete("/members/1")
        assert response.status_code == 500
        assert response.json()["detail"] == "Failed to delete member"
        mock_session.rollback.assert_awaited_once()
    finally:
        app.dependency_overrides.clear()
