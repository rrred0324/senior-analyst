"""Base class for data sources."""

from dataclasses import dataclass, field
from typing import Any


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


class BaseSource:
    """Base class for all data sources."""

    name: str = "base"

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
