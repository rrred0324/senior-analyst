"""Alpha Vantage data source — Tier 1 (requires API key).

Provides global stock fundamentals, news with sentiment, and technical indicators.
Free tier: 25 requests/day.
"""

import logging
from datetime import datetime, timezone
from typing import Any

import httpx

from .base import BaseSource, DataResult, CompanyProfileData
from .config import AV_KEY, cache_key, get_cache

logger = logging.getLogger(__name__)

AV_BASE = "https://www.alphavantage.co/query"


class AlphaVantageSource(BaseSource):
    name = "alphavantage"

    def __init__(self):
        if not AV_KEY:
            raise RuntimeError("Alpha Vantage API key not configured (SENIOR_ANALYST_AV_KEY)")
        self._apikey = AV_KEY

    async def _get(self, params: dict, timeout: float = 5.0) -> dict | None:
        """Make an Alpha Vantage API request."""
        params["apikey"] = self._apikey
        try:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                resp = await client.get(AV_BASE, params=params)
                resp.raise_for_status()
                data = resp.json()
                if "Error Message" in data or "Note" in data:
                    msg = data.get("Error Message") or data.get("Note", "rate limited")
                    logger.warning(f"AV error: {msg}")
                    return None
                return data
        except Exception as e:
            logger.warning(f"AV request failed: {e}")
            return None

    def _resolve_ticker(self, identifier: str) -> str | None:
        from .yfinance_source import _load_ticker_map
        ticker_map = _load_ticker_map()
        if identifier in ticker_map:
            t = ticker_map[identifier]
            if t.startswith("PRIVATE:"):
                return None
            # AV uses different suffix: .SHSE, .SZSE, .HKG
            if t.endswith(".SS"):
                return t.replace(".SS", ".SHSE")
            if t.endswith(".SZ"):
                return t.replace(".SZ", ".SZSE")
            if t.endswith(".HK"):
                return t.replace(".HK", ".HKG")
            return t
        return None

    async def get_financials(
        self, identifier: str, period: str = "annual", years: int = 3
    ) -> DataResult:
        ticker = self._resolve_ticker(identifier) or identifier
        # AV's OVERVIEW + INCOME_STATEMENT endpoints
        data = await self._get({
            "function": "INCOME_STATEMENT",
            "symbol": ticker,
        })
        if not data:
            return DataResult(success=False, error="AV: no income statement")

        reports = data.get("annualReports", []) if period == "annual" else data.get("quarterlyReports", [])
        if not reports:
            return DataResult(success=False, error="AV: no reports found")

        result_rows = []
        for report in reports[:years]:
            date_str = report.get("fiscalDateEnding", "")
            year = int(date_str[:4]) if date_str and len(date_str) >= 4 else 0
            result_rows.append({
                "year": year,
                "quarter": "",
                "revenue": _av_float(report.get("totalRevenue")),
                "gross_profit": _av_float(report.get("grossProfit")),
                "net_income": _av_float(report.get("netIncome")),
                "operating_cash_flow": None,
                "total_assets": None,
                "total_liabilities": None,
                "currency": report.get("reportedCurrency", "USD"),
            })

        if not result_rows:
            return DataResult(success=False, error="AV: no financial rows parsed")

        return DataResult(
            success=True,
            data={"company": identifier, "ticker": ticker, "currency": result_rows[0].get("currency", "USD"), "data": result_rows},
            source="alphavantage",
        )

    async def get_profile(self, identifier: str) -> DataResult:
        ticker = self._resolve_ticker(identifier) or identifier

        ck = cache_key("profile", ticker)
        cache = get_cache("profile")
        if ck in cache:
            return cache[ck]

        data = await self._get({"function": "OVERVIEW", "symbol": ticker})
        if not data or "Symbol" not in data:
            return DataResult(success=False, error="AV: no overview data")

        result = DataResult(
            success=True,
            data=CompanyProfileData(
                name=data.get("Name", identifier),
                ticker=ticker,
                exchange=data.get("Exchange", ""),
                industry=data.get("Industry", ""),
                sector=data.get("Sector", ""),
                market_cap=_av_float(data.get("MarketCapitalization")),
                pe_ratio=_av_float(data.get("PERatio")),
                ps_ratio=_av_float(data.get("PriceToSalesRatioTTM")),
                pb_ratio=_av_float(data.get("PriceToBookRatio")),
                description=data.get("Description", ""),
            ),
            source="alphavantage",
        )
        cache[ck] = result
        return result

    async def get_peers(self, identifier: str) -> DataResult:
        return DataResult(success=False, error="AV: peer lookup not supported")

    async def get_market_data(
        self, industry: str, region: str = "global", metric: str = ""
    ) -> DataResult:
        return DataResult(success=False, error="AV: market data not supported")

    async def get_news(self, query: str, limit: int = 5) -> DataResult:
        """Get news with sentiment from Alpha Vantage."""
        try:
            data = await self._get({
                "function": "NEWS_SENTIMENT",
                "tickers": query,
                "limit": str(min(limit, 50)),
            })
            if not data or "feed" not in data:
                return DataResult(success=False, error="AV: no news data")

            results = []
            for item in data["feed"][:limit]:
                ticker_sentiments = item.get("ticker_sentiment", [])
                sentiment_score = None
                sentiment_label = None
                if ticker_sentiments:
                    ts = ticker_sentiments[0]
                    sentiment_score = _av_float(ts.get("ticker_sentiment_score"))
                    sentiment_label = ts.get("ticker_sentiment_label", "")

                results.append({
                    "title": item.get("title", ""),
                    "source": item.get("source", ""),
                    "date": item.get("time_published", ""),
                    "snippet": (item.get("summary", "") or "")[:200],
                    "url": item.get("url", ""),
                    "sentiment": sentiment_score,
                    "sentiment_label": sentiment_label,
                })

            return DataResult(
                success=True,
                data={"query": query, "results": results},
                source="alphavantage",
            )
        except Exception as e:
            return DataResult(success=False, error=str(e))

    async def get_stock_news(
        self, identifier: str, days: int = 7, limit: int = 10
    ) -> DataResult:
        """Get company-specific news with sentiment."""
        ticker = self._resolve_ticker(identifier) or identifier
        result = await self.get_news(ticker, limit)
        if result.has_data():
            # Restructure for stock_news format
            articles = result.data.get("results", [])
            result.data = {
                "identifier": identifier,
                "ticker": ticker,
                "articles": articles,
                "announcements": [],
                "data_source": "alphavantage",
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            }
        return result


def _av_float(val: Any) -> float | None:
    if val is None or val == "None" or val == "-":
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None
