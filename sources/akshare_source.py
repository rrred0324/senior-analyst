"""akshare data source — focused on Chinese markets (A-shares, HK, macro)."""

import logging
from typing import Any

from .base import BaseSource, DataResult, FinancialData, CompanyProfileData

logger = logging.getLogger(__name__)


def _try_import_akshare():
    try:
        import akshare as ak
        return ak
    except ImportError:
        return None


class AkshareSource(BaseSource):
    name = "akshare"

    def __init__(self):
        self._ak = None

    @property
    def ak(self):
        if self._ak is None:
            self._ak = _try_import_akshare()
        return self._ak

    async def get_financials(
        self, identifier: str, period: str = "annual", years: int = 3
    ) -> DataResult:
        if self.ak is None:
            return DataResult(success=False, error="akshare not installed")

        # Try to resolve as A-share or HK stock
        ticker = self._resolve_cn_ticker(identifier)
        if not ticker:
            return DataResult(success=False, error=f"Cannot resolve CN ticker for: {identifier}")

        try:
            if ticker.endswith(".HK"):
                return await self._get_hk_financials(ticker, period, years)
            else:
                return await self._get_cn_financials(ticker, period, years)
        except Exception as e:
            logger.warning(f"akshare get_financials failed for {identifier}: {e}")
            return DataResult(success=False, error=str(e))

    async def _get_cn_financials(
        self, ticker: str, period: str, years: int
    ) -> DataResult:
        try:
            # Get income statement
            df = self.ak.stock_financial_report_sina(stock=f"sh{ticker}" if ticker.startswith("6") else f"sz{ticker}", symbol="利润表")
            if df is None or df.empty:
                return DataResult(success=False, error="No data from akshare")

            data = []
            for _, row in df.head(years).iterrows():
                year = _extract_year(row)
                if not year:
                    continue
                _rev = _to_float(row.get("营业收入"))
                _cost = _to_float(row.get("营业成本"))
                _gross = (_rev - _cost) if (_rev is not None and _cost is not None) else None
                data.append({
                    "year": year,
                    "quarter": "",
                    "revenue": _rev,
                    "gross_profit": _gross,
                    "net_income": _to_float(row.get("净利润")),
                    "operating_cash_flow": None,
                    "total_assets": None,
                    "total_liabilities": None,
                    "currency": "CNY",
                })

            if not data:
                return DataResult(success=False, error="No financial rows parsed")

            return DataResult(
                success=True,
                data={"company": ticker, "ticker": ticker, "currency": "CNY", "data": data},
                source="akshare",
            )
        except Exception as e:
            return DataResult(success=False, error=str(e))

    async def _get_hk_financials(
        self, ticker: str, period: str, years: int
    ) -> DataResult:
        # akshare has limited HK stock financial data
        # Return a basic result suggesting yfinance as primary for HK
        return DataResult(success=False, error="HK stock financials: yfinance recommended as primary")

    async def get_profile(self, identifier: str) -> DataResult:
        if self.ak is None:
            return DataResult(success=False, error="akshare not installed")

        ticker = self._resolve_cn_ticker(identifier)
        if not ticker:
            return DataResult(success=False, error=f"Cannot resolve CN ticker for: {identifier}")

        try:
            df = self.ak.stock_individual_info_em(symbol=ticker)
            if df is None or df.empty:
                return DataResult(success=False, error="No profile data")

            info = {}
            for _, row in df.iterrows():
                info[row.iloc[0]] = row.iloc[1]

            return DataResult(
                success=True,
                data=CompanyProfileData(
                    name=info.get("股票简称", identifier),
                    ticker=ticker,
                    exchange=info.get("上市板块", "CN"),
                    industry=info.get("行业", ""),
                    sector="",
                    market_cap=None,
                    pe_ratio=_to_float(info.get("市盈率(动态)")),
                    ps_ratio=None,
                    pb_ratio=_to_float(info.get("市净率")),
                    description=info.get("公司介绍", ""),
                ),
                source="akshare",
            )
        except Exception as e:
            logger.warning(f"akshare get_profile failed for {identifier}: {e}")
            return DataResult(success=False, error=str(e))

    async def get_peers(self, identifier: str) -> DataResult:
        # akshare doesn't have a direct peer lookup
        return DataResult(success=False, error="akshare: peer lookup not supported, use yfinance")

    async def get_market_data(
        self, industry: str, region: str = "global", metric: str = ""
    ) -> DataResult:
        if self.ak is None:
            return DataResult(success=False, error="akshare not installed")

        try:
            # Try to get macro industry data
            df = self.ak.macro_china_gdp()
            if df is not None and not df.empty:
                return DataResult(
                    success=True,
                    data={"industry": industry, "region": region, "macro_gdp_data": df.tail(3).to_dict()},
                    source="akshare",
                )
        except Exception as e:
            logger.warning(f"akshare get_market_data failed: {e}")

        return DataResult(success=False, error=f"akshare: no market data for {industry}")

    async def get_news(self, query: str, limit: int = 5) -> DataResult:
        if self.ak is None:
            return DataResult(success=False, error="akshare not installed")

        try:
            df = self.ak.stock_news_em(symbol=query)
            if df is not None and not df.empty:
                results = []
                for _, row in df.head(limit).iterrows():
                    results.append({
                        "title": row.get("新闻标题", ""),
                        "source": row.get("新闻来源", ""),
                        "date": str(row.get("发布时间", "")),
                        "snippet": row.get("新闻内容", "")[:200],
                    })
                return DataResult(success=True, data={"query": query, "results": results}, source="akshare")
        except Exception as e:
            logger.warning(f"akshare get_news failed: {e}")

        return DataResult(success=False, error="akshare: no news data")

    def _resolve_cn_ticker(self, identifier: str) -> str | None:
        """Try to resolve identifier to a CN stock ticker."""
        # If already looks like a CN ticker
        if identifier.isdigit() and len(identifier) == 6:
            return identifier

        # Check ticker map for CN entries
        from .yfinance_source import _load_ticker_map
        ticker_map = _load_ticker_map()
        if identifier in ticker_map:
            t = ticker_map[identifier]
            if t.startswith("PRIVATE:"):
                return None
            # CN market tickers like 600519.SS, 000001.SZ
            if t.endswith(".SS") or t.endswith(".SZ"):
                return t.split(".")[0]
            if t.endswith(".HK"):
                # HK-listed company may also have A-share listing
                # Try to find A-share code via eastmoney search
                return self._search_cn_ticker(identifier)

        # Try to search for A-share code
        return self._search_cn_ticker(identifier)

    def _search_cn_ticker(self, name: str) -> str | None:
        """Search for A-share stock code via eastmoney suggest API."""
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
            r = _httpx.get(url, params=params, timeout=5, follow_redirects=True)
            data = r.json()
            items = data.get("QuotationCodeTable", {}).get("Data", [])
            for item in items:
                code = item.get("Code", "")
                mkt = item.get("MktNum", "")
                if mkt in ("0", "1") and len(code) == 6:
                    return code
            return None
        except Exception:
            return None


def _to_float(val: Any) -> float | None:
    if val is None:
        return None
    try:
        result = float(val)
        return result if str(result) != "nan" else None
    except (ValueError, TypeError):
        return None


def _extract_year(row) -> int | None:
    for key in ["报告日", "日期", "截止日期"]:
        if key in row.index:
            val = str(row[key])
            try:
                return int(val[:4])
            except (ValueError, IndexError):
                pass
    return None
