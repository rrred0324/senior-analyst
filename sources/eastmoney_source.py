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
    use_cache = True

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
                    _revenue = _em_to_float(item.get("TOTAL_OPERATE_INCOME"))
                    _operate_cost = _em_to_float(item.get("OPERATE_COST"))
                    _gross = (_revenue - _operate_cost) if (_revenue is not None and _operate_cost is not None) else None
                    _ocf = _em_to_float(item.get("NETCASH_OPERATE"))
                    _capex = _em_to_float(item.get("CCE_INVEST_ASSETFIX"))
                    _fcf = (_ocf + _capex) if (_ocf is not None and _capex is not None) else None
                    row = {
                        "year": _em_extract_year(item.get("REPORT_DATE") or item.get("NOTICE_DATE", "")),
                        "quarter": "",
                        "revenue": _revenue,
                        "gross_profit": _gross,
                        "net_income": _em_to_float(item.get("PARENT_NETPROFIT")),
                        "operating_cash_flow": _ocf,
                        "total_assets": _em_to_float(item.get("TOTAL_ASSETS")),
                        "total_liabilities": _em_to_float(item.get("TOTAL_LIABILITIES")),
                        "operating_expenses": _em_to_float(item.get("TOTAL_OPERATE_EXPENSE")),
                        "ebitda": _em_to_float(item.get("EBITDA")),
                        "currency": "CNY",
                    }
                    if _fcf is not None:
                        row["free_cash_flow"] = _fcf
                    result_data.append(row)

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
                        pb_ratio=d.get("f173"),
                        description="",
                    ),
                    source="eastmoney",
                )

        except Exception as e:
            logger.warning(f"eastmoney get_profile failed for {identifier}: {e}")
            return DataResult(success=False, error=str(e))

    async def get_peers(self, identifier: str) -> DataResult:
        """Find peer companies via eastmoney industry classification."""
        secucode = self._resolve_secucode(identifier)
        if not secucode:
            return DataResult(success=False, error=f"Cannot resolve code for: {identifier}")

        # First get the company's industry, then find same-industry companies
        profile = await self.get_profile(identifier)
        industry = ""
        if profile.has_data():
            industry = _to_dict_safe(profile.data).get("industry", "")

        if not industry:
            return DataResult(success=False, error="eastmoney: cannot determine industry for peer lookup")

        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Referer": "https://quote.eastmoney.com/",
            }
            async with httpx.AsyncClient(timeout=10, follow_redirects=True, headers=headers) as client:
                params = {
                    "reportName": "RPT_LICO_FN_CPD",
                    "columns": "SECURITY_CODE,SECURITY_NAME_ABBR,TOTAL_OPERATE_INCOME,PARENT_NETPROFIT",
                    "filter": f'(SECURITY_NAME_ABBR like "%{industry}%")',
                    "pageNumber": "1",
                    "pageSize": "10",
                    "sortTypes": "-1",
                    "sortColumns": "TOTAL_OPERATE_INCOME",
                    "source": "WEB",
                    "client": "WEB",
                }
                resp = await client.get(EM_FINANCIAL_API, params=params)
                resp.raise_for_status()
                data = resp.json()
                items = data.get("result", {}).get("data", []) if data.get("result") else []

                code = secucode.split(".")[0] if "." in secucode else secucode
                peers = []
                for item in items[:8]:
                    item_code = item.get("SECURITY_CODE", "")
                    if item_code == code:
                        continue
                    rev = _em_to_float(item.get("TOTAL_OPERATE_INCOME"))
                    ni = _em_to_float(item.get("PARENT_NETPROFIT"))
                    peers.append({
                        "ticker": item_code,
                        "name": item.get("SECURITY_NAME_ABBR", ""),
                        "revenue": rev,
                        "net_income": ni,
                    })

                if peers:
                    return DataResult(
                        success=True,
                        data={"peer_tickers": [p["ticker"] for p in peers], "peers_detail": peers},
                        source="eastmoney",
                    )
        except Exception as e:
            logger.warning(f"eastmoney get_peers failed: {e}")

        return DataResult(success=False, error="eastmoney: peer lookup failed")

    async def get_market_data(
        self, industry: str, region: str = "global", metric: str = ""
    ) -> DataResult:
        """Get industry sector data from eastmoney."""
        from datetime import datetime, timezone

        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Referer": "https://quote.eastmoney.com/",
            }

            # Try eastmoney industry board API
            board_url = "https://push2.eastmoney.com/api/qt/clist/get"
            params = {
                "pn": "1",
                "pz": "20",
                "po": "1",
                "np": "1",
                "fltt": "2",
                "invt": "2",
                "fid": "f3",
                "fs": "m:90 t:2",
                "fields": "f12,f14,f2,f3,f62,f184,f66,f69,f72,f75,f78,f81,f84,f87",
                "key": industry,
            }
            async with httpx.AsyncClient(timeout=10, follow_redirects=True, headers=headers) as client:
                resp = await client.get(board_url, params=params)
                resp.raise_for_status()
                data = resp.json()

            diff = data.get("data", {}).get("diff", []) if data.get("data") else []
            if diff:
                # Find matching industry
                for item in diff:
                    name = item.get("f14", "")
                    if industry in name or name in industry:
                        result_data = {
                            "industry": name,
                            "region": "中国",
                            "classification": "东方财富行业板块",
                            "board_code": item.get("f12", ""),
                            "market_summary": {
                                "change_pct": item.get("f3"),
                                "main_net_inflow": item.get("f62"),
                                "pe_ratio": item.get("f84"),
                                "pb_ratio": item.get("f87"),
                            },
                            "data_source": "eastmoney",
                            "fetched_at": datetime.now(timezone.utc).isoformat(),
                        }
                        return DataResult(success=True, data=result_data, source="eastmoney")

                # Return first result if no exact match
                if diff:
                    item = diff[0]
                    result_data = {
                        "industry": item.get("f14", industry),
                        "region": "中国",
                        "classification": "东方财富行业板块",
                        "board_code": item.get("f12", ""),
                        "market_summary": {
                            "change_pct": item.get("f3"),
                            "main_net_inflow": item.get("f62"),
                        },
                        "data_source": "eastmoney",
                        "fetched_at": datetime.now(timezone.utc).isoformat(),
                    }
                    return DataResult(success=True, data=result_data, source="eastmoney")

        except Exception as e:
            logger.warning(f"eastmoney get_market_data failed: {e}")

        return DataResult(success=False, error="eastmoney: market data not available")

    async def get_industry_data(
        self, industry: str, region: str = "global", metric: str = ""
    ) -> DataResult:
        """Get industry classification and constituent data from eastmoney."""
        from datetime import datetime, timezone

        # Reuse market_data as base, then add constituents
        base_result = await self.get_market_data(industry, region, metric)
        if not base_result.has_data():
            return base_result

        result_data = base_result.data if isinstance(base_result.data, dict) else {}
        result_data["classification_system"] = result_data.get("classification", "东方财富行业板块")

        # Try to get constituent stocks
        board_code = result_data.get("board_code", "")
        board_name = result_data.get("industry", industry)

        if board_code or board_name:
            try:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                    "Referer": "https://quote.eastmoney.com/",
                }
                cons_url = "https://push2.eastmoney.com/api/qt/clist/get"
                params = {
                    "pn": "1",
                    "pz": "20",
                    "po": "1",
                    "np": "1",
                    "fltt": "2",
                    "invt": "2",
                    "fid": "f20",
                    "fs": f"b:{board_code} f:!50",
                    "fields": "f12,f14,f2,f3,f9,f20,f23",
                }
                async with httpx.AsyncClient(timeout=10, follow_redirects=True, headers=headers) as client:
                    resp = await client.get(cons_url, params=params)
                    resp.raise_for_status()
                    data = resp.json()

                diff = data.get("data", {}).get("diff", []) if data.get("data") else []
                stocks = []
                for item in diff[:20]:
                    stocks.append({
                        "code": item.get("f12", ""),
                        "name": item.get("f14", ""),
                        "pe_ratio": item.get("f9"),
                        "market_cap": item.get("f20"),
                        "pb_ratio": item.get("f23"),
                    })
                result_data["constituent_stocks"] = stocks
            except Exception as e:
                logger.warning(f"eastmoney constituent lookup failed: {e}")

        result_data["data_source"] = "eastmoney"
        result_data["fetched_at"] = datetime.now(timezone.utc).isoformat()
        return DataResult(success=True, data=result_data, source="eastmoney")

    async def get_stock_news(
        self, identifier: str, days: int = 7, limit: int = 10
    ) -> DataResult:
        """Get company-specific news from eastmoney."""
        from datetime import datetime, timezone

        # Use eastmoney search for company news
        result = await self.get_news(identifier, limit)
        if not result.has_data():
            return result

        # Restructure for stock_news format
        articles = result.data.get("results", []) if isinstance(result.data, dict) else []
        secucode = self._resolve_secucode(identifier)
        ticker = secucode.split(".")[0] if secucode and "." in secucode else identifier

        return DataResult(
            success=True,
            data={
                "identifier": identifier,
                "ticker": ticker,
                "articles": articles,
                "announcements": [],
                "data_source": "eastmoney",
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            },
            source="eastmoney",
        )

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
                # Eastmoney public suggest API token (same as akshare uses)
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


def _to_dict_safe(data):
    """Safely convert dataclass/dict to dict."""
    if hasattr(data, "__dataclass_fields__"):
        from dataclasses import asdict
        return asdict(data)
    if isinstance(data, dict):
        return data
    return {}


def _em_extract_year(date_str: str) -> int:
    try:
        return int(str(date_str)[:4])
    except (ValueError, IndexError):
        return 0
