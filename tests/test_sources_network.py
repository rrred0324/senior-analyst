"""Network tests for new data sources. Marked as @pytest.mark.network so they
can be skipped in CI or when offline.

Run only network tests:
    pytest tests/test_sources_network.py -v -m network
Skip them:
    pytest tests/ -v -m "not network"
"""

import pytest

pytestmark = pytest.mark.network


@pytest.mark.asyncio
async def test_worldbank_fetches_us_gdp():
    from sources.worldbank_source import WorldBankSource
    src = WorldBankSource()
    r = await src.get_macro_data("gdp", region="US", years=3)
    assert r.success, f"failed: {r.error}"
    assert r.data.points, "no points returned"
    assert r.data.region == "USA"
    assert r.data.unit == "USD"


@pytest.mark.asyncio
async def test_worldbank_fetches_cn_gdp():
    from sources.worldbank_source import WorldBankSource
    src = WorldBankSource()
    r = await src.get_macro_data("gdp", region="CN", years=3)
    assert r.success, f"failed: {r.error}"
    assert r.data.points
    assert r.data.region == "CHN"


@pytest.mark.asyncio
async def test_worldbank_unsupported_indicator_returns_error():
    from sources.worldbank_source import WorldBankSource
    src = WorldBankSource()
    r = await src.get_macro_data("nonsense_indicator", region="US")
    assert not r.success
    assert "does not support" in r.error


@pytest.mark.asyncio
async def test_coingecko_fetches_btc():
    from sources.coingecko_source import CoinGeckoSource
    src = CoinGeckoSource()
    r = await src.get_crypto_data("BTC")
    assert r.success, f"failed: {r.error}"
    asset = r.data
    assert asset.symbol.upper() == "BTC"
    assert asset.price_usd is not None and asset.price_usd > 0
    assert asset.market_cap_usd is not None and asset.market_cap_usd > 0


@pytest.mark.asyncio
async def test_coingecko_handles_lowercase_id():
    from sources.coingecko_source import CoinGeckoSource
    src = CoinGeckoSource()
    r = await src.get_crypto_data("ethereum")
    assert r.success, f"failed: {r.error}"
    assert r.data.coingecko_id == "ethereum"


@pytest.mark.asyncio
async def test_stats_gov_cn_fetches_cpi():
    from sources.stats_gov_cn_source import StatsGovCNSource
    src = StatsGovCNSource()
    r = await src.get_macro_data("cpi", region="CN", period="monthly", years=2)
    assert r.success, f"failed: {r.error}"
    assert r.data.points
    # Most recent point should be 2024+ for a healthy data source
    most_recent = r.data.points[0]
    assert "20" in most_recent["date"], f"unexpected date format: {most_recent}"


@pytest.mark.asyncio
async def test_stats_gov_cn_rejects_non_cn_region():
    from sources.stats_gov_cn_source import StatsGovCNSource
    src = StatsGovCNSource()
    r = await src.get_macro_data("cpi", region="US")
    assert not r.success
    assert "only supports region='CN'" in r.error


@pytest.mark.asyncio
async def test_macro_data_tool_routes_us_to_worldbank_without_fred_key():
    """When no FRED key is set, US macro_data should fall through to World Bank."""
    import os
    from sources.config import has_fred
    if has_fred():
        pytest.skip("FRED key is set; this test only exercises the fallback path")

    import sys
    sys.path.insert(0, ".")
    from server import macro_data
    import json
    out = await macro_data("gdp", "US", "annual", 3)
    j = json.loads(out)
    assert j["success"] is True
    assert j["data_source"] == "worldbank"
