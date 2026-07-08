import json
from typing import Any

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import Settings, get_settings


class SecretConfigurationError(RuntimeError):
    """Raised when encrypted target configuration cannot be stored or read."""


class SecretCipher:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def encrypt_json(self, value: Any) -> str:
        cipher = self._get_cipher()
        serialized = json.dumps(
            value,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        return cipher.encrypt(serialized).decode("ascii")

    def decrypt_json(self, value: str) -> Any:
        cipher = self._get_cipher()
        try:
            decrypted = cipher.decrypt(value.encode("ascii"))
            return json.loads(decrypted.decode("utf-8"))
        except (InvalidToken, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise SecretConfigurationError(
                "Encrypted request configuration could not be decrypted. "
                "Check PINGWAKE_ENCRYPTION_KEY."
            ) from exc

    def _get_cipher(self) -> Fernet:
        secret = self.settings.pingwake_encryption_key
        if secret is None or not secret.get_secret_value().strip():
            raise SecretConfigurationError(
                "PINGWAKE_ENCRYPTION_KEY is required for custom headers or request bodies."
            )

        try:
            return Fernet(secret.get_secret_value().strip().encode("ascii"))
        except (ValueError, UnicodeEncodeError) as exc:
            raise SecretConfigurationError(
                "PINGWAKE_ENCRYPTION_KEY must be a valid Fernet key."
            ) from exc
