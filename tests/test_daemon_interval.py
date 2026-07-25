"""Tests for adaptive daemon interval / backoff / keepalive throttle."""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest


def test_adaptive_interval_default() -> None:
    """CHECK_INTERVAL defaults to 5 seconds (not 60)."""
    from tools.daemon_interval import get_check_interval

    with patch.dict(os.environ, {}, clear=True):
        # Ensure CHECK_INTERVAL is unset
        os.environ.pop("CHECK_INTERVAL", None)
        assert get_check_interval() == 5


def test_adaptive_interval_from_env() -> None:
    """CHECK_INTERVAL can be overridden via environment."""
    from tools.daemon_interval import get_check_interval

    with patch.dict(os.environ, {"CHECK_INTERVAL": "10"}, clear=False):
        assert get_check_interval() == 10


def test_refresh_interval_default() -> None:
    """REFRESH_INTERVAL defaults to 1800 seconds (30 min)."""
    from tools.daemon_interval import get_refresh_interval

    with patch.dict(os.environ, {}, clear=True):
        os.environ.pop("REFRESH_INTERVAL", None)
        assert get_refresh_interval() == 1800


def test_backoff_doubles_on_net_down() -> None:
    """On network failure, backoff doubles until capped at 60s."""
    from tools.daemon_interval import next_backoff

    assert next_backoff(5, success=False) == 10
    assert next_backoff(10, success=False) == 20
    assert next_backoff(20, success=False) == 40
    assert next_backoff(40, success=False) == 60
    assert next_backoff(60, success=False) == 60


def test_backoff_resets_on_net_up() -> None:
    """On success, backoff resets to baseline (5s)."""
    from tools.daemon_interval import next_backoff

    assert next_backoff(60, success=True, baseline=5) == 5
    assert next_backoff(40, success=True, baseline=5) == 5
    assert next_backoff(5, success=True, baseline=5) == 5


def test_keepalive_throttled() -> None:
    """Keepalive is needed only after REFRESH_INTERVAL elapsed."""
    from tools.daemon_interval import should_send_keepalive

    refresh = 1800
    last_ts = 1_000_000.0

    assert should_send_keepalive(last_ts, last_ts + 100, refresh) is False
    assert should_send_keepalive(last_ts, last_ts + 1799, refresh) is False
    assert should_send_keepalive(last_ts, last_ts + 1800, refresh) is True
    assert should_send_keepalive(last_ts, last_ts + 2000, refresh) is True


def test_keepalive_needed_when_never_sent() -> None:
    """If keepalive never ran (last_ts=0), it should be requested."""
    from tools.daemon_interval import should_send_keepalive

    assert should_send_keepalive(0.0, 1_000_000.0, 1800) is True


@pytest.mark.parametrize(
    ("current", "success", "expected"),
    [
        (5, False, 10),
        (30, False, 60),
        (60, True, 5),
    ],
)
def test_backoff_parametrized(current: int, success: bool, expected: int) -> None:
    from tools.daemon_interval import next_backoff

    assert next_backoff(current, success=success, baseline=5, cap=60) == expected
