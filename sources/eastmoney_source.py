"""Eastmoney (东方财富) data source — L1 primary for China-accessible networks.

Uses eastmoney's public stock data API endpoints.
"""

import json
import logging
import re
import time
from typing import Any

import httpx

from .base import BaseSource, DataResult, CompanyProfileData

logger = logging.getLogger(__name__)

# Eastmoney public API endpoints
EM_FINANCIAL_API = "https://datacenter-web.eastmoney.com/api/data/v1/get"
EM_STOCK_INFO_API = "https://push2.eastmoney.com/api/qt/stock/get"


class EastmoneySource(BaseSource):
    name = "eastmoney"

    async def get_financials(
        self, identifier: str, period: str = "annual", years: int = 3
    ) -> DataResult:
        secucode = self._resolve_secucode(identifier)
        if not secucode:
            return DataResult(success=False, error=f"Cannot resolve code for: {identifier}")

        code, market = secucode.split(".") if "." in secucode else (secucode, "SH")

        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Referer": "https://quote.eastmoney.com/",
            }
            async with httpx.AsyncClient(timeout=15, follow_redirects=True, headers=headers) as client:
                # Use eastmoney datacenter API for financial data
                params = {
                    "reportName": "RPT_LICO_FN_CPD",
                    "columns": "ALL",
                    "filter": f'(SECURITY_CODE="{code}")',
                    "pageNumber": "1",
                    "pageSize": str(years),
                    "sortTypes": "-1",
                    "sortColumns": "NOTICE_DATE",
                    "source": "WEB",
                    "client": "WEB",
                }
                resp = await client.get(EM_FINANCIAL_API, params=params)
                resp.raise_for_status()
                data = resp.json()

                if not data or str(data.get("code")) != "0" or not data.get("result"):
                    return DataResult(success=False, error="No data from eastmoney API")

                items = data["result"].get("data", [])
                if not items:
                    return DataResult(success=False, error="Empty data from eastmoney")

                result_data = []
                for item in items[:years]:
                    result_data.append({
                        "year": _em_extract_year(item.get("REPORT_DATE") or item.get("NOTICE_DATE", "")),
                        "quarter": "",
                        "revenue": _em_to_float(item.get("TOTAL_OPERATE_INCOME")),
                        "gross_profit": _em_to_float(item.get("OPERATE_INCOME")),
                        "net_income": _em_to_float(item.get("PARENT_NETPROFIT")),
                        "operating_cash_flow": _em_to_float(item.get("NETCASH_OPERATE")),
                        "total_assets": _em_to_float(item.get("TOTAL_ASSETS")),
                        "total_liabilities": _em_to_float(item.get("TOTAL_LIABILITIES")),
                        "currency": "CNY",
                    })

                if not result_data or all(d["year"] == 0 for d in result_data):
                    return DataResult(success=False, error="No valid financial rows parsed")

                return DataResult(
                    success=True,
                    data={"company": identifier, "ticker": secucode, "currency": "CNY", "data": result_data},
                    source="eastmoney",
                )

        except Exception as e:
            logger.warning(f"eastmoney get_financials failed for {identifier}: {e}")
            return DataResult(success=False, error=str(e))

    async def get_profile(self, identifier: str) -> DataResult:
        secucode = self._resolve_secucode(identifier)
        if not secucode:
            return DataResult(success=False, error=f"Cannot resolve code for: {identifier}")

        code, market = secucode.split(".") if "." in secucode else (secucode, "SH")
        # eastmoney uses market code: 0=深圳, 1=上海
        secid = f"1.{code}" if market == "SH" else f"0.{code}"

        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Referer": "https://quote.eastmoney.com/",
            }
            async with httpx.AsyncClient(timeout=15, follow_redirects=True, headers=headers) as client:
                params = {
                    "secid": secid,
                    "fields": "f57,f58,f84,f116,f117,f162,f167,f170,f171,f173,f187,f190,f192",
                }
                resp = await client.get(EM_STOCK_INFO_API, params=params)
                resp.raise_for_status()
                data = resp.json()

                if not data or not data.get("data"):
                    return DataResult(success=False, error="No profile data from eastmoney")

                d = data["data"]
                return DataResult(
                    success=True,
                    data=CompanyProfileData(
                        name=d.get("f58", identifier),
                        ticker=secucode,
                        exchange=market,
                        industry=d.get("f187", ""),
                        sector="",
                        market_cap=d.get("f116"),
                        pe_ratio=d.get("f162"),
                        ps_ratio=d.get("f167"),
                        pb_ratio=d.get("f167"),
                        description="",
                    ),
                    source="eastmoney",
                )

        except Exception as e:
            logger.warning(f"eastmoney get_profile failed for {identifier}: {e}")
            return DataResult(success=False, error=str(e))

    async def get_peers(self, identifier: str) -> DataResult:
        return DataResult(success=False, error="eastmoney: peer lookup not supported")

    async def get_market_data(
        self, industry: str, region: str = "global", metric: str = ""
    ) -> DataResult:
        return DataResult(success=False, error="eastmoney: market data not supported")

    async def get_news(self, query: str, limit: int = 5) -> DataResult:
        """Search news via eastmoney search API (JSONP)."""
        try:
            url = "https://search-api-web.eastmoney.com/search/jsonp"
            cb = f"jQuery{int(time.time() * 1000)}_{int(time.time() * 1000)}"
            param = json.dumps({
                "uid": "",
                "keyword": query,
                "type": ["cmsArticleWebOld"],
                "client": "web",
                "clientType": "web",
                "clientVersion": "curr",
                "param": {
                    "cmsArticleWebOld": {
                        "searchScope": "default",
                        "sort": "default",
                        "pageIndex": 1,
                        "pageSize": limit,
                        "preTag": "",
                        "postTag": "",
                    }
                },
            }, ensure_ascii=False)

            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Referer": "https://so.eastmoney.com/",
            }

            async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
                resp = await client.get(url, params={"cb": cb, "param": param}, headers=headers)
                resp.raise_for_status()
                text = resp.text

                if not text:
                    return DataResult(success=False, error="Empty response from eastmoney search")

                # Strip JSONP callback: jQuery_xxx({...})
                start = text.index("(")
                end = text.rindex(")")
                data = json.loads(text[start + 1:end])

                articles = data.get("result", {}).get("cmsArticleWebOld", [])
                if not articles:
                    return DataResult(success=False, error="No news from eastmoney search")

                results = []
                for art in articles[:limit]:
                    title = art.get("title", "")
                    title = re.sub(r'<[^>]+>', '', title)
                    results.append({
                        "title": title,
                        "source": art.get("source", ""),
                        "date": art.get("date", ""),
                        "snippet": art.get("content", "")[:200] if art.get("content") else "",
                        "url": art.get("url", ""),
                    })

                return DataResult(
                    success=True,
                    data={"query": query, "results": results},
                    source="eastmoney",
                )

        except Exception as e:
            logger.warning(f"eastmoney get_news failed for {query}: {e}")
            return DataResult(success=False, error=str(e))

    def _resolve_secucode(self, identifier: str) -> str | None:
        from .yfinance_source import _load_ticker_map
        ticker_map = _load_ticker_map()

        if identifier in ticker_map:
            t = ticker_map[identifier]
            if t.startswith("PRIVATE:"):
                return None
            if t.endswith(".SS"):
                return f"{t.split('.')[0]}.SH"
            if t.endswith(".SZ"):
                return t
            if t.endswith(".HK"):
                # HK-listed company may also have A-share listing
                result = self._search_secucode(identifier)
                if result:
                    return result
                return None

        if identifier.isdigit() and len(identifier) == 6:
            if identifier.startswith("6"):
                return f"{identifier}.SH"
            return f"{identifier}.SZ"

        # Try to resolve as A-share code via eastmoney datacenter search
        return self._search_secucode(identifier)

    def _search_secucode(self, name: str) -> str | None:
        """Search for A-share stock code by company name via eastmoney API."""
        try:
            import httpx as _httpx
            url = "https://searchapi.eastmoney.com/api/suggest/get"
            params = {
                "input": name,
                "type": "14",
                "token": "D43BF722C8E33BDC906FB84D85E326E8",
                "count": "5",
            }
            with _httpx.Client(timeout=5, follow_redirects=True) as client:
                r = client.get(url, params=params)
                r.raise_for_status()
                data = r.json()
            items = data.get("QuotationCodeTable", {}).get("Data", [])
            for item in items:
                code = item.get("Code", "")
                mkt = item.get("MktNum", "")
                if mkt in ("0", "1") and len(code) == 6:
                    market = "SH" if mkt == "1" else "SZ"
                    return f"{code}.{market}"
            return None
        except Exception:
            return None


def _em_to_float(val: Any) -> float | None:
    if val is None or val == "-" or val == "":
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def _em_extract_year(date_str: str) -> int:
    try:
        return int(str(date_str)[:4])
    except (ValueError, IndexError):
        return 0
