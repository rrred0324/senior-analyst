from .yfinance_source import YFinanceSource
from .akshare_source import AkshareSource
from .eastmoney_source import EastmoneySource
from .config import has_fmp, has_av, has_newsapi

# Tier 1 sources (optional, require API keys)
FMPSource = None
AlphaVantageSource = None
NewsAPISource = None

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

__all__ = [
    "YFinanceSource", "AkshareSource", "EastmoneySource",
    "FMPSource", "AlphaVantageSource", "NewsAPISource",
]
