"""Shared configuration: API key detection, source availability, caching."""

import os
import logging
from pathlib import Path
from cachetools import TTLCache

logger = logging.getLogger(__name__)

# --- API Key Detection ---

def _load_dotenv():
    """Load .env file from server.py directory if python-dotenv is available."""
    try:
        from dotenv import load_dotenv
        env_path = Path(__file__).parent.parent / ".env"
        if env_path.exists():
            load_dotenv(env_path)
    except ImportError:
        pass

_load_dotenv()

FMP_KEY = os.environ.get("SENIOR_ANALYST_FMP_KEY", "")
AV_KEY = os.environ.get("SENIOR_ANALYST_AV_KEY", "")
NEWSAPI_KEY = os.environ.get("SENIOR_ANALYST_NEWSAPI_KEY", "")


def has_fmp() -> bool:
    return bool(FMP_KEY)

def has_av() -> bool:
    return bool(AV_KEY)

def has_newsapi() -> bool:
    return bool(NEWSAPI_KEY)


# --- Source Availability ---

# Built at startup: lists which sources are available for each tool.
# Populated by build_source_registry() after imports.
AVAILABLE_SOURCES: dict[str, list[str]] = {}


def build_source_registry():
    """Detect available sources and build priority lists for each tool."""
    sources = {
        "company_financials": [],
        "company_profile": [],
        "competitor_compare": [],
        "market_data": [],
        "news_search": [],
        "industry_data": [],
        "stock_news": [],
    }

    # FMP (Tier 1, needs key)
    if has_fmp():
        for tool in sources:
            sources[tool].append("fmp")

    # Eastmoney (Tier 0, always available)
    for tool in ["company_financials", "company_profile", "market_data", "news_search", "industry_data", "stock_news"]:
        sources[tool].append("eastmoney")

    # Akshare (Tier 0, always available)
    for tool in ["company_financials", "company_profile", "market_data", "news_search", "industry_data", "stock_news"]:
        sources[tool].append("akshare")

    # yfinance (Tier 0, always available)
    for tool in ["company_financials", "company_profile", "competitor_compare"]:
        sources[tool].append("yfinance")

    # Alpha Vantage (Tier 1, needs key)
    if has_av():
        for tool in ["company_financials", "company_profile", "news_search", "stock_news"]:
            sources[tool].append("alphavantage")

    # NewsAPI (Tier 1, needs key)
    if has_newsapi():
        for tool in ["news_search", "stock_news"]:
            sources[tool].append("newsapi")

    AVAILABLE_SOURCES.update(sources)

    active = {k: v for k, v in sources.items() if v}
    logger.info(f"Source registry: {active}")
    if has_fmp():
        logger.info("FMP: key detected, Tier 1 enabled")
    if has_av():
        logger.info("Alpha Vantage: key detected, Tier 1 enabled")
    if has_newsapi():
        logger.info("NewsAPI: key detected, Tier 1 enabled")


# --- Caching ---

CACHE_TTL = {
    "financials": 3600,     # 1 hour
    "profile": 86400,       # 24 hours
    "news": 300,            # 5 minutes
    "market": 1800,         # 30 minutes
    "industry": 86400,      # 24 hours
    "stock_news": 300,      # 5 minutes
    "peers": 86400,         # 24 hours
}

caches = {k: TTLCache(maxsize=100, ttl=v) for k, v in CACHE_TTL.items()}


def cache_key(category: str, *args) -> str:
    return f"{category}:{':'.join(str(a) for a in args)}"


def get_cache(category: str) -> TTLCache:
    return caches.get(category, caches["financials"])


# --- Timeout Strategy ---

def compute_timeouts(n_sources: int, total_budget: float = 8.0) -> list[float]:
    """Distribute timeout budget across sources, front-loading higher-priority ones."""
    if n_sources <= 1:
        return [total_budget]
    if n_sources == 2:
        return [4.0, 4.0]
    if n_sources == 3:
        return [3.0, 3.0, 2.0]
    # 4+: front half gets 55%, back half gets 45%
    top = max(2, n_sources // 2)
    top_timeout = total_budget * 0.55 / top
    bottom_timeout = total_budget * 0.45 / (n_sources - top)
    return [top_timeout] * top + [bottom_timeout] * (n_sources - top)
