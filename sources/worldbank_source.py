"""World Bank Open Data source — Tier 0 (no API key required).

Provides global macroeconomic indicators for 200+ countries.
Docs: https://datahelpdesk.worldbank.org/knowledgebase/articles/889392
"""

import logging
from typing import Any

import httpx

from .base import BaseSource, DataResult, MacroSeriesData
from .config import cache_key, get_cache

logger = logging.getLogger(__name__)

WB_BASE = "https://api.worldbank.org/v2"


REGION_TO_COUNTRY = {
    "US": "USA", "USA": "USA",
    "CN": "CHN", "CHN": "CHN", "CHINA": "CHN",
    "EU": "EUU", "EUR": "EUU", "EURO": "EUU",
    "JP": "JPN", "JPN": "JPN",
    "UK": "GBR", "GBR": "GBR",
    "DE": "DEU", "FR": "FRA", "IN": "IND",
    "GLOBAL": "WLD", "WORLD": "WLD",
}


INDICATOR_MAP = {
    "gdp":            {"code": "NY.GDP.MKTP.CD", "unit": "USD"},
    "gdp_growth":     {"code": "NY.GDP.MKTP.KD.ZG", "unit": "%"},
    "gdp_per_capita": {"code": "NY.GDP.PCAP.CD", "unit": "USD"},
    "cpi":            {"code": "FP.CPI.TOTL", "unit": "index 2010=100"},
    "cpi_yoy":        {"code": "FP.CPI.TOTL.ZG", "unit": "%"},
    "unemployment":   {"code": "SL.UEM.TOTL.ZS", "unit": "%"},
    "interest_rate":  {"code": "FR.INR.RINR", "unit": "%"},
    "population":     {"code": "SP.POP.TOTL", "unit": "persons"},
    "trade_balance":  {"code": "NE.RSB.GNFS.CD", "unit": "USD"},
    "fdi":            {"code": "BX.KLT.DINV.CD.WD", "unit": "USD"},
    "exports":        {"code": "NE.EXP.GNFS.CD", "unit": "USD"},
    "imports":        {"code": "NE.IMP.GNFS.CD", "unit": "USD"},
    "current_account":{"code": "BN.CAB.XOKA.CD", "unit": "USD"},
    "gov_debt_pct_gdp": {"code": "GC.DOD.TOTL.GD.ZS", "unit": "% of GDP"},
}


class WorldBankSource(BaseSource):
    name = "worldbank"

    async def get_macro_data(
        self, indicator: str, region: str = "global", period: str = "annual", years: int = 3
    ) -> DataResult:
        ind_key = indicator.lower()
        country_key = REGION_TO_COUNTRY.get(region.upper(), region.upper())

        if ind_key not in INDICATOR_MAP:
            return DataResult(
                success=False,
                error=f"World Bank does not support indicator='{indicator}'. "
                      f"Supported: {sorted(INDICATOR_MAP.keys())}",
            )

        cfg = INDICATOR_MAP[ind_key]
        ck = cache_key("macro", "worldbank", country_key, cfg["code"], years)
        cache = get_cache("macro")
        if ck in cache:
            return cache[ck]

        path = f"country/{country_key}/indicator/{cfg['code']}"
        try:
            async with httpx.AsyncClient(timeout=6.0, follow_redirects=True) as client:
                resp = await client.get(
                    f"{WB_BASE}/{path}",
                    params={"format": "json", "per_page": max(years * 2, 10), "date": _date_range(years)},
                )
                resp.raise_for_status()
                payload = resp.json()
        except Exception as e:
            logger.warning(f"World Bank request failed ({path}): {e}")
            return DataResult(success=False, error=str(e))

        # WB returns [metadata, [observations]]
        if not isinstance(payload, list) or len(payload) < 2 or payload[1] is None:
            return DataResult(success=False, error="World Bank returned empty data")

        observations = payload[1]
        points = []
        for obs in observations:
            v = obs.get("value")
            if v is None:
                continue
            try:
                points.append({
                    "date": obs.get("date", ""),
                    "value": float(v),
                    "unit": cfg["unit"],
                })
            except (ValueError, TypeError):
                continue

        if not points:
            return DataResult(success=False, error="World Bank returned no usable observations")

        series = MacroSeriesData(
            indicator=indicator,
            region=country_key,
            period="annual",  # WB indicators are annual
            unit=cfg["unit"],
            series_id=cfg["code"],
            points=points,
            notes=f"Source: World Bank ({cfg['code']}, country={country_key})",
        )
        result = DataResult(success=True, data=series, source="worldbank")
        cache[ck] = result
        return result


def _date_range(years: int) -> str:
    from datetime import datetime
    end = datetime.now().year
    # WB indicators are annual and lag by 1-2 years; widen the window so we
    # always return at least `years` real points even for the latest year.
    start = end - max(years + 1, 2)
    return f"{start}:{end}"
