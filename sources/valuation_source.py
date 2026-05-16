"""Valuation parameter aggregation — assembles DCF/Comps/DDM inputs from other sources."""

import logging
from typing import Any

from .base import BaseSource, DataResult, ValuationData

logger = logging.getLogger(__name__)

# Default equity risk premiums by region
_EQUITY_RISK_PREMIUMS = {
    "US": 5.5, "CN": 7.0, "EU": 6.0, "JP": 6.5,
    "UK": 6.0, "DE": 6.0, "FR": 6.0, "IN": 8.0,
    "global": 6.0,
}

# Map country codes to risk-free-rate indicator / region
_RFR_INDICATORS = {
    "US": "treasury_10y", "JP": "interest_rate", "UK": "interest_rate",
    "EU": "interest_rate", "DE": "interest_rate", "FR": "interest_rate",
    "CN": "interest_rate", "IN": "interest_rate",
}


def _cagr(start: float, end: float, years: int) -> float | None:
    if start and end and years > 0 and start > 0:
        return (end / start) ** (1.0 / years) - 1.0
    return None


class ValuationSource(BaseSource):
    """Aggregates valuation parameters by calling other sources' methods.

    Not a standalone data source — receives source instances via __init__
    and delegates profile/financials/macro/peers calls to them.
    """

    name = "valuation"
    use_cache = True

    def __init__(self, financials_sources: list, macro_source, peers_sources: list):
        self._fin_sources = financials_sources
        self._macro_source = macro_source
        self._peers_sources = peers_sources

    async def get_valuation(self, identifier: str, method: str = "dcf") -> DataResult:
        profile = None
        financials = None
        peers_data = None

        # 1. Get profile (beta, market_cap, etc.)
        for src in self._fin_sources:
            if src is None:
                continue
            try:
                r = await src.get_profile(identifier)
                if r.has_data():
                    profile = r.data if isinstance(r.data, dict) else {}
                    break
            except Exception:
                continue

        # 2. Get financials (5 years for CAGR)
        for src in self._fin_sources:
            if src is None:
                continue
            try:
                r = await src.get_financials(identifier, period="annual", years=5)
                if r.has_data():
                    financials = r.data if isinstance(r.data, dict) else {}
                    break
            except Exception:
                continue

        # 3. Get peers for Comps
        for src in self._peers_sources:
            if src is None:
                continue
            try:
                r = await src.get_peers(identifier)
                if r.has_data():
                    peers_data = r.data if isinstance(r.data, dict) else {}
                    break
            except Exception:
                continue

        if not profile and not financials:
            return DataResult(success=False, error=f"No data available for {identifier}")

        val = ValuationData(identifier=identifier)

        # --- Profile data ---
        if profile:
            val.beta = profile.get("beta")
            val.market_cap = profile.get("market_cap")
            val.pe_ratio = profile.get("pe_ratio")
            val.ps_ratio = profile.get("ps_ratio")
            # Try to infer region from exchange
            exchange = profile.get("exchange", "").upper()
            if "SH" in exchange or "SZ" in exchange or "HK" in exchange:
                val.region = "CN"
            elif "L" in exchange:
                val.region = "UK"
            elif "T" in exchange:
                val.region = "JP"

        # --- Financial data ---
        if financials and isinstance(financials, dict):
            periods = financials.get("data", [])
            val.currency = financials.get("currency", "USD")
            val.shares_outstanding = None

            if periods:
                latest = periods[0]
                val.latest_fcf = latest.get("free_cash_flow")
                rev = latest.get("revenue")
                fcf = latest.get("free_cash_flow")
                if rev and fcf:
                    val.fcf_margin = fcf / rev * 100

                # CAGRs
                if len(periods) >= 4:
                    newest_rev = periods[0].get("revenue")
                    oldest_3y = periods[min(3, len(periods) - 1)].get("revenue")
                    val.revenue_cagr_3y = _cagr(oldest_3y, newest_rev, 3)

                    newest_ni = periods[0].get("net_income")
                    oldest_ni_3y = periods[min(3, len(periods) - 1)].get("net_income")
                    val.earnings_cagr_3y = _cagr(oldest_ni_3y, newest_ni, 3)

                if len(periods) >= 6:
                    oldest_5y = periods[min(5, len(periods) - 1)].get("revenue")
                    val.revenue_cagr_5y = _cagr(oldest_5y, periods[0].get("revenue"), 5)

                # Dividend inputs
                ni_latest = latest.get("net_income")
                div_latest = latest.get("dividends")
                if ni_latest and div_latest and ni_latest != 0:
                    val.payout_ratio = abs(div_latest) / abs(ni_latest) * 100

                val.shares_outstanding = latest.get("shares_outstanding")
                val.eps = latest.get("eps")
                val.ebitda = latest.get("ebitda")

        # --- Dividend yield ---
        if val.market_cap and financials and isinstance(financials, dict):
            periods = financials.get("data", [])
            if periods:
                div = periods[0].get("dividends")
                if div and val.market_cap != 0:
                    val.dividend_yield = abs(div) / val.market_cap * 100

        # --- WACC estimation ---
        erp = _EQUITY_RISK_PREMIUMS.get(val.region, 6.0)
        val.equity_risk_premium = erp

        if val.beta and val.market_cap:
            # Use 4% as default risk-free rate if macro source unavailable
            val.risk_free_rate = 4.0
            cost_of_equity = (val.risk_free_rate / 100) + val.beta * (erp / 100)
            # Simplified: assume 100% equity (no debt component)
            val.wacc = cost_of_equity * 100

        # --- Peer multiples (if Comps method) ---
        if method in ("comps", "all") and peers_data:
            peer_tickers = peers_data.get("peer_tickers", [])
            # Collect PE/PS from peers — best-effort
            # (Full implementation would fetch each peer's profile; skip for now
            #  and let the skill layer compute from competitor_compare data)
            val.peer_pe_median = None
            val.peer_ps_median = None
            val.peer_ev_ebitda_median = None

        # --- Current price ---
        if val.market_cap and val.shares_outstanding and val.shares_outstanding != 0:
            val.current_price = val.market_cap / val.shares_outstanding

        return DataResult(success=True, data=val, source="valuation")
