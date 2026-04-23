"""yfinance data source."""

import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Any

import yfinance as yf

from .base import BaseSource, DataResult, FinancialData, CompanyProfileData

logger = logging.getLogger(__name__)

# Rate limiting: minimum seconds between yfinance requests
_LAST_REQUEST_TIME = 0.0
_MIN_INTERVAL = 3.0


async def _rate_limited():
    """Enforce minimum interval between yfinance API calls."""
    global _LAST_REQUEST_TIME
    now = time.time()
    elapsed = now - _LAST_REQUEST_TIME
    if elapsed < _MIN_INTERVAL:
        await asyncio.sleep(_MIN_INTERVAL - elapsed)
    _LAST_REQUEST_TIME = time.time()

TICKER_MAP_PATH = Path(__file__).parent / "ticker_map.json"


def _load_ticker_map() -> dict[str, str]:
    try:
        with open(TICKER_MAP_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def resolve_ticker(identifier: str) -> str | None:
    """Resolve a company name or ticker to a yfinance-compatible ticker."""
    ticker_map = _load_ticker_map()

    # Direct map lookup
    if identifier in ticker_map:
        t = ticker_map[identifier]
        if t.startswith("PRIVATE:"):
            return None
        return t

    # Already looks like a ticker (has a dot or is all uppercase with length <= 10)
    if "." in identifier or (identifier.isupper() and len(identifier) <= 10):
        return identifier

    # Try yfinance search
    try:
        result = yf.Search(identifier)
        quotes = getattr(result, "quotes", []) or []
        if quotes:
            return quotes[0].get("symbol", identifier)
    except Exception:
        pass

    return None


class YFinanceSource(BaseSource):
    name = "yfinance"

    async def get_financials(
        self, identifier: str, period: str = "annual", years: int = 3
    ) -> DataResult:
        ticker_symbol = resolve_ticker(identifier)
        if not ticker_symbol:
            return DataResult(success=False, error=f"Cannot resolve ticker for: {identifier}")

        for attempt in range(2):
            try:
                await _rate_limited()
                ticker = yf.Ticker(ticker_symbol)

                income_stmt = ticker.income_stmt
                if income_stmt is None or income_stmt.empty:
                    income_stmt = ticker.quarterly_income_stmt if period != "annual" else None

                balance_sheet = ticker.balance_sheet
                cashflow = ticker.cashflow

                info = ticker.info or {}
                currency = info.get("currency", "USD")
                company_name = info.get("longName", info.get("shortName", identifier))

                data = []
                if income_stmt is not None and not income_stmt.empty:
                    cols = list(income_stmt.columns)
                    for col in cols[:years]:
                        year = col.year if hasattr(col, "year") else int(str(col)[:4])
                        quarter = ""
                        if period == "quarterly" and hasattr(col, "month"):
                            quarter = f"Q{(col.month - 1) // 3 + 1}"

                        revenue = _safe_float(income_stmt, "Total Revenue", col)
                        gross_profit = _safe_float(income_stmt, "Gross Profit", col)
                        net_income = _safe_float(income_stmt, "Net Income", col)

                        ocf = None
                        if cashflow is not None and not cashflow.empty and col in cashflow.columns:
                            ocf = _safe_float(cashflow, "Operating Cash Flow", col)

                        total_assets = None
                        total_liabilities = None
                        if balance_sheet is not None and not balance_sheet.empty and col in balance_sheet.columns:
                            total_assets = _safe_float(balance_sheet, "Total Assets", col)
                            total_liabilities = _safe_float(balance_sheet, "Total Liabilities Net Minority Interest", col)
                            if total_liabilities is None:
                                total_liabilities = _safe_float(balance_sheet, "Total Liabilities", col)

                        data.append(FinancialData(
                            year=year, quarter=quarter, revenue=revenue,
                            gross_profit=gross_profit, net_income=net_income,
                            operating_cash_flow=ocf, total_assets=total_assets,
                            total_liabilities=total_liabilities, currency=currency,
                        ))

                if not data:
                    return DataResult(success=False, error="No financial data returned")

                return DataResult(
                    success=True,
                    data={
                        "company": company_name, "ticker": ticker_symbol,
                        "currency": currency, "data": [_fd_to_dict(d) for d in data],
                    },
                    source="yfinance",
                )

            except Exception as e:
                if "Rate limited" in str(e) and attempt < 1:
                    logger.warning(f"yfinance rate limited, retrying after delay for {identifier}")
                    await asyncio.sleep(5)
                    continue
                logger.warning(f"yfinance get_financials failed for {identifier}: {e}")
                return DataResult(success=False, error=str(e))

    async def get_profile(self, identifier: str) -> DataResult:
        ticker_symbol = resolve_ticker(identifier)
        if not ticker_symbol:
            return DataResult(success=False, error=f"Cannot resolve ticker for: {identifier}")

        try:
            await _rate_limited()
            ticker = yf.Ticker(ticker_symbol)
            info = ticker.info or {}

            return DataResult(
                success=True,
                data=CompanyProfileData(
                    name=info.get("longName", info.get("shortName", identifier)),
                    ticker=ticker_symbol,
                    exchange=info.get("exchange", ""),
                    industry=info.get("industry", ""),
                    sector=info.get("sector", ""),
                    market_cap=info.get("marketCap"),
                    pe_ratio=info.get("trailingPE"),
                    ps_ratio=info.get("priceToSalesTrailing12Months"),
                    pb_ratio=info.get("priceToBook"),
                    description=info.get("longBusinessSummary", ""),
                ),
                source="yfinance",
            )
        except Exception as e:
            logger.warning(f"yfinance get_profile failed for {identifier}: {e}")
            return DataResult(success=False, error=str(e))

    async def get_peers(self, identifier: str) -> DataResult:
        ticker_symbol = resolve_ticker(identifier)
        if not ticker_symbol:
            return DataResult(success=False, error=f"Cannot resolve ticker for: {identifier}")

        try:
            await _rate_limited()
            ticker = yf.Ticker(ticker_symbol)
            # yfinance doesn't have a direct peers API, use sector/industry matching
            info = ticker.info or {}
            industry = info.get("industry", "")
            sector = info.get("sector", "")

            # Try to get peers from recommendations
            recommendations = getattr(ticker, "recommendations", None)
            peer_tickers = []
            if recommendations is not None:
                try:
                    if hasattr(recommendations, "index"):
                        peer_tickers = list(recommendations.index)[:5]
                except Exception:
                    pass

            # Fallback: use industry from info for downstream lookup
            return DataResult(
                success=True,
                data={
                    "ticker": ticker_symbol,
                    "industry": industry,
                    "sector": sector,
                    "peer_tickers": peer_tickers,
                },
                source="yfinance",
            )
        except Exception as e:
            logger.warning(f"yfinance get_peers failed for {identifier}: {e}")
            return DataResult(success=False, error=str(e))


def _safe_float(df: Any, label: str, col: Any) -> float | None:
    """Safely extract a float value from a yfinance DataFrame."""
    try:
        if label in df.index and col in df.columns:
            val = df.loc[label, col]
            if val is not None and str(val) != "nan":
                return float(val)
    except Exception:
        pass
    return None


def _fd_to_dict(fd: FinancialData) -> dict:
    return {
        "year": fd.year,
        "quarter": fd.quarter,
        "revenue": fd.revenue,
        "gross_profit": fd.gross_profit,
        "net_income": fd.net_income,
        "operating_cash_flow": fd.operating_cash_flow,
        "total_assets": fd.total_assets,
        "total_liabilities": fd.total_liabilities,
        "currency": fd.currency,
    }
