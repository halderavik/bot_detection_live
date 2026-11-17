"""
Data-centre IP detection.

Real respondents connect from homes, offices and mobile networks. Bot farms and
many VPNs run on cloud servers, whose providers publish their address ranges.
The ranges are downloaded in the background when the service starts and
refreshed daily; until they arrive (or if a download fails) no IP is flagged.
"""

import asyncio
import csv
import io
import ipaddress
import logging
from typing import Dict, List, Optional, Tuple

import httpx

logger = logging.getLogger(__name__)

# provider -> URL of its published ranges
SOURCES: Dict[str, str] = {
    "Amazon Web Services": "https://ip-ranges.amazonaws.com/ip-ranges.json",
    "Google Cloud": "https://www.gstatic.com/ipranges/cloud.json",
    "Oracle Cloud": "https://docs.oracle.com/iaas/tools/public_ip_ranges.json",
    "DigitalOcean": "https://digitalocean.com/geo/google.csv",
}
REFRESH_SECONDS = 24 * 3600

# IPv4 networks bucketed by first octet; IPv6 kept in one list
_V4: Dict[int, List[Tuple[ipaddress.IPv4Network, str]]] = {}
_V6: List[Tuple[ipaddress.IPv6Network, str]] = []
_loaded = 0


def _parse(provider: str, body: str) -> List[str]:
    """CIDR strings from one provider's published file."""
    if provider == "DigitalOcean":
        return [row[0] for row in csv.reader(io.StringIO(body)) if row and "/" in row[0]]
    import json

    data = json.loads(body)
    if provider == "Amazon Web Services":
        return [p["ip_prefix"] for p in data.get("prefixes", [])] + [
            p["ipv6_prefix"] for p in data.get("ipv6_prefixes", [])
        ]
    if provider == "Google Cloud":
        return [p.get("ipv4Prefix") or p.get("ipv6Prefix") for p in data.get("prefixes", []) if p.get("ipv4Prefix") or p.get("ipv6Prefix")]
    if provider == "Oracle Cloud":
        return [c["cidr"] for region in data.get("regions", []) for c in region.get("cidrs", [])]
    return []


def load(ranges: Dict[str, List[str]]) -> int:
    """Replace the known ranges. Returns how many networks were loaded."""
    global _V4, _V6, _loaded
    v4: Dict[int, List[Tuple[ipaddress.IPv4Network, str]]] = {}
    v6: List[Tuple[ipaddress.IPv6Network, str]] = []
    for provider, cidrs in ranges.items():
        for cidr in cidrs:
            try:
                network = ipaddress.ip_network(cidr, strict=False)
            except ValueError:
                continue
            if network.version == 4:
                first = int(network.network_address) >> 24
                last = int(network.broadcast_address) >> 24
                for octet in range(first, last + 1):
                    v4.setdefault(octet, []).append((network, provider))
            else:
                v6.append((network, provider))
    _V4, _V6 = v4, v6
    _loaded = sum(len(c) for c in ranges.values())
    return _loaded


def provider_for(ip: Optional[str]) -> Optional[str]:
    """The cloud provider that owns ``ip``, or None."""
    if not ip:
        return None
    try:
        address = ipaddress.ip_address(ip)
    except ValueError:
        return None
    if address.version == 4:
        candidates = _V4.get(int(address) >> 24, [])
    else:
        candidates = _V6
    for network, provider in candidates:
        if address in network:
            return provider
    return None


def loaded() -> int:
    """Number of networks currently known."""
    return _loaded


async def refresh() -> int:
    """Download every provider's ranges. Keeps the old ranges for any that fail."""
    ranges: Dict[str, List[str]] = {}
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as http:
        for provider, url in SOURCES.items():
            try:
                response = await http.get(url)
                response.raise_for_status()
                ranges[provider] = _parse(provider, response.text)
            except Exception as exc:  # noqa: BLE001 - one provider failing must not stop the others
                logger.warning(f"Data-centre ranges for {provider} not loaded: {exc}")
    if ranges:
        count = load(ranges)
        logger.info(f"Loaded {count} data-centre networks from {len(ranges)} providers")
    return _loaded


async def keep_fresh() -> None:
    """Background task: load now, then refresh daily."""
    while True:
        try:
            await refresh()
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"Data-centre range refresh failed: {exc}")
        await asyncio.sleep(REFRESH_SECONDS)
