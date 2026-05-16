"""Tests for cli.doctor and cli.setup_keys (smoke + unit only)."""

import asyncio
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


pytestmark = pytest.mark.unit


def test_doctor_module_imports():
    from cli import doctor
    assert hasattr(doctor, "run")
    assert hasattr(doctor, "main")


def test_setup_keys_module_imports():
    from cli import setup_keys
    assert hasattr(setup_keys, "run")
    assert hasattr(setup_keys, "main")
    assert hasattr(setup_keys, "_validate_key")


def test_setup_keys_read_env_file_handles_missing(tmp_path):
    from cli.setup_keys import _read_env_file
    p = tmp_path / "missing.env"
    assert _read_env_file(p) == {}


def test_setup_keys_write_then_read(tmp_path):
    from cli.setup_keys import _read_env_file, _write_env_file
    p = tmp_path / "test.env"
    _write_env_file(p, {"FOO": "bar", "BAZ": "qux qux"})
    assert p.exists()
    # chmod 600
    import stat
    mode = p.stat().st_mode & 0o777
    assert mode == 0o600, f"expected 0o600, got {oct(mode)}"
    # Round trip
    loaded = _read_env_file(p)
    assert loaded["FOO"] == "bar"
    assert loaded["BAZ"] == "qux qux"


def test_setup_keys_unknown_service_handled():
    """_configure_one with an invalid service name should reject without crashing."""
    from cli.setup_keys import _configure_one
    result = asyncio.run(_configure_one("fake-service-xyz"))
    assert result is False
