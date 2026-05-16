"""Senior Analyst MCP Server — structured financial/business data for Claude Code.

Supports Tier 0 (free, no keys) and Tier 1 (FMP/Alpha Vantage/NewsAPI, with keys).
"""

import sys
import os
import logging
import json
from dataclasses import asdict
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

from mcp.server.fastmcp import FastMCP
from sources import (
    YFinanceSource, AkshareSource, EastmoneySource,
    WorldBankSource, StatsGovCNSource, CoinGeckoSource,
    FMPSource, AlphaVantageSource, NewsAPISource, FREDSource,
    Validator, ValuationSource,
)
from sources.config import build_source_registry, AVAILABLE_SOURCES, compute_timeouts
from sources.base import ConfidenceScore

mcp = FastMCP(
    "senior_analyst",
    instructions=(
        "Financial and business data server for Senior Analyst skill. "
        "Use company_financials for financial statements, "
        "company_profile for company info and valuation, competitor_compare for peer analysis, "
        "market_data for industry/market data, news_search for recent news, "
        "industry_data for industry classification and constituents, "
        "stock_news for company-specific news and announcements, "
        "macro_data for macroeconomic indicators (GDP, CPI, unemployment, rates) by country, "
        "crypto_data for cryptocurrency market data via CoinGecko. "
        "Supports company names (Chinese or English) and ticker symbols. "
        "No API keys required for basic data; configure keys for enhanced sources."
    ),
)

# --- Initialize sources ---

_yfinance = YFinanceSource()
_akshare = AkshareSource()
_eastmoney = EastmoneySource()
_worldbank = WorldBankSource()
_stats_gov_cn = StatsGovCNSource()
_coingecko = CoinGeckoSource()

_fmp = None
_av = None
_newsapi = None
_fred = None

if FMPSource is not None:
    try:
        _fmp = FMPSource()
    except Exception:
        pass

if AlphaVantageSource is not None:
    try:
        _av = AlphaVantageSource()
    except Exception:
        pass

if NewsAPISource is not None:
    try:
        _newsapi = NewsAPISource()
    except Exception:
        pass

if FREDSource is not None:
    try:
        _fred = FREDSource()
    except Exception:
        pass

# Build source registry after all sources are initialized
build_source_registry()

_validator = Validator()

# Valuation source aggregates data from other sources
_valuation = ValuationSource(
    financials_sources=[_fmp, _eastmoney, _akshare, _yfinance, _av],
    macro_source=_fred or _worldbank,
    peers_sources=[_fmp, _yfinance, _eastmoney],
)

logger = logging.getLogger(__name__)


def _to_dict(data):
    if hasattr(data, "__dataclass_fields__"):
        return asdict(data)
    return data


def _fetched_at() -> str:
    return datetime.now(timezone.utc).isoformat()


# --- Source fallback runner ---

async def _run_with_fallback(sources_with_methods: list[tuple, str], timeout_budget: float = 8.0):
    """Try sources in priority order with timeout budget.

    sources_with_methods: list of (source_instance, method_name, args_dict)
    Returns the first successful DataResult, or the last failure.
    """
    n = len(sources_with_methods)
    timeouts = compute_timeouts(n, timeout_budget)
    last_error = "All data sources unavailable"

    for i, (source, method_name, args) in enumerate(sources_with_methods):
        if source is None:
            continue
        try:
            method = getattr(source, method_name, None)
            if method is None:
                continue
            result = await method(**args)
            if result.has_data():
                return result
            last_error = result.error or last_error
        except Exception as e:
            logger.warning(f"Source {source.name}.{method_name} failed: {e}")
            last_error = str(e)

    from sources.base import DataResult
    return DataResult(success=False, error=last_error)


async def _run_secondary(
    sources_with_methods: list[tuple], exclude_source: str, timeout_budget: float = 6.0
):
    """Try sources EXCLUDING the one that already succeeded (for cross-validation).

    Returns the first successful DataResult from a different source, or a failure.
    """
    filtered = [
        (src, method, args)
        for src, method, args in sources_with_methods
        if src is not None and src.name != exclude_source
    ]
    if not filtered:
        from sources.base import DataResult
        return DataResult(success=False, error="No secondary source available")

    return await _run_with_fallback(filtered, timeout_budget=timeout_budget)


# --- MCP Tools ---

@mcp.tool()
async def company_financials(identifier: str, period: str = "annual", years: int = 3) -> str:
    """Get financial data (revenue, profit, cash flow, balance sheet) for a company.

    Args:
        identifier: Company name (e.g., "滴滴", "Apple") or ticker symbol (e.g., "AAPL", "0700.HK")
        period: "annual" or "quarterly"
        years: Number of years/quarters to retrieve (default 3)
    """
    sources = []
    if _fmp:
        sources.append((_fmp, "get_financials", {"identifier": identifier, "period": period, "years": years}))
    sources.append((_eastmoney, "get_financials", {"identifier": identifier, "period": period, "years": years}))
    sources.append((_akshare, "get_financials", {"identifier": identifier, "period": period, "years": years}))
    sources.append((_yfinance, "get_financials", {"identifier": identifier, "period": period, "years": years}))
    if _av:
        sources.append((_av, "get_financials", {"identifier": identifier, "period": period, "years": years}))

    result = await _run_with_fallback(sources)
    if result.has_data():
        data = _to_dict(result.data)
        data["data_source"] = result.source
        data["fetched_at"] = _fetched_at()

        # Cross-validate if we have multiple sources
        confidence = _validator.build_confidence_for_tool(result)
        if len(sources) >= 2:
            try:
                secondary = await _run_secondary(sources, exclude_source=result.source)
                if secondary.has_data():
                    cv = _validator.compare_sources([result, secondary])
                    confidence = cv.confidence
                    data["cross_validation"] = {
                        "sources_compared": [result.source, secondary.source],
                        "discrepancies": cv.discrepancies,
                        "reconciled": cv.reconciled,
                    }
            except Exception:
                pass

        data["confidence"] = asdict(confidence)
        return json.dumps({"success": True, **data}, ensure_ascii=False, default=str)

    return json.dumps({
        "success": False, "identifier": identifier,
        "error": result.error or "All data sources unavailable. Try WebSearch or provide data manually.",
    }, ensure_ascii=False)


@mcp.tool()
async def company_profile(identifier: str) -> str:
    """Get company profile including industry, sector, market cap, and valuation ratios.

    Args:
        identifier: Company name (e.g., "滴滴", "Apple") or ticker symbol (e.g., "AAPL", "0700.HK")
    """
    sources = []
    if _fmp:
        sources.append((_fmp, "get_profile", {"identifier": identifier}))
    sources.append((_eastmoney, "get_profile", {"identifier": identifier}))
    sources.append((_yfinance, "get_profile", {"identifier": identifier}))
    sources.append((_akshare, "get_profile", {"identifier": identifier}))
    if _av:
        sources.append((_av, "get_profile", {"identifier": identifier}))

    result = await _run_with_fallback(sources)
    if result.has_data():
        data = _to_dict(result.data)
        data["data_source"] = result.source
        data["fetched_at"] = _fetched_at()

        confidence = _validator.build_confidence_for_tool(result)
        data["confidence"] = asdict(confidence)

        return json.dumps({"success": True, **data}, ensure_ascii=False, default=str)

    return json.dumps({
        "success": False, "identifier": identifier,
        "error": result.error or "All data sources unavailable for profile lookup.",
    }, ensure_ascii=False)


@mcp.tool()
async def competitor_compare(identifier: str, metrics: str = "revenue,net_margin,ps_ratio") -> str:
    """Get peer/competitor companies and compare key financial metrics.

    Args:
        identifier: Target company name or ticker symbol
        metrics: Comma-separated metrics to compare (default: "revenue,net_margin,ps_ratio")
    """
    target_data = {"name": identifier, "ticker": identifier}
    peers_data = []
    source = "mixed"

    async def _fetch_company_brief(src, ticker: str) -> dict:
        """Fetch profile + financials for a single company, returning a brief dict."""
        brief = {"name": ticker, "ticker": ticker}
        profile_result = await src.get_profile(ticker)
        fin_result = await src.get_financials(ticker, years=1)
        if profile_result.has_data():
            pp = _to_dict(profile_result.data)
            brief["name"] = pp.get("name", ticker)
            brief["industry"] = pp.get("industry", "")
            brief["sector"] = pp.get("sector", "")
            brief["ps_ratio"] = pp.get("ps_ratio")
        if fin_result.has_data():
            latest = fin_result.data.get("data", [{}])[0] if isinstance(fin_result.data, dict) and fin_result.data.get("data") else {}
            rev = latest.get("revenue")
            ni = latest.get("net_income")
            brief["revenue"] = rev
            brief["net_margin"] = round(ni / rev, 4) if rev and ni and rev != 0 else None
        return brief

    # L1: FMP (best peer data when available)
    if _fmp:
        try:
            peers_result = await _fmp.get_peers(identifier)
            target_data = await _fetch_company_brief(_fmp, identifier)

            peer_tickers = []
            if peers_result.has_data():
                peer_tickers = peers_result.data.get("peer_tickers", [])

            for pt in peer_tickers[:5]:
                peers_data.append(await _fetch_company_brief(_fmp, pt))

            if target_data.get("revenue") or peers_data:
                source = "fmp"
        except Exception:
            pass

    # L2: yfinance (if FMP didn't work)
    if not peers_data:
        peers_result = await _yfinance.get_peers(identifier)
        target_data = await _fetch_company_brief(_yfinance, identifier)

        peer_tickers = []
        if peers_result.has_data():
            peer_tickers = peers_result.data.get("peer_tickers", [])

        for pt in peer_tickers[:5]:
            peers_data.append(await _fetch_company_brief(_yfinance, pt))

        if target_data.get("revenue") or peers_data:
            source = "yfinance"

    # L3: eastmoney peers (China companies)
    if not peers_data:
        em_peers = await _eastmoney.get_peers(identifier)
        if em_peers.has_data():
            pd = em_peers.data
            if isinstance(pd, dict) and "peers_detail" in pd:
                peers_data = pd["peers_detail"][:5]
                source = "eastmoney"

    result = {
        "success": True,
        "target": target_data,
        "peers": peers_data,
        "source": source,
        "data_source": source,
        "fetched_at": _fetched_at(),
    }
    if source == "eastmoney":
        result["note"] = "Peer data from eastmoney. Peers based on industry match. Specify tickers for more control."
    elif source in ("fmp", "yfinance"):
        result["note"] = f"Peer list based on {source} recommendations. Specify tickers for more control."
    else:
        result["note"] = "Limited peer data available. Consider specifying competitor tickers manually."

    return json.dumps(result, ensure_ascii=False, default=str)


@mcp.tool()
async def market_data(industry: str, region: str = "global", metric: str = "") -> str:
    """Get market size, growth rate, and industry-level data.

    Args:
        industry: Industry name (e.g., "ride-hailing", "insurance", "ev", "银行", "游戏")
        region: Geographic region (default "global")
        metric: Specific metric to query (optional)
    """
    sources = []
    if _fmp:
        sources.append((_fmp, "get_market_data", {"industry": industry, "region": region, "metric": metric}))
    sources.append((_eastmoney, "get_market_data", {"industry": industry, "region": region, "metric": metric}))
    sources.append((_akshare, "get_market_data", {"industry": industry, "region": region, "metric": metric}))

    result = await _run_with_fallback(sources)
    if result.has_data():
        data = _to_dict(result.data) if isinstance(result.data, dict) else {"data": result.data}
        data["data_source"] = result.source
        data["fetched_at"] = _fetched_at()
        return json.dumps({
            "success": True, **data,
            "disclaimer": "Market data from free sources may be limited. Use WebSearch for comprehensive reports.",
        }, ensure_ascii=False, default=str)

    return json.dumps({
        "success": False, "industry": industry, "region": region,
        "error": result.error or "No market data from available sources.",
        "suggestion": f'Search for: "{industry} 市场规模" or "{industry} market size {region}"',
    }, ensure_ascii=False)


@mcp.tool()
async def news_search(query: str, limit: int = 5) -> str:
    """Get recent news articles related to a company or topic.

    Args:
        query: Search keywords (e.g., "滴滴 保险", "Tesla earnings")
        limit: Maximum number of results (default 5, max 20)
    """
    limit = min(max(limit, 1), 20)

    sources = []
    if _newsapi:
        sources.append((_newsapi, "get_news", {"query": query, "limit": limit}))
    sources.append((_akshare, "get_news", {"query": query, "limit": limit}))
    sources.append((_eastmoney, "get_news", {"query": query, "limit": limit}))
    if _av:
        sources.append((_av, "get_news", {"query": query, "limit": limit}))
    if _fmp:
        sources.append((_fmp, "get_news", {"query": query, "limit": limit}))

    result = await _run_with_fallback(sources)
    if result.has_data():
        data = _to_dict(result.data) if isinstance(result.data, dict) else {"data": result.data}
        data["data_source"] = result.source
        data["fetched_at"] = _fetched_at()
        return json.dumps({"success": True, **data}, ensure_ascii=False, default=str)

    return json.dumps({
        "success": False, "query": query,
        "error": result.error or "News sources unavailable. Try WebSearch in main session.",
    }, ensure_ascii=False)


@mcp.tool()
async def industry_data(industry: str, metric: str = "", region: str = "global") -> str:
    """Get industry classification, constituent stocks, and valuation data.

    Args:
        industry: Industry name or code (Chinese or English, e.g., "游戏", "银行", "gaming")
        metric: Specific metric (optional, e.g., "pe_median", "revenue_growth")
        region: Geographic region (default "global")
    """
    sources = []
    if _fmp:
        sources.append((_fmp, "get_industry_data", {"industry": industry, "region": region, "metric": metric}))
    sources.append((_eastmoney, "get_industry_data", {"industry": industry, "region": region, "metric": metric}))
    sources.append((_akshare, "get_industry_data", {"industry": industry, "region": region, "metric": metric}))

    result = await _run_with_fallback(sources)
    if result.has_data():
        data = _to_dict(result.data) if isinstance(result.data, dict) else {"data": result.data}
        data["data_source"] = result.source
        data["fetched_at"] = _fetched_at()
        return json.dumps({"success": True, **data}, ensure_ascii=False, default=str)

    return json.dumps({
        "success": False, "industry": industry,
        "error": result.error or "No industry data from available sources.",
        "suggestion": f'Try a more specific industry name, or search "{industry} 行业分析" via WebSearch.',
    }, ensure_ascii=False)


@mcp.tool()
async def stock_news(identifier: str, days: int = 7, limit: int = 10) -> str:
    """Get company-specific news, announcements, and sentiment data.

    Args:
        identifier: Company name or ticker symbol (e.g., "腾讯", "AAPL")
        days: Lookback period in days (default 7)
        limit: Maximum number of results (default 10, max 20)
    """
    limit = min(max(limit, 1), 20)

    sources = []
    sources.append((_akshare, "get_stock_news", {"identifier": identifier, "days": days, "limit": limit}))
    sources.append((_eastmoney, "get_stock_news", {"identifier": identifier, "days": days, "limit": limit}))
    if _newsapi:
        sources.append((_newsapi, "get_stock_news", {"identifier": identifier, "days": days, "limit": limit}))
    if _av:
        sources.append((_av, "get_stock_news", {"identifier": identifier, "days": days, "limit": limit}))
    if _fmp:
        sources.append((_fmp, "get_stock_news", {"identifier": identifier, "days": days, "limit": limit}))

    result = await _run_with_fallback(sources)
    if result.has_data():
        data = _to_dict(result.data) if isinstance(result.data, dict) else {"data": result.data}
        data["data_source"] = result.source
        data["fetched_at"] = _fetched_at()
        return json.dumps({"success": True, **data}, ensure_ascii=False, default=str)

    return json.dumps({
        "success": False, "identifier": identifier,
        "error": result.error or "No stock news from available sources.",
    }, ensure_ascii=False)


@mcp.tool()
async def macro_data(
    indicator: str, region: str = "US", period: str = "monthly", years: int = 3
) -> str:
    """Get macroeconomic indicator time series for a country/region.

    Args:
        indicator: Indicator name. Common values: "gdp", "gdp_growth", "cpi", "cpi_yoy",
                   "ppi", "pmi", "m2", "interest_rate", "unemployment", "retail_sales",
                   "industrial_production", "fdi", "exports", "imports", "fx".
        region: Country/region code: "US", "CN", "EU", "JP", "UK", "DE", "FR", "IN",
                or "global" for World Bank world aggregates.
        period: "monthly", "quarterly", or "annual" (used where source supports it).
        years: Number of years of history to retrieve (default 3).

    Source priority:
        US     -> FRED (if key) -> WorldBank
        CN     -> stats_gov_cn (NBS/PBOC via akshare) -> WorldBank
        Other  -> WorldBank (annual) -> FRED (if key, fx_dxy only)
    """
    region_upper = region.upper()
    sources = []

    if region_upper in ("US", "USA"):
        if _fred:
            sources.append((_fred, "get_macro_data", {"indicator": indicator, "region": "US", "period": period, "years": years}))
        sources.append((_worldbank, "get_macro_data", {"indicator": indicator, "region": "US", "period": "annual", "years": years}))
    elif region_upper in ("CN", "CHINA", "CHN"):
        sources.append((_stats_gov_cn, "get_macro_data", {"indicator": indicator, "region": "CN", "period": period, "years": years}))
        sources.append((_worldbank, "get_macro_data", {"indicator": indicator, "region": "CN", "period": "annual", "years": years}))
    else:
        sources.append((_worldbank, "get_macro_data", {"indicator": indicator, "region": region, "period": "annual", "years": years}))
        if _fred and indicator.lower() in ("fx_dxy",):
            sources.append((_fred, "get_macro_data", {"indicator": indicator, "region": "global", "period": period, "years": years}))

    result = await _run_with_fallback(sources, timeout_budget=8.0)
    if result.has_data():
        data = _to_dict(result.data) if isinstance(result.data, dict) or hasattr(result.data, "__dataclass_fields__") else {"data": result.data}
        data["data_source"] = result.source
        data["fetched_at"] = _fetched_at()
        return json.dumps({"success": True, **data}, ensure_ascii=False, default=str)

    return json.dumps({
        "success": False, "indicator": indicator, "region": region,
        "error": result.error or "No macro data available.",
        "suggestion": (
            f"For US data, configure FRED key (free): senior_analyst setup-keys --service fred. "
            f"For CN data, ensure akshare is installed and reachable. "
            f"World Bank covers most countries with annual data."
        ),
    }, ensure_ascii=False)


@mcp.tool()
async def crypto_data(identifier: str, metrics: str = "price,marketcap,volume") -> str:
    """Get cryptocurrency market data via CoinGecko.

    Args:
        identifier: Symbol (e.g., "BTC", "ETH") or CoinGecko id (e.g., "bitcoin", "ethereum").
        metrics: Comma-separated metrics to focus on (default: "price,marketcap,volume").
                 Currently informational; full asset snapshot is always returned.
    """
    sources = [(_coingecko, "get_crypto_data", {"identifier": identifier, "metrics": metrics})]
    result = await _run_with_fallback(sources, timeout_budget=6.0)

    if result.has_data():
        data = _to_dict(result.data) if hasattr(result.data, "__dataclass_fields__") else {"data": result.data}
        if not isinstance(data, dict):
            data = {"data": data}
        data["data_source"] = result.source
        data["fetched_at"] = _fetched_at()
        return json.dumps({"success": True, **data}, ensure_ascii=False, default=str)

    return json.dumps({
        "success": False, "identifier": identifier,
        "error": result.error or "CoinGecko unavailable.",
        "suggestion": "Check spelling — common symbols: BTC, ETH, SOL, BNB, XRP. For lesser-known coins, use the CoinGecko id (e.g., 'avalanche-2' instead of 'AVAX').",
    }, ensure_ascii=False)


@mcp.tool()
async def validate_financials(identifier: str, period: str = "annual", years: int = 3) -> str:
    """Cross-validate financial data from multiple sources with anomaly detection.
    Performs three-statement reconciliation, detects outliers, and computes confidence scores.

    Args:
        identifier: Company name or ticker symbol
        period: "annual" or "quarterly"
        years: Number of years/quarters to validate (default 3)
    """
    sources = []
    if _fmp:
        sources.append((_fmp, "get_financials", {"identifier": identifier, "period": period, "years": years}))
    sources.append((_eastmoney, "get_financials", {"identifier": identifier, "period": period, "years": years}))
    sources.append((_akshare, "get_financials", {"identifier": identifier, "period": period, "years": years}))
    sources.append((_yfinance, "get_financials", {"identifier": identifier, "period": period, "years": years}))
    if _av:
        sources.append((_av, "get_financials", {"identifier": identifier, "period": period, "years": years}))

    if not sources:
        return json.dumps({
            "success": False, "identifier": identifier,
            "error": "No data sources available for validation.",
        }, ensure_ascii=False)

    # Collect results from multiple sources
    results = []
    for source, method_name, args in sources[:3]:  # max 3 sources for speed
        if source is None:
            continue
        try:
            method = getattr(source, method_name, None)
            if method is None:
                continue
            r = await method(**args)
            if r.has_data():
                results.append(r)
                if len(results) >= 2:
                    break  # 2 sources enough for cross-validation
        except Exception:
            continue

    if not results:
        return json.dumps({
            "success": False, "identifier": identifier,
            "error": "No financial data from any source.",
        }, ensure_ascii=False)

    # Cross-validate across sources
    cv = _validator.compare_sources(results)

    # Anomaly detection on the primary source
    primary = results[0]
    periods = []
    currency = "USD"
    if isinstance(primary.data, dict):
        periods = primary.data.get("data", [])
        currency = primary.data.get("currency", "USD")

    anomalies = _validator.detect_anomalies(periods, currency)

    # Three-statement reconciliation on latest period
    reconciliations = []
    if periods:
        reconciliations = _validator.reconcile_statements(periods[0])

    # Build confidence with anomaly info
    confidence = cv.confidence
    confidence.anomalies = [a.detail for a in anomalies]

    output = {
        "success": True,
        "identifier": identifier,
        "sources_used": [r.source for r in results],
        "data_source": primary.source,
        "fetched_at": _fetched_at(),
        "confidence": asdict(confidence),
        "cross_validation": {
            "discrepancies": cv.discrepancies,
            "reconciled_values": cv.reconciled,
        },
        "anomalies": [asdict(a) for a in anomalies],
        "reconciliations": [asdict(r) for r in reconciliations],
        "latest_period": periods[0] if periods else None,
    }

    return json.dumps(output, ensure_ascii=False, default=str)


@mcp.tool()
async def company_valuation(identifier: str, method: str = "dcf") -> str:
    """Get valuation parameters for a company (WACC components, growth rates, peer multiples).

    Args:
        identifier: Company name or ticker symbol
        method: "dcf", "comps", "ddm", or "all" (default: "dcf")
    """
    result = await _valuation.get_valuation(identifier, method=method)
    if result.has_data():
        data = _to_dict(result.data)
        data["data_source"] = result.source
        data["fetched_at"] = _fetched_at()
        return json.dumps({"success": True, **data}, ensure_ascii=False, default=str)

    return json.dumps({
        "success": False, "identifier": identifier,
        "error": result.error or "Valuation parameters unavailable.",
    }, ensure_ascii=False)


if __name__ == "__main__":
    mcp.run()
