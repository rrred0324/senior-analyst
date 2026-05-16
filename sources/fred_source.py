"""FRED data source — Tier 1 (requires free API key from St. Louis Fed).

Provides US macroeconomic indicators: GDP, CPI, unemployment, interest rates, M2, etc.
Sign up: https://fredaccount.stlouisfed.org/apikey
"""

import logging
from typing import Any

import httpx

from .base import BaseSource, DataResult, MacroSeriesData, MacroDataPoint
from .config import FRED_KEY, cache_key, get_cache

logger = logging.getLogger(__name__)

FRED_BASE = "https://api.stlouisfed.org/fred"


INDICATOR_MAP = {
    ("gdp", "US"): {"series_id": "GDP", "unit": "USD billion", "freq": "Q"},
    ("gdp_real", "US"): {"series_id": "GDPC1", "unit": "USD billion (chained 2017)", "freq": "Q"},
    ("cpi", "US"): {"series_id": "CPIAUCSL", "unit": "index 1982-1984=100", "freq": "M"},
    ("cpi_yoy", "US"): {"series_id": "CPIAUCSL", "unit": "%", "freq": "M", "transform": "yoy_pct"},
    ("ppi", "US"): {"series_id": "PPIACO", "unit": "index 1982=100", "freq": "M"},
    ("unemployment", "US"): {"series_id": "UNRATE", "unit": "%", "freq": "M"},
    ("interest_rate", "US"): {"series_id": "FEDFUNDS", "unit": "%", "freq": "M"},
    ("treasury_10y", "US"): {"series_id": "DGS10", "unit": "%", "freq": "D"},
    ("treasury_2y", "US"): {"series_id": "DGS2", "unit": "%", "freq": "D"},
    ("m2", "US"): {"series_id": "M2SL", "unit": "USD billion", "freq": "M"},
    ("pmi", "US"): {"series_id": "MANEMP", "unit": "thousands of persons", "freq": "M"},  # proxy via mfg employment
    ("retail_sales", "US"): {"series_id": "RSAFS", "unit": "USD million", "freq": "M"},
    ("industrial_production", "US"): {"series_id": "INDPRO", "unit": "index 2017=100", "freq": "M"},
    ("housing_starts", "US"): {"series_id": "HOUST", "unit": "thousands", "freq": "M"},
    ("consumer_sentiment", "US"): {"series_id": "UMCSENT", "unit": "index", "freq": "M"},
    ("fx_dxy", "global"): {"series_id": "DTWEXBGS", "unit": "index", "freq": "D"},
}


class FREDSource(BaseSource):
    name = "fred"

    def __init__(self):
        if not FRED_KEY:
            raise RuntimeError("FRED API key not configured (SENIOR_ANALYST_FRED_KEY)")
        self._apikey = FRED_KEY

    async def _get(self, path: str, params: dict, timeout: float = 5.0) -> dict | None:
        params = {**params, "api_key": self._apikey, "file_type": "json"}
        try:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                resp = await client.get(f"{FRED_BASE}/{path}", params=params)
                resp.raise_for_status()
                return resp.json()
        except Exception as e:
            logger.warning(f"FRED request failed ({path}): {e}")
            return None

    async def get_macro_data(
        self, indicator: str, region: str = "US", period: str = "monthly", years: int = 3
    ) -> DataResult:
        ind_key = (indicator.lower(), region.upper())
        if ind_key not in INDICATOR_MAP:
            return DataResult(
                success=False,
                error=f"FRED does not support indicator='{indicator}' for region='{region}'. "
                      f"Supported: {sorted(set(k for k, _ in INDICATOR_MAP))}",
            )

        cfg = INDICATOR_MAP[ind_key]
        ck = cache_key("macro", "fred", cfg["series_id"], period, years)
        cache = get_cache("macro")
        if ck in cache:
            return cache[ck]

        # FRED limit: ~years*12 monthly, ~years*4 quarterly, ~years*250 daily
        freq_to_count = {"D": years * 250, "M": years * 12, "Q": years * 4}
        limit = freq_to_count.get(cfg["freq"], years * 12)

        observations = await self._get(
            "series/observations",
            {"series_id": cfg["series_id"], "limit": limit, "sort_order": "desc"},
        )
        if not observations or "observations" not in observations:
            result = DataResult(success=False, error=f"FRED returned no data for {cfg['series_id']}")
            return result

        raw_points = []
        for obs in observations["observations"]:
            try:
                v = obs.get("value", ".")
                if v == "." or v == "":
                    continue
                raw_points.append(MacroDataPoint(date=obs["date"], value=float(v), unit=cfg["unit"]))
            except (ValueError, KeyError):
                continue

        # Apply year-over-year transform if configured
        if cfg.get("transform") == "yoy_pct" and len(raw_points) > 12:
            sorted_pts = sorted(raw_points, key=lambda p: p.date)
            yoy = []
            for i in range(12, len(sorted_pts)):
                prev = sorted_pts[i - 12].value
                cur = sorted_pts[i].value
                if prev and prev != 0:
                    yoy.append(MacroDataPoint(
                        date=sorted_pts[i].date,
                        value=round((cur - prev) / prev * 100, 2),
                        unit=cfg["unit"],
                    ))
            raw_points = list(reversed(yoy))

        series = MacroSeriesData(
            indicator=indicator,
            region=region,
            period=period,
            unit=cfg["unit"],
            series_id=cfg["series_id"],
            points=[{"date": p.date, "value": p.value, "unit": p.unit} for p in raw_points[:limit]],
            notes=f"Source: FRED ({cfg['series_id']})",
        )
        result = DataResult(success=True, data=series, source="fred")
        cache[ck] = result
        return result
