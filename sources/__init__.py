from .yfinance_source import YFinanceSource
from .akshare_source import AkshareSource
from .eastmoney_source import EastmoneySource
from .worldbank_source import WorldBankSource
from .stats_gov_cn_source import StatsGovCNSource
from .coingecko_source import CoinGeckoSource
from .config import has_fmp, has_av, has_newsapi, has_fred

# Tier 1 sources (optional, require API keys)
FMPSource = None
AlphaVantageSource = None
NewsAPISource = None
FREDSource = None

if has_fmp():
    try:
        from .fmp_source import FMPSource
    except Exception:
        pass

if has_av():
    try:
        from .alphavantage_source import AlphaVantageSource
    except Exception:
        pass

if has_newsapi():
    try:
        from .newsapi_source import NewsAPISource
    except Exception:
        pass

if has_fred():
    try:
        from .fred_source import FREDSource
    except Exception:
        pass

__all__ = [
    "YFinanceSource", "AkshareSource", "EastmoneySource",
    "WorldBankSource", "StatsGovCNSource", "CoinGeckoSource",
    "FMPSource", "AlphaVantageSource", "NewsAPISource", "FREDSource",
]
