#!/usr/bin/env python3
import argparse
import ipaddress
import subprocess
import tempfile
import urllib.request


def fetch_networks(url: str, version: int) -> list[str]:
    request = urllib.request.Request(url, headers={"User-Agent": "sym-security-firewall/1.0"})
    with urllib.request.urlopen(request, timeout=15) as response:
        return [
            str(ipaddress.ip_network(line.strip()))
            for line in response.read().decode().splitlines()
            if line.strip() and ipaddress.ip_network(line.strip()).version == version
        ]


def parse_networks(values: list[str], version: int) -> list[str]:
    networks = [
        str(ipaddress.ip_network(value.strip())) for item in values for value in item.split(",") if value.strip()
    ]
    if not networks or any(ipaddress.ip_network(network).version != version for network in networks):
        raise ValueError(f"at least one IPv{version} administrator SSH CIDR is required")
    return networks


def render(ssh_v4: list[str], ssh_v6: list[str], cf_v4: list[str], cf_v6: list[str]) -> str:
    return f"""table inet sym_filter {{
    set cf4 {{ type ipv4_addr; flags interval; elements = {{ {', '.join(cf_v4)} }} }}
    set cf6 {{ type ipv6_addr; flags interval; elements = {{ {', '.join(cf_v6)} }} }}
    set ssh4 {{ type ipv4_addr; flags interval; elements = {{ {', '.join(ssh_v4)} }} }}
    set ssh6 {{ type ipv6_addr; flags interval; elements = {{ {', '.join(ssh_v6)} }} }}
    chain web_ingress {{
        type filter hook prerouting priority raw; policy accept;
        fib daddr type local tcp dport {{ 80, 443 }} ip saddr @cf4 accept
        fib daddr type local tcp dport {{ 80, 443 }} ip6 saddr @cf6 accept
        fib daddr type local tcp dport {{ 80, 443 }} drop
    }}
    chain input {{
        type filter hook input priority 0; policy drop;
        ct state established,related accept
        iifname lo accept
        ip protocol icmp accept
        ip6 nexthdr ipv6-icmp accept
        tcp dport {{ 80, 443 }} ip saddr @cf4 accept
        tcp dport {{ 80, 443 }} ip6 saddr @cf6 accept
        tcp dport 22 ip saddr @ssh4 accept
        tcp dport 22 ip6 saddr @ssh6 accept
    }}
}}"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Render the SYM origin firewall; dry-run unless --apply is supplied.")
    parser.add_argument("--ssh-ipv4", action="append", required=True)
    parser.add_argument("--ssh-ipv6", action="append", default=[])
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    ssh_v4 = parse_networks(args.ssh_ipv4, 4)
    ssh_v6 = parse_networks(args.ssh_ipv6, 6) if args.ssh_ipv6 else ["::1/128"]
    rules = render(
        ssh_v4,
        ssh_v6,
        fetch_networks("https://www.cloudflare.com/ips-v4", 4),
        fetch_networks("https://www.cloudflare.com/ips-v6", 6),
    )
    if not args.apply:
        print(rules)
        return
    if subprocess.run(["nft", "list", "table", "inet", "sym_filter"], capture_output=True).returncode == 0:
        raise RuntimeError("inet sym_filter already exists; inspect it before replacing rules")
    with tempfile.NamedTemporaryFile("w", suffix=".nft") as rules_file:
        rules_file.write(rules)
        rules_file.flush()
        subprocess.run(["nft", "-c", "-f", rules_file.name], check=True)
        subprocess.run(["nft", "-f", rules_file.name], check=True)


if __name__ == "__main__":
    main()
