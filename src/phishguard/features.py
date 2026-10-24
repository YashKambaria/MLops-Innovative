"""Safe, offline URL feature extraction.

This module parses URL strings only. It never opens sockets, resolves DNS, or
requests a page represented by a URL.
"""

from __future__ import annotations

import ipaddress
import math
import re
from urllib.parse import urlsplit

import pandas as pd

FEATURE_NAMES = [
    "url_length", "hostname_length", "path_length", "query_length",
    "num_dots", "num_hyphens", "num_digits", "num_special_chars",
    "num_subdomains", "has_ip_address", "has_https", "has_at_symbol",
    "has_punycode", "has_port", "has_query", "has_fragment",
    "entropy", "digit_ratio", "special_ratio", "path_depth",
]

_SPECIAL_CHARS = re.compile(r"[^A-Za-z0-9]")


def _entropy(value: str) -> float:
    if not value:
        return 0.0
    counts = pd.Series(list(value)).value_counts(normalize=True)
    return float(-(counts * counts.map(math.log2)).sum())


def _has_ip(hostname: str) -> int:
    try:
        ipaddress.ip_address(hostname.strip("[]"))
        return 1
    except ValueError:
        return 0


def extract_url_features(url: str) -> dict[str, float]:
    """Extract numeric lexical features without contacting *url*."""
    value = str(url).strip()
    parsed = urlsplit(value if "://" in value else f"http://{value}")
    hostname = parsed.hostname or ""
    path = parsed.path or ""
    query = parsed.query or ""
    digits = sum(char.isdigit() for char in value)
    specials = len(_SPECIAL_CHARS.findall(value))
    nonempty_host_parts = [part for part in hostname.split(".") if part]
    return {
        "url_length": len(value),
        "hostname_length": len(hostname),
        "path_length": len(path),
        "query_length": len(query),
        "num_dots": value.count("."),
        "num_hyphens": value.count("-"),
        "num_digits": digits,
        "num_special_chars": specials,
        "num_subdomains": max(0, len(nonempty_host_parts) - 2),
        "has_ip_address": _has_ip(hostname),
        "has_https": int(parsed.scheme.lower() == "https"),
        "has_at_symbol": int("@" in value),
        "has_punycode": int("xn--" in hostname.lower()),
        "has_port": int(parsed.port is not None),
        "has_query": int(bool(query)),
        "has_fragment": int(bool(parsed.fragment)),
        "entropy": _entropy(value),
        "digit_ratio": digits / max(1, len(value)),
        "special_ratio": specials / max(1, len(value)),
        "path_depth": len([part for part in path.split("/") if part]),
    }


def build_feature_frame(urls: pd.Series) -> pd.DataFrame:
    """Build a stable feature matrix from a URL series."""
    return pd.DataFrame([extract_url_features(url) for url in urls], columns=FEATURE_NAMES)
