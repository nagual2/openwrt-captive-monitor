"""Adaptive check interval and keepalive throttle for captive portal daemon.

Pure helpers — no I/O — so unit tests stay deterministic.
"""

from __future__ import annotations

import os

DEFAULT_CHECK_INTERVAL = 5
DEFAULT_REFRESH_INTERVAL = 1800
DEFAULT_BACKOFF_CAP = 60


def get_check_interval() -> int:
    """Return CHECK_INTERVAL from env (seconds), default 5."""
    return int(os.environ.get("CHECK_INTERVAL", str(DEFAULT_CHECK_INTERVAL)))


def get_refresh_interval() -> int:
    """Return REFRESH_INTERVAL from env (seconds), default 1800."""
    return int(os.environ.get("REFRESH_INTERVAL", str(DEFAULT_REFRESH_INTERVAL)))


def next_backoff(
    current: int,
    *,
    success: bool,
    baseline: int = DEFAULT_CHECK_INTERVAL,
    cap: int = DEFAULT_BACKOFF_CAP,
) -> int:
    """Compute next sleep interval after a check cycle.

    On success, reset to baseline. On failure, double until ``cap``.
    """
    if success:
        return baseline
    return min(max(current, 1) * 2, cap)


def should_send_keepalive(last_ts: float, now: float, refresh_interval: int) -> bool:
    """Return True if enough time passed since last keepalive (or never sent)."""
    if last_ts <= 0:
        return True
    return (now - last_ts) >= refresh_interval
