"""Tests for ICMP-first lightweight internet check."""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch


def test_default_ping_targets() -> None:
    from tools.internet_check import get_ping_targets

    with patch.dict(os.environ, {}, clear=True):
        os.environ.pop("PING_TARGETS", None)
        os.environ.pop("PING_TARGET", None)
        assert get_ping_targets() == ["1.1.1.1", "8.8.8.8"]


def test_ping_targets_from_env_list() -> None:
    from tools.internet_check import get_ping_targets

    with patch.dict(os.environ, {"PING_TARGETS": "1.1.1.1, 9.9.9.9"}, clear=False):
        assert get_ping_targets() == ["1.1.1.1", "9.9.9.9"]


def test_ping_target_singular_env() -> None:
    from tools.internet_check import get_ping_targets

    with patch.dict(os.environ, {"PING_TARGET": "1.0.0.1"}, clear=False):
        os.environ.pop("PING_TARGETS", None)
        assert get_ping_targets() == ["1.0.0.1"]


def test_ping_timeout_default_is_one_second() -> None:
    from tools.internet_check import get_ping_timeout

    with patch.dict(os.environ, {}, clear=True):
        os.environ.pop("PING_TIMEOUT", None)
        assert get_ping_timeout() == 1


def test_build_ping_command() -> None:
    from tools.internet_check import build_ping_command

    assert build_ping_command("1.1.1.1", timeout=1) == [
        "ping",
        "-c",
        "1",
        "-W",
        "1",
        "1.1.1.1",
    ]


def test_check_internet_succeeds_on_first_target() -> None:
    from tools.internet_check import check_internet_lightweight

    runner = MagicMock(return_value=0)
    assert check_internet_lightweight(run_ping=runner, targets=["1.1.1.1", "8.8.8.8"], timeout=1) is True
    runner.assert_called_once()
    assert runner.call_args[0][0][-1] == "1.1.1.1"


def test_check_internet_falls_back_to_second_target() -> None:
    from tools.internet_check import check_internet_lightweight

    def run_ping(cmd: list[str]) -> int:
        host = cmd[-1]
        if host == "1.1.1.1":
            raise OSError("unreachable")
        return 0

    assert check_internet_lightweight(run_ping=run_ping, targets=["1.1.1.1", "8.8.8.8"], timeout=1) is True


def test_check_internet_false_when_all_targets_fail() -> None:
    from tools.internet_check import check_internet_lightweight

    def run_ping(_cmd: list[str]) -> int:
        raise OSError("down")

    assert check_internet_lightweight(run_ping=run_ping, targets=["1.1.1.1"], timeout=1) is False


def test_check_internet_does_not_call_curl() -> None:
    """Hot path must not use curl/msftconnecttest."""
    from tools.internet_check import check_internet_lightweight

    with patch("subprocess.run") as curl_run, patch("subprocess.check_call") as ping_call:
        ping_call.return_value = 0
        # Use real runner path (no inject) to ensure default impl uses ping only
        assert check_internet_lightweight(targets=["1.1.1.1"], timeout=1) is True
        curl_run.assert_not_called()
        ping_call.assert_called()
        cmd = ping_call.call_args[0][0]
        assert "curl" not in cmd
        assert "msftconnecttest" not in " ".join(cmd)
        assert cmd == ["ping", "-c", "1", "-W", "1", "1.1.1.1"]
