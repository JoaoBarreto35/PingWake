import asyncio
import ipaddress
import socket
from urllib.parse import urlsplit

from app.core.config import Settings


class UnsafeTargetError(ValueError):
    """Raised when a target URL points to a forbidden destination."""


def _is_forbidden_ip(address: str) -> bool:
    ip = ipaddress.ip_address(address)
    return any(
        (
            ip.is_private,
            ip.is_loopback,
            ip.is_link_local,
            ip.is_multicast,
            ip.is_reserved,
            ip.is_unspecified,
        )
    )


def validate_target_url_static(url: str, settings: Settings) -> None:
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"}:
        raise UnsafeTargetError("Only HTTP and HTTPS targets are supported.")
    if parsed.username or parsed.password:
        raise UnsafeTargetError("Credentials in target URLs are not allowed.")
    if not parsed.hostname:
        raise UnsafeTargetError("Target URL must contain a hostname.")

    hostname = parsed.hostname.lower()
    if settings.allowed_hosts and hostname not in settings.allowed_hosts:
        raise UnsafeTargetError("Target hostname is not in the configured allowlist.")

    if hostname == "localhost" and not settings.allow_private_targets:
        raise UnsafeTargetError("Local targets are blocked.")

    try:
        is_forbidden = _is_forbidden_ip(hostname)
    except ValueError:
        return

    if is_forbidden and not settings.allow_private_targets:
        raise UnsafeTargetError("Private or reserved target addresses are blocked.")


async def validate_target_url_runtime(url: str, settings: Settings) -> None:
    validate_target_url_static(url, settings)
    hostname = urlsplit(url).hostname
    if hostname is None or settings.allow_private_targets:
        return

    try:
        ipaddress.ip_address(hostname)
        return
    except ValueError:
        pass

    loop = asyncio.get_running_loop()
    try:
        records = await loop.getaddrinfo(
            hostname,
            None,
            family=socket.AF_UNSPEC,
            type=socket.SOCK_STREAM,
        )
    except socket.gaierror as exc:
        raise UnsafeTargetError("Target hostname could not be resolved.") from exc

    addresses = {record[4][0] for record in records}
    if not addresses:
        raise UnsafeTargetError("Target hostname returned no addresses.")
    if any(_is_forbidden_ip(address) for address in addresses):
        raise UnsafeTargetError("Target resolves to a private or reserved address.")
