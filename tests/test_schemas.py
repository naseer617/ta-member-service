import pytest
from pydantic import ValidationError
from app.schemas import MemberCreate

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
