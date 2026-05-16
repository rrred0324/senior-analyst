"""Shared configuration: API key detection, source availability, caching."""

import os
import logging
from pathlib import Path
from cachetools import TTLCache

logger = logging.getLogger(__name__)

# --- API Key Detection ---

USER_CONFIG_DIR = Path.home() / ".config" / "senior_analyst"
USER_ENV_PATH = USER_CONFIG_DIR / ".env"


def _load_dotenv():
    """Load .env files. Project root .env loads first, user-config .env overrides."""
    try:
        from dotenv import load_dotenv
        project_env = Path(__file__).parent.parent / ".env"
        if project_env.exists():
            load_dotenv(project_env)
        if USER_ENV_PATH.exists():
            load_dotenv(USER_ENV_PATH, override=True)
    except ImportError:
        pass

_load_dotenv()

FMP_KEY = os.environ.get("SENIOR_ANALYST_FMP_KEY", "")
AV_KEY = os.environ.get("SENIOR_ANALYST_AV_KEY", "")
NEWSAPI_KEY = os.environ.get("SENIOR_ANALYST_NEWSAPI_KEY", "")
FRED_KEY = os.environ.get("SENIOR_ANALYST_FRED_KEY", "")
COINGECKO_PRO_KEY = os.environ.get("SENIOR_ANALYST_COINGECKO_KEY", "")


def has_fmp() -> bool:
    return bool(FMP_KEY)

def has_av() -> bool:
    return bool(AV_KEY)

def has_newsapi() -> bool:
    return bool(NEWSAPI_KEY)

def has_fred() -> bool:
    return bool(FRED_KEY)

def has_coingecko_pro() -> bool:
    return bool(COINGECKO_PRO_KEY)


KEY_SERVICES = {
    "fmp": {
        "env_var": "SENIOR_ANALYST_FMP_KEY",
        "label": "Financial Modeling Prep",
        "tier": "paid",
        "signup_url": "https://site.financialmodelingprep.com/developer/docs",
        "unlocks": "Global financials, peer recommendations, structured news",
        "free_tier_note": "Free tier: 250 req/day, US stocks only",
    },
    "av": {
        "env_var": "SENIOR_ANALYST_AV_KEY",
        "label": "Alpha Vantage",
        "tier": "free-key",
        "signup_url": "https://www.alphavantage.co/support/#api-key",
        "unlocks": "Global stock fundamentals, news with sentiment",
        "free_tier_note": "Free tier: 25 req/day",
    },
    "newsapi": {
        "env_var": "SENIOR_ANALYST_NEWSAPI_KEY",
        "label": "NewsAPI",
        "tier": "free-key",
        "signup_url": "https://newsapi.org/register",
        "unlocks": "English-language news search",
        "free_tier_note": "Free tier: 100 req/day, dev only",
    },
    "fred": {
        "env_var": "SENIOR_ANALYST_FRED_KEY",
        "label": "FRED (St. Louis Fed)",
        "tier": "free-key",
        "signup_url": "https://fredaccount.stlouisfed.org/apikey",
        "unlocks": "US macro economic data (GDP, CPI, unemployment, rates, M2)",
        "free_tier_note": "Free tier: 120 req/min, no daily cap",
    },
    "coingecko": {
        "env_var": "SENIOR_ANALYST_COINGECKO_KEY",
        "label": "CoinGecko Pro",
        "tier": "paid-optional",
        "signup_url": "https://www.coingecko.com/en/api/pricing",
        "unlocks": "Higher rate limits, historical data, premium endpoints",
        "free_tier_note": "Public API works without key (30 req/min)",
    },
}


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
        "macro_data": [],
        "crypto_data": [],
        "company_valuation": [],
    }

    # FMP (Tier 1, needs key)
    if has_fmp():
        for tool in ["company_financials", "company_profile", "competitor_compare", "market_data", "news_search", "industry_data", "stock_news"]:
            sources[tool].append("fmp")

    # Eastmoney (Tier 0, always available)
    for tool in ["company_financials", "company_profile", "market_data", "news_search", "industry_data", "stock_news"]:
        sources[tool].append("eastmoney")

    # Akshare (Tier 0, always available)
    for tool in ["company_financials", "company_profile", "market_data", "news_search", "industry_data", "stock_news"]:
        sources[tool].append("akshare")

    # stats_gov_cn (Tier 0, China NBS/PBOC via akshare wrappers) — preferred for CN macro
    sources["macro_data"].append("stats_gov_cn")

    # yfinance (Tier 0, always available)
    for tool in ["company_financials", "company_profile", "competitor_compare"]:
        sources[tool].append("yfinance")

    # FRED (Tier 1 free key, US macro)
    if has_fred():
        sources["macro_data"].insert(0, "fred")

    # World Bank (Tier 0, always available, global macro)
    sources["macro_data"].append("worldbank")

    # CoinGecko (Tier 0 always; pro key optional)
    sources["crypto_data"].append("coingecko")

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
    if has_fred():
        logger.info("FRED: key detected, US macro enabled")
    if has_coingecko_pro():
        logger.info("CoinGecko Pro: key detected, premium endpoints enabled")


# --- Caching ---

CACHE_TTL = {
    "financials": 3600,     # 1 hour
    "profile": 86400,       # 24 hours
    "news": 300,            # 5 minutes
    "market": 1800,         # 30 minutes
    "industry": 86400,      # 24 hours
    "stock_news": 300,      # 5 minutes
    "peers": 86400,         # 24 hours
    "macro": 21600,         # 6 hours (macro data updates slowly)
    "crypto": 60,           # 1 minute (crypto moves fast)
    "valuation": 3600,      # 1 hour (derived from financials)
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
