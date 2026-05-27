from app.core.security import hash_password, verify_password


def test_password_hash_roundtrip():
    password = "admin123"
    hashed = hash_password(password)

    assert hashed.startswith("pbkdf2_sha256$")
    assert verify_password(password, hashed) is True
    assert verify_password("wrong", hashed) is False


def test_password_hash_supports_long_passwords_without_bcrypt_limit():
    password = "x" * 200
    hashed = hash_password(password)

    assert verify_password(password, hashed) is True
