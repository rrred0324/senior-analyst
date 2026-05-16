"""Financial Modeling Prep (FMP) data source — Tier 1 (requires API key).

Provides comprehensive global financial data, industry classification,
structured company news, and peer recommendations.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any

import httpx

from .base import BaseSource, DataResult, FinancialData, CompanyProfileData
from .config import FMP_KEY, cache_key, get_cache

logger = logging.getLogger(__name__)

FMP_BASE = "https://financialmodelingprep.com/api/v3"


class FMPSource(BaseSource):
    name = "fmp"

    def __init__(self):
        if not FMP_KEY:
            raise RuntimeError("FMP API key not configured (SENIOR_ANALYST_FMP_KEY)")
        self._apikey = FMP_KEY

    async def _get(self, path: str, params: dict | None = None, timeout: float = 5.0) -> dict | list | None:
        """Make an FMP API request."""
        p = params or {}
        p["apikey"] = self._apikey
        try:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                resp = await client.get(f"{FMP_BASE}/{path}", params=p)
                resp.raise_for_status()
                data = resp.json()
                if isinstance(data, dict) and "Error Message" in data:
                    logger.warning(f"FMP error: {data['Error Message']}")
                    return None
                return data
        except Exception as e:
            logger.warning(f"FMP request failed ({path}): {e}")
            return None

    async def _get_v4(self, path: str, params: dict | None = None, timeout: float = 5.0) -> dict | list | None:
        """Make an FMP v4 API request."""
        p = params or {}
        p["apikey"] = self._apikey
        try:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                resp = await client.get(f"https://financialmodelingprep.com/api/v4/{path}", params=p)
                resp.raise_for_status()
                data = resp.json()
                if isinstance(data, dict) and "Error Message" in data:
                    return None
                return data
        except Exception as e:
            logger.warning(f"FMP v4 request failed ({path}): {e}")
            return None

    def _resolve_ticker(self, identifier: str) -> str | None:
        """Resolve company name to ticker symbol."""
        from .yfinance_source import _load_ticker_map
        ticker_map = _load_ticker_map()
        if identifier in ticker_map:
            t = ticker_map[identifier]
            if t.startswith("PRIVATE:"):
                return None
            return t
        # If it looks like a ticker already
        if identifier.isupper() or "." in identifier:
            return identifier
        return None

    async def _search_ticker(self, name: str) -> str | None:
        """Search for ticker by company name."""
        data = await self._get("search", {"query": name, "limit": "5"})
        if not data or not isinstance(data, list):
            return None
        for item in data:
            sym = item.get("symbol", "")
            if sym:
                return sym
        return None

    async def get_financials(
        self, identifier: str, period: str = "annual", years: int = 3
    ) -> DataResult:
        ticker = self._resolve_ticker(identifier) or await self._search_ticker(identifier)
        if not ticker:
            return DataResult(success=False, error=f"FMP: cannot resolve ticker for {identifier}")

        # Check cache
        ck = cache_key("financials", ticker, period, years)
        cache = get_cache("financials")
        if ck in cache:
            return cache[ck]

        stmt = "income-statement" if period == "annual" else "income-statement-growth"
        data = await self._get(f"income-statement/{ticker}", {"period": period, "limit": str(years)})
        if not data or not isinstance(data, list):
            return DataResult(success=False, error="FMP: no income statement data")

        # Get balance sheet and cash flow too for completeness
        bs_data = await self._get(f"balance-sheet-statement/{ticker}", {"period": period, "limit": str(years)})
        cf_data = await self._get(f"cash-flow-statement/{ticker}", {"period": period, "limit": str(years)})

        result_rows = []
        for i, item in enumerate(data[:years]):
            year = item.get("calendarYear", "") or str(item.get("date", ""))[:4]
            bs = bs_data[i] if bs_data and isinstance(bs_data, list) and i < len(bs_data) else {}
            cf = cf_data[i] if cf_data and isinstance(cf_data, list) and i < len(cf_data) else {}
            row = {
                "year": int(year) if year.isdigit() else 0,
                "quarter": "",
                "revenue": item.get("revenue"),
                "gross_profit": item.get("grossProfit"),
                "net_income": item.get("netIncome"),
                "operating_cash_flow": cf.get("operatingCashFlow"),
                "total_assets": bs.get("totalAssets"),
                "total_liabilities": bs.get("totalLiabilities"),
                "shares_outstanding": item.get("weightedAverageShsOut"),
                "eps": item.get("eps"),
                "operating_expenses": item.get("operatingExpenses"),
                "rd_expenses": item.get("researchAndDevelopmentExpenses"),
                "ebitda": item.get("ebitda"),
                "dividends": cf.get("dividendsPaid"),
                "currency": item.get("reportedCurrency", "USD"),
            }
            capex = cf.get("capitalExpenditure")
            ocf = cf.get("operatingCashFlow")
            if ocf is not None and capex is not None:
                row["free_cash_flow"] = ocf + capex
            result_rows.append(row)

        if not result_rows:
            return DataResult(success=False, error="FMP: no financial rows parsed")

        result = DataResult(
            success=True,
            data={"company": identifier, "ticker": ticker, "currency": result_rows[0].get("currency", "USD"), "data": result_rows},
            source="fmp",
        )
        cache[ck] = result
        return result

    async def get_profile(self, identifier: str) -> DataResult:
        ticker = self._resolve_ticker(identifier) or await self._search_ticker(identifier)
        if not ticker:
            return DataResult(success=False, error=f"FMP: cannot resolve ticker for {identifier}")

        ck = cache_key("profile", ticker)
        cache = get_cache("profile")
        if ck in cache:
            return cache[ck]

        data = await self._get(f"profile/{ticker}")
        if not data or not isinstance(data, list) or not data:
            return DataResult(success=False, error="FMP: no profile data")

        d = data[0]
        result = DataResult(
            success=True,
            data=CompanyProfileData(
                name=d.get("companyName", identifier),
                ticker=ticker,
                exchange=d.get("exchangeShortName", ""),
                industry=d.get("industry", ""),
                sector=d.get("sector", ""),
                market_cap=d.get("mktCap"),
                pe_ratio=d.get("price"),
                ps_ratio=None,
                pb_ratio=None,
                description=d.get("description", ""),
            ),
            source="fmp",
        )
        cache[ck] = result
        return result

    async def get_peers(self, identifier: str) -> DataResult:
        ticker = self._resolve_ticker(identifier) or await self._search_ticker(identifier)
        if not ticker:
            return DataResult(success=False, error=f"FMP: cannot resolve ticker for {identifier}")

        ck = cache_key("peers", ticker)
        cache = get_cache("peers")
        if ck in cache:
            return cache[ck]

        # FMP stock peers endpoint
        data = await self._get(f"stock_peers/{ticker}")
        if not data or not isinstance(data, list) or not data:
            return DataResult(success=False, error="FMP: no peer data")

        d = data[0]
        peers = d.get("peersList", []) if isinstance(d, dict) else []
        result = DataResult(
            success=True,
            data={"peer_tickers": peers[:8]},
            source="fmp",
        )
        cache[ck] = result
        return result

    async def get_market_data(
        self, industry: str, region: str = "global", metric: str = ""
    ) -> DataResult:
        # FMP doesn't have great free-tier market/industry data
        # Try stock sector performance as a basic signal
        try:
            data = await self._get("sector-performance")
            if data and isinstance(data, list):
                return DataResult(
                    success=True,
                    data={"industry": industry, "region": region, "sector_performance": data[:10]},
                    source="fmp",
                )
        except Exception:
            pass
        return DataResult(success=False, error="FMP: market data not available for this query")

    async def get_news(self, query: str, limit: int = 5) -> DataResult:
        """Get company news from FMP."""
        try:
            data = await self._get("stock_news", {"tickers": query, "limit": str(limit)})
            if not data or not isinstance(data, list):
                return DataResult(success=False, error="FMP: no news data")

            results = []
            for art in data[:limit]:
                results.append({
                    "title": art.get("title", ""),
                    "source": art.get("site", ""),
                    "date": art.get("publishedDate", ""),
                    "snippet": (art.get("text", "") or "")[:200],
                    "url": art.get("url", ""),
                    "ticker": art.get("symbol", ""),
                })

            return DataResult(
                success=True,
                data={"query": query, "results": results},
                source="fmp",
            )
        except Exception as e:
            return DataResult(success=False, error=str(e))

    async def get_industry_data(
        self, industry: str, region: str = "global", metric: str = ""
    ) -> DataResult:
        """Get industry classification and peer data from FMP."""
        # FMP has stock screener by sector/industry
        try:
            data = await self._get("stock-screener", {
                "exchange": region if region != "global" else "",
                "limit": "20",
                "industry": industry,
            })
            if not data or not isinstance(data, list):
                return DataResult(success=False, error="FMP: no industry data")

            stocks = []
            for s in data[:20]:
                stocks.append({
                    "code": s.get("symbol", ""),
                    "name": s.get("companyName", ""),
                    "market_cap": s.get("marketCap"),
                    "pe_ratio": s.get("peRatio"),
                    "price": s.get("price"),
                })

            return DataResult(
                success=True,
                data={
                    "industry": industry,
                    "region": region,
                    "classification_system": "FMP industry",
                    "constituent_stocks": stocks,
                    "data_source": "fmp",
                    "fetched_at": datetime.now(timezone.utc).isoformat(),
                },
                source="fmp",
            )
        except Exception as e:
            return DataResult(success=False, error=str(e))

    async def get_stock_news(
        self, identifier: str, days: int = 7, limit: int = 10
    ) -> DataResult:
        """Get company-specific news from FMP."""
        ticker = self._resolve_ticker(identifier) or await self._search_ticker(identifier)
        if not ticker:
            return DataResult(success=False, error=f"FMP: cannot resolve ticker for {identifier}")

        try:
            data = await self._get("stock_news", {"tickers": ticker, "limit": str(limit)})
            if not data or not isinstance(data, list):
                return DataResult(success=False, error="FMP: no stock news")

            articles = []
            for art in data[:limit]:
                articles.append({
                    "title": art.get("title", ""),
                    "source": art.get("site", ""),
                    "date": art.get("publishedDate", ""),
                    "url": art.get("url", ""),
                })

            return DataResult(
                success=True,
                data={
                    "identifier": identifier,
                    "ticker": ticker,
                    "articles": articles,
                    "announcements": [],
                    "data_source": "fmp",
                    "fetched_at": datetime.now(timezone.utc).isoformat(),
                },
                source="fmp",
            )
        except Exception as e:
            return DataResult(success=False, error=str(e))
