"""NewsAPI.org data source — Tier 1 (requires API key).

Provides professional financial news search with source/date filtering.
Free tier: 100 requests/day.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from .base import BaseSource, DataResult
from .config import NEWSAPI_KEY, cache_key, get_cache

logger = logging.getLogger(__name__)

NEWSAPI_BASE = "https://newsapi.org/v2"


class NewsAPISource(BaseSource):
    name = "newsapi"

    def __init__(self):
        if not NEWSAPI_KEY:
            raise RuntimeError("NewsAPI key not configured (SENIOR_ANALYST_NEWSAPI_KEY)")
        self._apikey = NEWSAPI_KEY

    async def get_financials(
        self, identifier: str, period: str = "annual", years: int = 3
    ) -> DataResult:
        return DataResult(success=False, error="NewsAPI: financial data not supported")

    async def get_profile(self, identifier: str) -> DataResult:
        return DataResult(success=False, error="NewsAPI: profile not supported")

    async def get_peers(self, identifier: str) -> DataResult:
        return DataResult(success=False, error="NewsAPI: peers not supported")

    async def get_market_data(
        self, industry: str, region: str = "global", metric: str = ""
    ) -> DataResult:
        return DataResult(success=False, error="NewsAPI: market data not supported")

    async def get_news(self, query: str, limit: int = 5) -> DataResult:
        """Search news via NewsAPI.org everything endpoint."""
        ck = cache_key("news", query, limit)
        cache = get_cache("news")
        if ck in cache:
            return cache[ck]

        try:
            from_date = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")
            params = {
                "q": query,
                "language": "zh" if any("一" <= c <= "鿿" for c in query) else "en",
                "sortBy": "publishedAt",
                "pageSize": str(min(limit, 100)),
                "from": from_date,
            }
            async with httpx.AsyncClient(timeout=8, follow_redirects=True) as client:
                resp = await client.get(
                    f"{NEWSAPI_BASE}/everything",
                    params=params,
                    headers={"X-Api-Key": self._apikey},
                )
                resp.raise_for_status()
                data = resp.json()

            if data.get("status") != "ok" or not data.get("articles"):
                return DataResult(success=False, error="NewsAPI: no articles found")

            results = []
            for art in data["articles"][:limit]:
                title = art.get("title", "")
                if not title or title == "[Removed]":
                    continue
                results.append({
                    "title": title,
                    "source": (art.get("source") or {}).get("name", ""),
                    "date": art.get("publishedAt", ""),
                    "snippet": (art.get("description", "") or "")[:200],
                    "url": art.get("url", ""),
                })

            if not results:
                return DataResult(success=False, error="NewsAPI: no valid articles")

            result = DataResult(
                success=True,
                data={"query": query, "results": results},
                source="newsapi",
            )
            cache[ck] = result
            return result

        except Exception as e:
            logger.warning(f"NewsAPI get_news failed: {e}")
            return DataResult(success=False, error=str(e))

    async def get_stock_news(
        self, identifier: str, days: int = 7, limit: int = 10
    ) -> DataResult:
        """Get company-specific news via NewsAPI."""
        ck = cache_key("stock_news", identifier, days, limit)
        cache = get_cache("stock_news")
        if ck in cache:
            return cache[ck]

        try:
            from_date = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
            params = {
                "q": identifier,
                "sortBy": "publishedAt",
                "pageSize": str(min(limit, 100)),
                "from": from_date,
            }
            async with httpx.AsyncClient(timeout=8, follow_redirects=True) as client:
                resp = await client.get(
                    f"{NEWSAPI_BASE}/everything",
                    params=params,
                    headers={"X-Api-Key": self._apikey},
                )
                resp.raise_for_status()
                data = resp.json()

            if data.get("status") != "ok" or not data.get("articles"):
                return DataResult(success=False, error="NewsAPI: no stock news found")

            articles = []
            for art in data["articles"][:limit]:
                title = art.get("title", "")
                if not title or title == "[Removed]":
                    continue
                articles.append({
                    "title": title,
                    "source": (art.get("source") or {}).get("name", ""),
                    "date": art.get("publishedAt", ""),
                    "url": art.get("url", ""),
                })

            result = DataResult(
                success=True,
                data={
                    "identifier": identifier,
                    "ticker": "",
                    "articles": articles,
                    "announcements": [],
                    "data_source": "newsapi",
                    "fetched_at": datetime.now(timezone.utc).isoformat(),
                },
                source="newsapi",
            )
            cache[ck] = result
            return result

        except Exception as e:
            return DataResult(success=False, error=str(e))
