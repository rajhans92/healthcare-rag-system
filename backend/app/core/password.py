"""
Password utility functions.

This module is responsible for:
- Hashing plain text passwords.
- Verifying hashed passwords.
"""

from pwdlib import PasswordHash

# Create a password hasher using the recommended algorithm (Argon2)
password_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """
    Hash a plain text password.

    Args:
        password: Plain text password.

    Returns:
        Hashed password.
    """
    return password_hasher.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    """
    Verify a plain text password against a hashed password.

    Args:
        plain_password: Password entered by the user.
        hashed_password: Password stored in the database.

    Returns:
        True if the password matches, otherwise False.
    """
    return password_hasher.verify(
        plain_password,
        hashed_password,
    )