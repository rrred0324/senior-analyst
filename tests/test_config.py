"""Unit tests for sources/config.py — key detection, registry, cache helpers."""

import pytest

from sources.config import (
    KEY_SERVICES, AVAILABLE_SOURCES, build_source_registry,
    has_fmp, has_av, has_newsapi, has_fred, has_coingecko_pro,
    cache_key, get_cache, compute_timeouts,
)


pytestmark = pytest.mark.unit


def test_key_services_complete():
    """KEY_SERVICES must list all 5 supported services with required fields."""
    expected = {"fmp", "av", "newsapi", "fred", "coingecko"}
    assert set(KEY_SERVICES.keys()) == expected
    for sid, svc in KEY_SERVICES.items():
        assert svc["env_var"], f"{sid} missing env_var"
        assert svc["label"], f"{sid} missing label"
        assert svc["tier"] in ("free-key", "paid", "paid-optional"), f"{sid} unknown tier"
        assert svc["signup_url"].startswith("http"), f"{sid} bad signup_url"
        assert svc["unlocks"], f"{sid} missing unlocks description"


def test_has_functions_return_bool():
    for fn in (has_fmp, has_av, has_newsapi, has_fred, has_coingecko_pro):
        assert isinstance(fn(), bool)


def test_build_source_registry_includes_macro_and_crypto():
    build_source_registry()
    assert "macro_data" in AVAILABLE_SOURCES
    assert "crypto_data" in AVAILABLE_SOURCES
    # Tier 0 always provides at least worldbank for macro and coingecko for crypto
    assert "worldbank" in AVAILABLE_SOURCES["macro_data"]
    assert "stats_gov_cn" in AVAILABLE_SOURCES["macro_data"]
    assert "coingecko" in AVAILABLE_SOURCES["crypto_data"]


def test_build_source_registry_existing_tools_unchanged():
    build_source_registry()
    # Existing tools must keep their Tier 0 sources
    assert "yfinance" in AVAILABLE_SOURCES["company_financials"]
    assert "akshare" in AVAILABLE_SOURCES["company_financials"]
    assert "eastmoney" in AVAILABLE_SOURCES["company_financials"]


def test_cache_key_deterministic():
    a = cache_key("macro", "fred", "GDP", "annual", 3)
    b = cache_key("macro", "fred", "GDP", "annual", 3)
    assert a == b
    c = cache_key("macro", "fred", "GDP", "annual", 5)
    assert a != c


def test_get_cache_includes_macro_and_crypto():
    macro = get_cache("macro")
    crypto = get_cache("crypto")
    assert macro is not None
    assert crypto is not None
    # TTL configured: macro = 6h (21600), crypto = 1m (60)
    assert macro.ttl == 21600
    assert crypto.ttl == 60


def test_compute_timeouts_distribution():
    t1 = compute_timeouts(1, total_budget=8.0)
    t2 = compute_timeouts(2, total_budget=8.0)
    t3 = compute_timeouts(3, total_budget=8.0)
    assert sum(t1) == 8.0
    assert abs(sum(t2) - 8.0) < 1e-6
    assert abs(sum(t3) - 8.0) < 1e-6
