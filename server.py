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
    FMPSource, AlphaVantageSource, NewsAPISource,
)
from sources.config import build_source_registry, AVAILABLE_SOURCES, compute_timeouts

mcp = FastMCP(
    "senior_analyst",
    instructions=(
        "Financial and business data server for Senior Analyst skill. "
        "Use company_financials for financial statements, "
        "company_profile for company info and valuation, competitor_compare for peer analysis, "
        "market_data for industry/market data, news_search for recent news, "
        "industry_data for industry classification and constituents, "
        "stock_news for company-specific news and announcements. "
        "Supports company names (Chinese or English) and ticker symbols. "
        "No API keys required for basic data; configure keys for enhanced sources."
    ),
)

# --- Initialize sources ---

_yfinance = YFinanceSource()
_akshare = AkshareSource()
_eastmoney = EastmoneySource()

_fmp = None
_av = None
_newsapi = None

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

# Build source registry after all sources are initialized
build_source_registry()

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

    # L1: FMP (best peer data when available)
    if _fmp:
        try:
            profile_result = await _fmp.get_profile(identifier)
            peers_result = await _fmp.get_peers(identifier)
            if profile_result.has_data() or peers_result.has_data():
                profile = _to_dict(profile_result.data) if profile_result.has_data() else {}
                target_data = {
                    "name": profile.get("name", identifier),
                    "ticker": profile.get("ticker", identifier),
                    "industry": profile.get("industry", ""),
                    "sector": profile.get("sector", ""),
                }
                fin_result = await _fmp.get_financials(identifier, years=1)
                if fin_result.has_data():
                    latest = fin_result.data.get("data", [{}])[0] if isinstance(fin_result.data, dict) and fin_result.data.get("data") else {}
                    revenue = latest.get("revenue")
                    net_income = latest.get("net_income")
                    target_data["revenue"] = revenue
                    target_data["net_margin"] = round(net_income / revenue, 4) if revenue and net_income and revenue != 0 else None
                    target_data["ps_ratio"] = profile.get("ps_ratio")

                peer_tickers = []
                if peers_result.has_data():
                    peer_tickers = peers_result.data.get("peer_tickers", [])

                for pt in peer_tickers[:5]:
                    p_profile = await _fmp.get_profile(pt)
                    p_fin = await _fmp.get_financials(pt, years=1)
                    peer = {"name": pt, "ticker": pt}
                    if p_profile.has_data():
                        pp = _to_dict(p_profile.data)
                        peer["name"] = pp.get("name", pt)
                        peer["industry"] = pp.get("industry", "")
                    if p_fin.has_data():
                        latest = p_fin.data.get("data", [{}])[0] if isinstance(p_fin.data, dict) and p_fin.data.get("data") else {}
                        rev = latest.get("revenue")
                        ni = latest.get("net_income")
                        peer["revenue"] = rev
                        peer["net_margin"] = round(ni / rev, 4) if rev and ni and rev != 0 else None
                    if p_profile.has_data():
                        pp = _to_dict(p_profile.data)
                        peer["ps_ratio"] = pp.get("ps_ratio")
                    peers_data.append(peer)

                source = "fmp"
        except Exception:
            pass

    # L2: yfinance (if FMP didn't work)
    if not peers_data:
        profile_result = await _yfinance.get_profile(identifier)
        peers_result = await _yfinance.get_peers(identifier)

        if profile_result.has_data() or peers_result.has_data():
            profile = _to_dict(profile_result.data) if profile_result.has_data() else {}
            target_data = {
                "name": profile.get("name", identifier),
                "ticker": profile.get("ticker", identifier),
                "industry": profile.get("industry", ""),
                "sector": profile.get("sector", ""),
            }
            fin_result = await _yfinance.get_financials(identifier, years=1)
            if fin_result.has_data():
                latest = fin_result.data.get("data", [{}])[0] if isinstance(fin_result.data, dict) and fin_result.data.get("data") else {}
                revenue = latest.get("revenue")
                net_income = latest.get("net_income")
                target_data["revenue"] = revenue
                target_data["net_margin"] = round(net_income / revenue, 4) if revenue and net_income and revenue != 0 else None
                target_data["ps_ratio"] = profile.get("ps_ratio")

            peer_tickers = []
            if peers_result.has_data():
                peer_tickers = peers_result.data.get("peer_tickers", [])

            for pt in peer_tickers[:5]:
                p_profile = await _yfinance.get_profile(pt)
                p_fin = await _yfinance.get_financials(pt, years=1)
                peer = {"name": pt, "ticker": pt}
                if p_profile.has_data():
                    pp = _to_dict(p_profile.data)
                    peer["name"] = pp.get("name", pt)
                    peer["industry"] = pp.get("industry", "")
                if p_fin.has_data():
                    latest = p_fin.data.get("data", [{}])[0] if isinstance(p_fin.data, dict) and p_fin.data.get("data") else {}
                    rev = latest.get("revenue")
                    ni = latest.get("net_income")
                    peer["revenue"] = rev
                    peer["net_margin"] = round(ni / rev, 4) if rev and ni and rev != 0 else None
                if p_profile.has_data():
                    pp = _to_dict(p_profile.data)
                    peer["ps_ratio"] = pp.get("ps_ratio")
                peers_data.append(peer)

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


if __name__ == "__main__":
    mcp.run()
