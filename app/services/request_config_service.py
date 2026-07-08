from typing import cast

from pydantic import JsonValue

from app.core.config import Settings
from app.core.crypto import SecretCipher
from app.db.models.monitoring_target import MonitoringTarget


class RequestConfigService:
    def __init__(
        self,
        settings: Settings | None = None,
        cipher: SecretCipher | None = None,
    ) -> None:
        self.cipher = cipher or SecretCipher(settings)

    def set_headers(
        self,
        target: MonitoringTarget,
        headers: dict[str, str] | None,
    ) -> None:
        if not headers:
            target.request_headers_encrypted = None
            target.has_custom_headers = False
            return
        target.request_headers_encrypted = self.cipher.encrypt_json(headers)
        target.has_custom_headers = True

    def set_body(self, target: MonitoringTarget, body: JsonValue | None) -> None:
        if body is None:
            target.request_body_encrypted = None
            target.has_request_body = False
            return
        target.request_body_encrypted = self.cipher.encrypt_json(body)
        target.has_request_body = True

    def get_headers(self, target: MonitoringTarget) -> dict[str, str]:
        if not target.has_custom_headers:
            return {}
        if target.request_headers_encrypted is None:
            raise ValueError("Target is marked with custom headers but encrypted data is missing.")

        value = self.cipher.decrypt_json(target.request_headers_encrypted)
        if not isinstance(value, dict) or not all(
            isinstance(key, str) and isinstance(item, str) for key, item in value.items()
        ):
            raise ValueError("Encrypted target headers have an invalid format.")
        return value

    def get_body(self, target: MonitoringTarget) -> JsonValue | None:
        if not target.has_request_body:
            return None
        if target.request_body_encrypted is None:
            raise ValueError("Target is marked with a request body but encrypted data is missing.")
        return cast(JsonValue, self.cipher.decrypt_json(target.request_body_encrypted))
