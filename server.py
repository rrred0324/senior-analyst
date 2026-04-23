"""Senior Analyst MCP Server — structured financial/business data for Claude Code."""

import sys
import os
import logging
import json
import re
from dataclasses import asdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

from mcp.server.fastmcp import FastMCP
from sources import YFinanceSource, AkshareSource, EastmoneySource

mcp = FastMCP(
    "senior_analyst",
    instructions=(
        "Financial and business data server for Senior Analyst skill. "
        "Use company_financials for financial statements, "
        "company_profile for company info and valuation, competitor_compare for peer analysis, "
        "market_data for industry/market data, and news_search for recent news. "
        "Supports company names (Chinese or English) and ticker symbols. No API keys required."
    ),
)

_yfinance = YFinanceSource()
_akshare = AkshareSource()
_eastmoney = EastmoneySource()


def _to_dict(data):
    if hasattr(data, "__dataclass_fields__"):
        return asdict(data)
    return data


@mcp.tool()
async def company_financials(identifier: str, period: str = "annual", years: int = 3) -> str:
    """Get financial data (revenue, profit, cash flow, balance sheet) for a company.

    Args:
        identifier: Company name (e.g., "滴滴", "Apple") or ticker symbol (e.g., "AAPL", "0700.HK")
        period: "annual" or "quarterly"
        years: Number of years/quarters to retrieve (default 3)
    """
    # L1: eastmoney (most reliable for China-accessible networks)
    result = await _eastmoney.get_financials(identifier, period, years)
    if result.has_data():
        return json.dumps({"success": True, **_to_dict(result.data), "source": result.source}, ensure_ascii=False, default=str)

    # L2: akshare
    result = await _akshare.get_financials(identifier, period, years)
    if result.has_data():
        return json.dumps({"success": True, **_to_dict(result.data), "source": result.source}, ensure_ascii=False, default=str)

    # L3: yfinance (fallback for overseas networks)
    result = await _yfinance.get_financials(identifier, period, years)
    if result.has_data():
        return json.dumps({"success": True, **_to_dict(result.data), "source": result.source}, ensure_ascii=False, default=str)

    # All failed
    return json.dumps({
        "success": False, "identifier": identifier,
        "error": "All data sources unavailable. Try WebSearch or provide data manually.",
    }, ensure_ascii=False)


@mcp.tool()
async def company_profile(identifier: str) -> str:
    """Get company profile including industry, sector, market cap, and valuation ratios.

    Args:
        identifier: Company name (e.g., "滴滴", "Apple") or ticker symbol (e.g., "AAPL", "0700.HK")
    """
    # L1: eastmoney
    result = await _eastmoney.get_profile(identifier)
    if result.has_data():
        return json.dumps({"success": True, **_to_dict(result.data), "source": result.source}, ensure_ascii=False, default=str)

    # L2: akshare
    result = await _akshare.get_profile(identifier)
    if result.has_data():
        return json.dumps({"success": True, **_to_dict(result.data), "source": result.source}, ensure_ascii=False, default=str)

    # L3: yfinance
    result = await _yfinance.get_profile(identifier)
    if result.has_data():
        return json.dumps({"success": True, **_to_dict(result.data), "source": result.source}, ensure_ascii=False, default=str)

    return json.dumps({
        "success": False, "identifier": identifier,
        "error": "All data sources unavailable for profile lookup.",
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

    # Try yfinance first (best peer data when available)
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
    else:
        # Fallback: use eastmoney/akshare for China-accessible competitor data
        # Step 1: Get target company industry via akshare
        ak_profile = await _akshare.get_profile(identifier)
        if ak_profile.has_data():
            ak_data = _to_dict(ak_profile.data)
            target_data = {
                "name": ak_data.get("name", identifier),
                "ticker": ak_data.get("ticker", identifier),
                "industry": ak_data.get("industry", ""),
                "sector": ak_data.get("sector", ""),
                "pe_ratio": ak_data.get("pe_ratio"),
                "pb_ratio": ak_data.get("pb_ratio"),
            }

        # Step 2: Get target financials via eastmoney
        em_fin = await _eastmoney.get_financials(identifier, years=1)
        if em_fin.has_data():
            latest = em_fin.data.get("data", [{}])[0] if isinstance(em_fin.data, dict) and em_fin.data.get("data") else {}
            revenue = latest.get("revenue")
            net_income = latest.get("net_income")
            target_data["revenue"] = revenue
            target_data["net_income"] = net_income
            target_data["net_margin"] = round(net_income / revenue, 4) if revenue and net_income and revenue != 0 else None

        # Step 3: Try to find same-industry companies
        industry = target_data.get("industry", "")
        if industry:
            # Sanitize industry to prevent filter injection
            industry_safe = re.sub(r'[^\w一-鿿\s]', '', industry).strip()
            if industry_safe:
                try:
                    import httpx
                    em_url = "https://datacenter-web.eastmoney.com/api/data/v1/get"
                    params = {
                        "reportName": "RPT_LICO_FN_CPD",
                        "columns": "SECURITY_CODE,SECURITY_NAME_ABBR,TOTAL_OPERATE_INCOME,PARENT_NETPROFIT",
                        "filter": f'(SECURITY_NAME_ABBR like "%{industry_safe}%")',
                        "pageNumber": "1",
                        "pageSize": "10",
                        "sortTypes": "-1",
                        "sortColumns": "TOTAL_OPERATE_INCOME",
                        "source": "WEB",
                        "client": "WEB",
                    }
                    async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
                        resp = await client.get(em_url, params=params)
                        resp.raise_for_status()
                        data = resp.json()
                        items = data.get("result", {}).get("data", []) if data.get("result") else []
                        for item in items[:5]:
                            code = item.get("SECURITY_CODE", "")
                            if code == target_data.get("ticker", ""):
                                continue
                            rev = item.get("TOTAL_OPERATE_INCOME")
                            ni = item.get("PARENT_NETPROFIT")
                            peers_data.append({
                                "name": item.get("SECURITY_NAME_ABBR", ""),
                                "ticker": code,
                                "revenue": rev,
                                "net_income": ni,
                                "net_margin": round(ni / rev, 4) if rev and ni and rev != 0 else None,
                            })
                        if peers_data:
                            source = "eastmoney"
                except Exception:
                    pass

        if not industry and not target_data.get("revenue"):
            return json.dumps({
                "success": False, "identifier": identifier,
                "error": "Cannot find company or peers. Try a specific stock code (e.g., '600519').",
            }, ensure_ascii=False)

    result = {
        "success": True,
        "target": target_data,
        "peers": peers_data,
        "source": source,
    }
    if source == "eastmoney":
        result["note"] = "Peer data from eastmoney. Peers based on industry match. Specify tickers for more control."
    elif source == "yfinance":
        result["note"] = "Peer list based on yfinance recommendations. Specify tickers for more control."
    else:
        result["note"] = "Limited peer data available. Consider specifying competitor tickers manually."

    return json.dumps(result, ensure_ascii=False, default=str)


@mcp.tool()
async def market_data(industry: str, region: str = "global", metric: str = "") -> str:
    """Get market size, growth rate, and industry-level data.

    Args:
        industry: Industry name (e.g., "ride-hailing", "insurance", "ev")
        region: Geographic region (default "global")
        metric: Specific metric to query (optional)
    """
    result = await _akshare.get_market_data(industry, region, metric)
    if result.has_data():
        return json.dumps({
            "success": True, **_to_dict(result.data),
            "disclaimer": "Market data from free sources may be limited. Use WebSearch for comprehensive reports.",
        }, ensure_ascii=False, default=str)

    return json.dumps({
        "success": False, "industry": industry, "region": region,
        "error": "No market data from free sources. Market size typically requires paid research.",
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
    # L1: akshare (eastmoney news via stock_news_em)
    result = await _akshare.get_news(query, limit)
    if result.has_data():
        return json.dumps({"success": True, **_to_dict(result.data), "source": result.source}, ensure_ascii=False, default=str)

    # L2: eastmoney search API
    result = await _eastmoney.get_news(query, limit)
    if result.has_data():
        return json.dumps({"success": True, **_to_dict(result.data), "source": result.source}, ensure_ascii=False, default=str)

    # L3: sina finance
    try:
        import httpx

        url = "https://feed.mix.sina.com.cn/api/roll/get"
        params = {
            "pageid": "153",
            "lid": "2516",
            "k": query,
            "num": limit,
            "page": 1,
        }
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            items = data.get("result", {}).get("data", [])
            results = []
            for item in items[:limit]:
                title = item.get("title", "")
                if not title:
                    continue
                results.append({
                    "title": title,
                    "url": item.get("url", ""),
                    "date": item.get("ctime", ""),
                    "source": item.get("author", item.get("media_name", "")),
                    "snippet": "",
                })
            if results:
                return json.dumps({
                    "success": True, "query": query, "results": results, "source": "sina_finance",
                }, ensure_ascii=False)
    except Exception:
        pass

    return json.dumps({
        "success": False, "query": query,
        "error": "News sources unavailable. Try WebSearch in main session.",
    }, ensure_ascii=False)


if __name__ == "__main__":
    mcp.run()
