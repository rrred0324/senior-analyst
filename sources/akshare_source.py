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
    use_cache = True

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
                _ni = _to_float(row.get("净利润"))
                _ocf = _to_float(row.get("经营活动产生的现金流量净额"))
                _ta = _to_float(row.get("总资产"))
                _tl = _to_float(row.get("总负债"))
                row_data = {
                    "year": year,
                    "quarter": "",
                    "revenue": _rev,
                    "gross_profit": _gross,
                    "net_income": _ni,
                    "operating_cash_flow": _ocf,
                    "total_assets": _ta,
                    "total_liabilities": _tl,
                    "currency": "CNY",
                }
                _eps = _to_float(row.get("基本每股收益"))
                if _eps is not None:
                    row_data["eps"] = _eps
                data.append(row_data)

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

        # Try industry board data first (申万行业)
        try:
            df = self.ak.stock_board_industry_name_em()
            if df is not None and not df.empty:
                # Find matching industry
                match = df[df["板块名称"].str.contains(industry, na=False)]
                if match.empty:
                    match = df[df["板块名称"].str.contains(industry[:2], na=False)]
                if not match.empty:
                    row = match.iloc[0]
                    board_code = row.get("板块代码", "")
                    board_name = row.get("板块名称", industry)

                    # Get board constituents and performance
                    result_data = {
                        "industry": board_name,
                        "region": "中国",
                        "classification": "东方财富行业板块",
                        "board_code": board_code,
                        "change_pct": _to_float(row.get("涨跌幅")),
                    }

                    # Try to get more details
                    try:
                        cons_df = self.ak.stock_board_industry_cons_em(symbol=board_name)
                        if cons_df is not None and not cons_df.empty:
                            result_data["constituent_count"] = len(cons_df)
                            top_stocks = []
                            for _, s in cons_df.head(10).iterrows():
                                top_stocks.append({
                                    "code": s.get("代码", ""),
                                    "name": s.get("名称", ""),
                                    "change_pct": _to_float(s.get("涨跌幅")),
                                })
                            result_data["top_stocks"] = top_stocks
                    except Exception:
                        pass

                    return DataResult(success=True, data=result_data, source="akshare")
        except Exception as e:
            logger.warning(f"akshare industry board failed: {e}")

        # Fallback: macro data
        try:
            df = self.ak.macro_china_gdp()
            if df is not None and not df.empty:
                latest = df.tail(3)
                return DataResult(
                    success=True,
                    data={
                        "industry": industry,
                        "region": region,
                        "classification": "宏观经济数据",
                        "macro_gdp_data": latest.to_dict(),
                        "note": "Specific industry data not found, returning macro GDP as fallback",
                    },
                    source="akshare",
                )
        except Exception as e:
            logger.warning(f"akshare macro data failed: {e}")

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

    async def get_industry_data(
        self, industry: str, region: str = "global", metric: str = ""
    ) -> DataResult:
        """Get industry classification, constituents, and valuation from akshare."""
        if self.ak is None:
            return DataResult(success=False, error="akshare not installed")

        from datetime import datetime, timezone

        try:
            # Get Shenwan industry index data
            df = self.ak.index_stock_info_shenwan()
            if df is not None and not df.empty:
                match = df[df["行业名称"].str.contains(industry, na=False)]
                if match.empty:
                    match = df[df["行业名称"].str.contains(industry[:2], na=False)]
                if not match.empty:
                    row = match.iloc[0]
                    industry_code = row.get("行业代码", "")
                    industry_name = row.get("行业名称", industry)

                    result_data = {
                        "industry": industry_name,
                        "classification_system": "申万行业分类",
                        "industry_code": industry_code,
                    }

                    # Get constituent stocks
                    try:
                        cons_df = self.ak.index_component_sw(symbol=industry_code)
                        if cons_df is not None and not cons_df.empty:
                            stocks = []
                            for _, s in cons_df.head(20).iterrows():
                                stocks.append({
                                    "code": str(s.get("股票代码", "")),
                                    "name": str(s.get("股票名称", "")),
                                })
                            result_data["constituent_stocks"] = stocks
                    except Exception:
                        pass

                    result_data["data_source"] = "akshare"
                    result_data["fetched_at"] = datetime.now(timezone.utc).isoformat()
                    return DataResult(success=True, data=result_data, source="akshare")
        except Exception as e:
            logger.warning(f"akshare get_industry_data failed: {e}")

        # Fallback: eastmoney industry board
        try:
            df = self.ak.stock_board_industry_name_em()
            if df is not None and not df.empty:
                match = df[df["板块名称"].str.contains(industry, na=False)]
                if match.empty:
                    match = df[df["板块名称"].str.contains(industry[:2], na=False)]
                if not match.empty:
                    row = match.iloc[0]
                    board_name = row.get("板块名称", industry)
                    result_data = {
                        "industry": board_name,
                        "classification_system": "东方财富行业板块",
                    }
                    try:
                        cons_df = self.ak.stock_board_industry_cons_em(symbol=board_name)
                        if cons_df is not None and not cons_df.empty:
                            stocks = []
                            for _, s in cons_df.head(20).iterrows():
                                stocks.append({
                                    "code": str(s.get("代码", "")),
                                    "name": str(s.get("名称", "")),
                                })
                            result_data["constituent_stocks"] = stocks
                    except Exception:
                        pass

                    result_data["data_source"] = "akshare"
                    result_data["fetched_at"] = datetime.now(timezone.utc).isoformat()
                    return DataResult(success=True, data=result_data, source="akshare")
        except Exception as e:
            logger.warning(f"akshare eastmoney board fallback failed: {e}")

        return DataResult(success=False, error=f"akshare: no industry data for {industry}")

    async def get_stock_news(
        self, identifier: str, days: int = 7, limit: int = 10
    ) -> DataResult:
        """Get company-specific news and announcements from akshare."""
        if self.ak is None:
            return DataResult(success=False, error="akshare not installed")

        from datetime import datetime, timezone

        ticker = self._resolve_cn_ticker(identifier)

        articles = []
        announcements = []

        # Get stock news from eastmoney
        try:
            df = self.ak.stock_news_em(symbol=ticker or identifier)
            if df is not None and not df.empty:
                for _, row in df.head(limit).iterrows():
                    articles.append({
                        "title": row.get("新闻标题", ""),
                        "source": row.get("新闻来源", ""),
                        "date": str(row.get("发布时间", "")),
                        "snippet": str(row.get("新闻内容", ""))[:200],
                    })
        except Exception as e:
            logger.warning(f"akshare stock_news_em failed: {e}")

        # Get company announcements
        if ticker:
            try:
                df = self.ak.stock_notice_report(symbol=ticker)
                if df is not None and not df.empty:
                    for _, row in df.head(5).iterrows():
                        announcements.append({
                            "title": row.get("标题", ""),
                            "type": row.get("类型", ""),
                            "date": str(row.get("公告日期", "")),
                        })
            except Exception as e:
                logger.warning(f"akshare stock_notice_report failed: {e}")

        if not articles and not announcements:
            return DataResult(success=False, error="akshare: no stock news or announcements")

        return DataResult(
            success=True,
            data={
                "identifier": identifier,
                "ticker": ticker or "",
                "articles": articles,
                "announcements": announcements,
                "data_source": "akshare",
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            },
            source="akshare",
        )

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
