import pytest
from pydantic import ValidationError
from datetime import datetime, timezone
from app.schemas import MemberCreate, Member, MemberOut

def test_member_create_validation():
    with pytest.raises(ValidationError):
        MemberCreate(first_name="A", last_name="B", login="ab", email="invalid")

    # valid
    m = MemberCreate(
        first_name="Alice",
        last_name="Smith",
        login="alice01",
        email="alice@example.com"
    )
    assert m.login == "alice01"

def test_member_schema():
    now = datetime.now(timezone.utc)
    member = Member(
        id=1,
        first_name="Alice",
        last_name="Smith",
        login="alice01",
        email="alice@example.com",
        avatar_url=None,
        followers=0,
        following=0,
        title=None,
        created_at=now,
        updated_at=now,
        deleted=False
    )
    assert member.id == 1
    assert member.login == "alice01"
    assert member.created_at == now
    assert member.updated_at == now
    assert member.deleted is False

def test_member_out_schema():
    now = datetime.now(timezone.utc)
    member = MemberOut(
        id=1,
        first_name="Alice",
        last_name="Smith",
        login="alice01",
        email="alice@example.com",
        avatar_url=None,
        followers=0,
        following=0,
        title=None,
        created_at=now,
        updated_at=now
    )
    assert member.id == 1
    assert member.login == "alice01"
    assert member.created_at == now
    assert member.updated_at == now

def test_member_schema_validation():
    with pytest.raises(ValidationError):
        Member(
            id=1,
            first_name="Alice",
            last_name="Smith",
            login="alice01",
            email="invalid",
            created_at=None,  # Should be datetime
            updated_at=None,  # Should be datetime
            deleted=None      # Should be boolean
        )
