#!/usr/bin/env python3
import fcntl
import ipaddress
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ENV_FILE = "/etc/fail2ban/cloudflare.env"
STATE_DIR = Path("/var/lib/fail2ban/sym-cloudflare")
STATE_FILE = STATE_DIR / "claims.json"
LOCK_FILE = STATE_DIR / "claims.lock"


def read_env() -> dict[str, str]:
    values = {}
    with open(ENV_FILE, encoding="utf-8") as env_file:
        for line in env_file:
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and "=" in stripped:
                key, value = stripped.split("=", 1)
                values[key.strip()] = value.strip()
    return values


def request(method: str, url: str, token: str, payload: dict | None = None) -> dict:
    body = json.dumps(payload).encode() if payload is not None else None
    api_request = urllib.request.Request(
        url,
        data=body,
        method=method,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(api_request, timeout=15) as response:
            result = json.load(response)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"Cloudflare API returned HTTP {exc.code}") from exc
    if not result.get("success"):
        raise RuntimeError("Cloudflare API rejected the request")
    return result


def load_claims() -> dict[str, dict[str, int]]:
    if not STATE_FILE.exists():
        return {}
    with open(STATE_FILE, encoding="utf-8") as state_file:
        claims = json.load(state_file)
    now = int(time.time())
    return {
        address: {jail: int(expires_at) for jail, expires_at in jails.items() if int(expires_at) > now}
        for address, jails in claims.items()
        if any(int(expires_at) > now for expires_at in jails.values())
    }


def save_claims(claims: dict[str, dict[str, int]]) -> None:
    temporary = STATE_FILE.with_suffix(".tmp")
    with open(temporary, "w", encoding="utf-8") as state_file:
        json.dump(claims, state_file, sort_keys=True)
    os.chmod(temporary, 0o600)
    os.replace(temporary, STATE_FILE)


def main() -> int:
    if len(sys.argv) not in {4, 5} or sys.argv[2] not in {"ban", "unban"}:
        print("usage: sym-cloudflare-ban <jail> <ban|unban> <ip> [seconds]", file=sys.stderr)
        return 2
    jail, operation, address = sys.argv[1:4]
    if operation == "ban" and len(sys.argv) != 5:
        raise ValueError("ban duration is required")
    ipaddress.ip_address(address)
    config = read_env()
    zone_id = config["CF_ZONE_ID"]
    token = config["CF_API_TOKEN"]
    marker = f"sym-fail2ban:{address}"
    endpoint = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/firewall/access_rules/rules"
    query = urllib.parse.urlencode({"configuration.target": "ip", "configuration.value": address, "per_page": 50})
    STATE_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(STATE_DIR, 0o700)
    with open(LOCK_FILE, "a+", encoding="utf-8") as lock_file:
        os.chmod(LOCK_FILE, 0o600)
        fcntl.flock(lock_file, fcntl.LOCK_EX)
        claims = load_claims()

        if operation == "ban":
            claims.setdefault(address, {})[jail] = int(time.time()) + max(1, int(sys.argv[4]))
        else:
            claims.get(address, {}).pop(jail, None)
            if address in claims and not claims[address]:
                claims.pop(address)

        rules = request("GET", f"{endpoint}?{query}", token).get("result") or []
        owned_rules = [rule for rule in rules if str(rule.get("notes") or "").startswith("sym-fail2ban:")]

        if operation == "ban":
            if not rules:
                request(
                    "POST",
                    endpoint,
                    token,
                    {"mode": "block", "configuration": {"target": "ip", "value": address}, "notes": marker},
                )
            save_claims(claims)
            return 0

        if claims.get(address):
            save_claims(claims)
            return 0
        for rule in owned_rules:
            request("DELETE", f"{endpoint}/{rule['id']}", token)
        save_claims(claims)
        return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (KeyError, OSError, ValueError, RuntimeError) as exc:
        print(f"sym-cloudflare-ban: {exc}", file=sys.stderr)
        raise SystemExit(1)
