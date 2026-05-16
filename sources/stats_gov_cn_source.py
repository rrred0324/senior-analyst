"""China official statistics source — Tier 0 (no API key required).

Wraps akshare's macro_china_* and macro_pboc_* functions to expose China's
official macro data (NBS, PBOC, customs) in the unified MacroSeriesData format.

NBS = National Bureau of Statistics; PBOC = People's Bank of China.
"""

import asyncio
import logging
from typing import Any

from .base import BaseSource, DataResult, MacroSeriesData
from .config import cache_key, get_cache

logger = logging.getLogger(__name__)


# (indicator, period) -> (akshare_fn_name, value_col, date_col, unit, notes)
INDICATOR_MAP = {
    ("gdp", "annual"):       ("macro_china_gdp_yearly",         "今值",        "日期",     "%",    "GDP YoY (NBS)"),
    ("gdp", "quarterly"):    ("macro_china_gdp",                None,         None,       "亿元", "GDP quarterly (NBS)"),
    ("cpi", "monthly"):      ("macro_china_cpi_monthly",        "今值",        "日期",     "%",    "CPI MoM (NBS)"),
    ("cpi", "annual"):       ("macro_china_cpi_yearly",         "今值",        "日期",     "%",    "CPI YoY (NBS)"),
    ("cpi", None):           ("macro_china_cpi",                None,         None,       "index","CPI index (NBS)"),
    ("ppi", "monthly"):      ("macro_china_ppi_yearly",         "今值",        "日期",     "%",    "PPI YoY (NBS)"),
    ("ppi", None):           ("macro_china_ppi",                None,         None,       "%",    "PPI index (NBS)"),
    ("pmi", "monthly"):      ("macro_china_pmi_yearly",         "今值",        "日期",     "index","Manufacturing PMI (NBS)"),
    ("pmi", None):           ("macro_china_pmi",                None,         None,       "index","PMI series (NBS)"),
    ("m2", "monthly"):       ("macro_china_m2_yearly",          "今值",        "日期",     "%",    "M2 YoY (PBOC)"),
    ("m2", None):            ("macro_china_supply_of_money",    None,         None,       "亿元", "Money supply (PBOC)"),
    ("interest_rate", None): ("macro_china_lpr",                None,         None,       "%",    "Loan Prime Rate (PBOC)"),
    ("unemployment", None):  ("macro_china_urban_unemployment", None,         None,       "%",    "Urban unemployment (NBS)"),
    ("retail_sales", "monthly"): ("macro_china_consumer_goods_retail", None,  None,       "亿元", "Retail sales (NBS)"),
    ("fx", None):            ("macro_china_foreign_exchange_gold", None,     None,       "USD bn","FX reserves & gold (PBOC)"),
    ("fdi", "monthly"):      ("macro_china_fdi",                None,         None,       "USD bn","FDI inflows (MOFCOM)"),
    ("exports", "monthly"):  ("macro_china_exports_yoy",        "今值",        "日期",     "%",    "Exports YoY (Customs)"),
    ("imports", "monthly"):  ("macro_china_imports_yoy",        "今值",        "日期",     "%",    "Imports YoY (Customs)"),
    ("housing_price", None): ("macro_china_new_house_price",    None,         None,       "index","New house price index (NBS)"),
    ("industrial_production", "monthly"): ("macro_china_industrial_production_yoy", "今值", "日期", "%", "Industrial production YoY (NBS)"),
}


class StatsGovCNSource(BaseSource):
    """China NBS/PBOC macro data via akshare wrappers."""

    name = "stats_gov_cn"

    def __init__(self):
        try:
            import akshare as ak
            self.ak = ak
            self._available = True
        except ImportError:
            logger.warning("akshare not installed; stats_gov_cn source unavailable")
            self._available = False

    async def get_macro_data(
        self, indicator: str, region: str = "CN", period: str = "monthly", years: int = 3
    ) -> DataResult:
        if not self._available:
            return DataResult(success=False, error="akshare not installed")

        if region.upper() not in ("CN", "CHINA", "CHN"):
            return DataResult(success=False, error=f"stats_gov_cn only supports region='CN', got '{region}'")

        ind = indicator.lower()
        # match (indicator, period) first, then (indicator, None)
        cfg = INDICATOR_MAP.get((ind, period.lower())) or INDICATOR_MAP.get((ind, None))
        if cfg is None:
            return DataResult(
                success=False,
                error=f"stats_gov_cn does not support indicator='{indicator}'. "
                      f"Supported: {sorted(set(k for k, _ in INDICATOR_MAP))}",
            )

        fn_name, value_col, date_col, unit, notes = cfg
        ck = cache_key("macro", "stats_gov_cn", fn_name, period, years)
        cache = get_cache("macro")
        if ck in cache:
            return cache[ck]

        try:
            fn = getattr(self.ak, fn_name, None)
            if fn is None:
                return DataResult(success=False, error=f"akshare missing function {fn_name}")
            df = await asyncio.to_thread(fn)
        except Exception as e:
            logger.warning(f"stats_gov_cn akshare call {fn_name} failed: {e}")
            return DataResult(success=False, error=str(e))

        if df is None or (hasattr(df, "empty") and df.empty):
            return DataResult(success=False, error=f"{fn_name} returned empty dataframe")

        points = _df_to_points(df, value_col, date_col, unit, max_rows=years * 12 + 24)
        if not points:
            return DataResult(success=False, error=f"{fn_name} returned no parseable rows")

        series = MacroSeriesData(
            indicator=indicator,
            region="CN",
            period=period,
            unit=unit,
            series_id=fn_name,
            points=points,
            notes=notes,
        )
        result = DataResult(success=True, data=series, source="stats_gov_cn")
        cache[ck] = result
        return result


def _df_to_points(df, value_col: str | None, date_col: str | None, unit: str, max_rows: int = 60) -> list[dict]:
    """Convert akshare dataframe to MacroDataPoint list (as dicts).

    Heuristics:
      - If value_col / date_col specified, use them.
      - Otherwise, find the first date-like column and the first numeric column.
      - Returns rows sorted DESC by date (most recent first), trimmed to max_rows.
    """
    try:
        cols = list(df.columns)

        # Pick date column
        if date_col and date_col in cols:
            dc = date_col
        else:
            dc = _detect_date_col(df, cols)

        # Pick value column
        if value_col and value_col in cols:
            vc = value_col
        else:
            vc = _detect_value_col(df, cols, exclude=dc)

        if not dc or not vc:
            return []

        # Sort by date descending if possible (akshare often returns oldest-first)
        try:
            df = df.sort_values(by=dc, ascending=False)
        except Exception:
            pass

        points = []
        for _, row in df.head(max_rows).iterrows():
            try:
                d = str(row[dc])
                v_raw = row[vc]
                if v_raw is None or str(v_raw) == "nan":
                    continue
                v = float(v_raw)
                points.append({"date": d, "value": v, "unit": unit})
            except (ValueError, TypeError):
                continue
        return points
    except Exception as e:
        logger.debug(f"_df_to_points failed: {e}")
        return []


def _detect_date_col(df, cols: list) -> str | None:
    candidates = ["日期", "时间", "month", "date", "year", "公布日期", "统计时间", "时间区间"]
    for c in candidates:
        if c in cols:
            return c
    # Fallback: first object/string column
    for c in cols:
        try:
            if df[c].dtype == "object":
                return c
        except Exception:
            continue
    return cols[0] if cols else None


def _detect_value_col(df, cols: list, exclude: str | None = None) -> str | None:
    candidates = ["今值", "value", "数值", "GDP", "CPI", "PPI", "M2", "金额", "总量", "指数"]
    for c in candidates:
        if c in cols and c != exclude:
            return c
    # Fallback: first numeric column != exclude
    for c in cols:
        if c == exclude:
            continue
        try:
            df[c].astype(float)
            return c
        except Exception:
            continue
    return None
