from uuid import uuid4

from app.core.jwt import (
    create_access_token,
    decode_token,
)


def test_create_access_token():

    token = create_access_token(
        user_id=uuid4(),
        email="test@test.com",
        role="PATIENT",
    )

    payload = decode_token(token)

    assert payload["email"] == "test@test.com"
    assert payload["role"] == "PATIENT"
    assert payload["type"] == "access"