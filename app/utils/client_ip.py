from ipaddress import ip_address

from fastapi import Request


def get_client_ip(request: Request) -> str:
    """Read the address overwritten by the trusted reverse proxy, never an XFF chain."""
    candidates = [request.headers.get("x-real-ip"), request.client.host if request.client else None]
    for candidate in candidates:
        try:
            return str(ip_address(str(candidate or "").strip()))
        except ValueError:
            continue
    return "unknown"
