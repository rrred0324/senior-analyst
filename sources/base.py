"""Base class for data sources."""

import functools
import logging
from dataclasses import dataclass, field
from typing import Any

from .config import cache_key, get_cache

logger = logging.getLogger(__name__)


@dataclass
class DataResult:
    success: bool = False
    data: Any = None
    source: str = ""
    error: str = ""

    def has_data(self) -> bool:
        if not self.success:
            return False
        if self.data is None:
            return False
        if isinstance(self.data, list) and len(self.data) == 0:
            return False
        if isinstance(self.data, dict) and len(self.data) == 0:
            return False
        return True


@dataclass
class FinancialData:
    year: int = 0
    quarter: str = ""
    revenue: float | None = None
    gross_profit: float | None = None
    net_income: float | None = None
    operating_cash_flow: float | None = None
    total_assets: float | None = None
    total_liabilities: float | None = None
    shares_outstanding: float | None = None
    eps: float | None = None
    operating_expenses: float | None = None
    rd_expenses: float | None = None
    free_cash_flow: float | None = None
    dividends: float | None = None
    ebitda: float | None = None
    currency: str = "USD"


@dataclass
class CompanyProfileData:
    name: str = ""
    ticker: str = ""
    exchange: str = ""
    industry: str = ""
    sector: str = ""
    market_cap: float | None = None
    pe_ratio: float | None = None
    ps_ratio: float | None = None
    pb_ratio: float | None = None
    description: str = ""


@dataclass
class MacroDataPoint:
    date: str = ""            # ISO 8601 (YYYY-MM-DD or YYYY-Q1)
    value: float | None = None
    unit: str = ""            # "%", "USD billion", "index", etc.


@dataclass
class MacroSeriesData:
    indicator: str = ""       # canonical key, e.g. "gdp", "cpi"
    region: str = ""          # "US", "CN", "EU", ...
    period: str = "monthly"   # "monthly", "quarterly", "annual"
    unit: str = ""
    series_id: str = ""       # provider's native series id (e.g. FRED "GDP")
    points: list = field(default_factory=list)   # list[MacroDataPoint]
    notes: str = ""


@dataclass
class CryptoAssetData:
    symbol: str = ""          # "BTC"
    name: str = ""            # "Bitcoin"
    coingecko_id: str = ""    # "bitcoin"
    price_usd: float | None = None
    market_cap_usd: float | None = None
    volume_24h_usd: float | None = None
    price_change_24h_pct: float | None = None
    circulating_supply: float | None = None
    max_supply: float | None = None
    rank: int | None = None


@dataclass
class ValuationData:
    """Aggregated valuation parameters for DCF/Comps/DDM analysis."""
    identifier: str = ""
    # WACC components
    risk_free_rate: float | None = None       # 10Y government bond yield (%)
    beta: float | None = None                 # stock beta
    equity_risk_premium: float | None = None  # by region (%)
    wacc: float | None = None                 # computed WACC (%)
    # Growth rates
    revenue_cagr_3y: float | None = None      # 3-year revenue CAGR (%)
    revenue_cagr_5y: float | None = None      # 5-year revenue CAGR (%)
    earnings_cagr_3y: float | None = None     # 3-year earnings CAGR (%)
    # FCF / DCF inputs
    latest_fcf: float | None = None
    fcf_margin: float | None = None           # FCF / revenue (%)
    shares_outstanding: float | None = None
    # Dividend inputs
    dividend_yield: float | None = None       # trailing dividend yield (%)
    payout_ratio: float | None = None         # dividends / net income (%)
    dividend_cagr_5y: float | None = None     # 5-year dividend CAGR (%)
    # Market data
    market_cap: float | None = None
    current_price: float | None = None
    # Peer multiples (median of peers)
    peer_pe_median: float | None = None
    peer_ps_median: float | None = None
    peer_ev_ebitda_median: float | None = None
    # Metadata
    currency: str = "USD"
    region: str = "US"


@dataclass
class ConfidenceScore:
    """Confidence score attached to every MCP tool response."""
    score: float = 0.0            # 0.0-1.0 composite confidence
    source_count: int = 0         # number of sources that returned data
    source_agreement: float = 0.0  # 0-1 agreement across sources (1.0 if single source)
    data_freshness: str = "unknown"  # "real-time" / "cached" / "stale"
    anomalies: list = field(default_factory=list)  # list of anomaly descriptions
    notes: str = ""


@dataclass
class AnomalyFlag:
    """A single detected anomaly in financial data."""
    field: str = ""          # e.g. "revenue", "gross_margin"
    period: str = ""         # e.g. "2024", "2024-Q3"
    severity: str = "warning"  # "info" / "warning" / "critical"
    rule: str = ""           # e.g. "qoq_spike>50%"
    detail: str = ""         # human-readable description
    value: float | None = None
    threshold: float | None = None


@dataclass
class CrossValidationResult:
    """Result of cross-validating data across multiple sources."""
    values: dict = field(default_factory=dict)
    # {field_name: [(source_name, value), ...]}
    discrepancies: list = field(default_factory=list)
    # [{field, sources, deviation_pct, severity}]
    reconciled: dict = field(default_factory=dict)
    # {field_name: median/reconciled value}
    anomaly_flags: list = field(default_factory=list)
    # list[AnomalyFlag]
    confidence: ConfidenceScore = field(default_factory=ConfidenceScore)


@dataclass
class ReconciliationCheck:
    """Single three-statement reconciliation check result."""
    name: str = ""           # e.g. "equity_check", "cash_flow_check"
    expected: float | None = None
    actual: float | None = None
    deviation_pct: float | None = None
    passed: bool = True
    detail: str = ""


def _make_cached_method(original, method_name: str):
    """Wrap an async source method with TTLCache lookup/store."""
    category = BaseSource._CACHE_CATEGORY.get(method_name, "financials")

    @functools.wraps(original)
    async def wrapper(self, *args, **kwargs):
        cache = get_cache(category)
        key = cache_key(category, self.name, method_name, *args, *sorted(kwargs.items()))
        if key in cache:
            logger.debug(f"Cache hit: {key}")
            return cache[key]
        result = await original(self, *args, **kwargs)
        cache[key] = result
        return result

    return wrapper


class BaseSource:
    """Base class for all data sources.

    Subclasses that want caching should set ``use_cache = True``.
    When enabled, all async ``get_*`` method calls are automatically
    wrapped with TTLCache lookup/store via config.cache_key / config.get_cache.
    """

    name: str = "base"
    use_cache: bool = False

    # Map method names to cache categories
    _CACHE_CATEGORY = {
        "get_financials": "financials",
        "get_profile": "profile",
        "get_peers": "peers",
        "get_market_data": "market",
        "get_news": "news",
        "get_stock_news": "stock_news",
        "get_macro_data": "macro",
        "get_crypto_data": "crypto",
        "get_industry_data": "industry",
        "get_valuation": "valuation",
    }

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not getattr(cls, "use_cache", False):
            return
        for method_name in BaseSource._CACHE_CATEGORY:
            original = getattr(cls, method_name, None)
            if original is None or not callable(original):
                continue
            if hasattr(original, "_cache_wrapped"):
                continue
            wrapped = _make_cached_method(original, method_name)
            wrapped._cache_wrapped = True
            setattr(cls, method_name, wrapped)

    async def get_financials(
        self, identifier: str, period: str = "annual", years: int = 3
    ) -> DataResult:
        raise NotImplementedError

    async def get_profile(self, identifier: str) -> DataResult:
        raise NotImplementedError

    async def get_peers(self, identifier: str) -> DataResult:
        raise NotImplementedError

    async def get_market_data(
        self, industry: str, region: str = "global", metric: str = ""
    ) -> DataResult:
        raise NotImplementedError

    async def get_news(self, query: str, limit: int = 5) -> DataResult:
        raise NotImplementedError

    async def get_macro_data(
        self, indicator: str, region: str = "US", period: str = "monthly", years: int = 3
    ) -> DataResult:
        raise NotImplementedError

    async def get_crypto_data(
        self, identifier: str, metrics: str = "price,marketcap,volume"
    ) -> DataResult:
        raise NotImplementedError
