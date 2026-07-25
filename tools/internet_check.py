"""ICMP-first lightweight connectivity check for the captive portal daemon.

Uses ping (not HTTP/curl) on the hot path so a 5s check interval stays responsive
when the uplink is down. Captive-portal HTTP detection remains in the Chrome path.
"""

from __future__ import annotations

import os
import subprocess
from collections.abc import Callable, Sequence

DEFAULT_PING_TARGETS = ("1.1.1.1", "8.8.8.8")
DEFAULT_PING_TIMEOUT = 1

PingRunner = Callable[[list[str]], int]


def get_ping_targets() -> list[str]:
    """Return ping hosts from env.

    ``PING_TARGETS`` — comma-separated list (preferred).
    ``PING_TARGET`` — single host fallback.
    Default: Cloudflare DNS then Google DNS.
    """
    raw_list = os.environ.get("PING_TARGETS", "").strip()
    if raw_list:
        return [h.strip() for h in raw_list.split(",") if h.strip()]

    singular = os.environ.get("PING_TARGET", "").strip()
    if singular:
        return [singular]

    return list(DEFAULT_PING_TARGETS)


def get_ping_timeout() -> int:
    """Return per-probe wait seconds (``ping -W``), default 1."""
    return int(os.environ.get("PING_TIMEOUT", str(DEFAULT_PING_TIMEOUT)))


def build_ping_command(host: str, timeout: int = DEFAULT_PING_TIMEOUT) -> list[str]:
    """Build a single-packet ICMP ping command (Linux/iputils)."""
    return ["ping", "-c", "1", "-W", str(timeout), host]


def _default_run_ping(cmd: list[str]) -> int:
    subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return 0


def check_internet_lightweight(
    *,
    run_ping: PingRunner | None = None,
    targets: Sequence[str] | None = None,
    timeout: int | None = None,
) -> bool:
    """Return True if any configured host answers ICMP echo.

    Does not use curl or captive-portal HTTP endpoints.
    """
    runner = run_ping or _default_run_ping
    hosts = list(targets) if targets is not None else get_ping_targets()
    wait = get_ping_timeout() if timeout is None else timeout

    for host in hosts:
        try:
            runner(build_ping_command(host, timeout=wait))
            return True
        except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
            continue
    return False
