import pytest
from pydantic import SecretStr

from app.core.config import Settings
from app.core.crypto import SecretCipher, SecretConfigurationError

KEY = "ogrz8oyDPaFypfjqBufjOyBlUlCG3Sl9I2eB0xLu8_E="
OTHER_KEY = "R3bjiwtE37tyr1mvVpVrt0aHezZWkOO8UpH3zZOQj-U="


def make_settings(key: str | None) -> Settings:
    return Settings(
        database_url="sqlite+aiosqlite:///:memory:",
        pingwake_encryption_key=SecretStr(key) if key is not None else None,
    )


def test_cipher_round_trip() -> None:
    cipher = SecretCipher(make_settings(KEY))
    encrypted = cipher.encrypt_json({"apikey": "secret"})

    assert "secret" not in encrypted
    assert cipher.decrypt_json(encrypted) == {"apikey": "secret"}


def test_cipher_requires_key() -> None:
    cipher = SecretCipher(make_settings(None))

    with pytest.raises(SecretConfigurationError):
        cipher.encrypt_json({"apikey": "secret"})


def test_cipher_rejects_different_key() -> None:
    encrypted = SecretCipher(make_settings(KEY)).encrypt_json({"apikey": "secret"})

    with pytest.raises(SecretConfigurationError):
        SecretCipher(make_settings(OTHER_KEY)).decrypt_json(encrypted)
