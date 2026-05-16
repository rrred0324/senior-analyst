"""Cross-validation engine: multi-source comparison, three-statement reconciliation,
anomaly detection, and confidence scoring."""

import logging
import math
from dataclasses import asdict
from typing import Any

from .base import (
    ConfidenceScore,
    CrossValidationResult,
    AnomalyFlag,
    ReconciliationCheck,
    DataResult,
)

logger = logging.getLogger(__name__)

# --- Thresholds ---

DISCREPANCY_WARNING_PCT = 10.0   # >10% deviation between sources → warning
DISCREPANCY_CRITICAL_PCT = 25.0  # >25% deviation → critical
RECONCILIATION_TOLERANCE_PCT = 2.0  # ±2% for three-statement checks
QOQ_SPIKE_THRESHOLD = 50.0      # revenue QoQ >50% → flag
MARGIN_CHANGE_PP = 5.0           # gross margin change >5pp → flag
OCF_NI_RATIO_FLOOR = 0.5        # OCF/NI < 0.5 for 2+ periods → flag

# Confidence weights
W_AGREEMENT = 0.4
W_FRESHNESS = 0.2
W_COMPLETENESS = 0.2
W_ANOMALY = 0.2

FRESHNESS_SCORES = {
    "real-time": 1.0,
    "cached": 0.8,
    "stale": 0.5,
    "unknown": 0.6,
}

FINANCIAL_FIELDS = [
    "revenue", "gross_profit", "net_income",
    "operating_cash_flow", "total_assets", "total_liabilities",
]

REQUIRED_FIELDS = ["revenue", "net_income"]


def _safe_div(a: float | None, b: float | None) -> float | None:
    if a is None or b is None or b == 0:
        return None
    return a / b


def _deviation_pct(a: float | None, b: float | None) -> float | None:
    if a is None or b is None or b == 0:
        return None
    return abs(a - b) / abs(b) * 100


def _median(values: list[float]) -> float | None:
    if not values:
        return None
    sorted_v = sorted(values)
    n = len(sorted_v)
    if n % 2 == 1:
        return sorted_v[n // 2]
    return (sorted_v[n // 2 - 1] + sorted_v[n // 2]) / 2


class Validator:
    """Cross-validate financial data from multiple sources."""

    def compare_sources(
        self,
        results: list[DataResult],
        fields: list[str] | None = None,
    ) -> CrossValidationResult:
        """Compare values for the same company across multiple source results.

        Each DataResult.data is expected to be a dict with a "data" key
        containing a list of period dicts (e.g. [{"year": 2024, "revenue": ...}, ...]).
        We compare the latest period across sources.
        """
        fields = fields or FINANCIAL_FIELDS
        valid_results = [r for r in results if r.has_data()]
        n_sources = len(valid_results)

        if n_sources == 0:
            return CrossValidationResult(
                confidence=ConfidenceScore(score=0.0, source_count=0, notes="No valid sources"),
            )

        # Extract latest-period values from each source
        source_values: dict[str, list[tuple[str, float]]] = {}
        for field in fields:
            source_values[field] = []

        for r in valid_results:
            data = r.data
            if isinstance(data, dict) and "data" in data:
                periods = data["data"]
                if not periods:
                    continue
                latest = periods[0]  # already sorted most-recent-first
                for field in fields:
                    val = latest.get(field)
                    if val is not None:
                        try:
                            source_values[field].append((r.source, float(val)))
                        except (TypeError, ValueError):
                            pass

        # Find discrepancies
        discrepancies = []
        for field in fields:
            vals = source_values.get(field, [])
            if len(vals) < 2:
                continue
            # Compare each pair
            for i in range(len(vals)):
                for j in range(i + 1, len(vals)):
                    src_a, val_a = vals[i]
                    src_b, val_b = vals[j]
                    dev = _deviation_pct(val_a, val_b)
                    if dev is not None and dev > DISCREPANCY_WARNING_PCT:
                        severity = "critical" if dev > DISCREPANCY_CRITICAL_PCT else "warning"
                        discrepancies.append({
                            "field": field,
                            "sources": [src_a, src_b],
                            "values": {src_a: val_a, src_b: val_b},
                            "deviation_pct": round(dev, 1),
                            "severity": severity,
                        })

        # Reconcile: take median for each field
        reconciled = {}
        for field in fields:
            vals = [v for _, v in source_values.get(field, [])]
            med = _median(vals)
            if med is not None:
                reconciled[field] = round(med, 2)

        # Compute source agreement
        total_comparisons = sum(
            max(0, len(source_values.get(f, [])) - 1)
            for f in fields
        )
        discrepancy_count = len(discrepancies)
        if total_comparisons == 0:
            agreement = 1.0 if n_sources == 1 else 0.5
        else:
            agreement = max(0.0, 1.0 - discrepancy_count / max(total_comparisons, 1))
            agreement = round(agreement, 2)

        # Compute completeness
        filled = sum(1 for f in REQUIRED_FIELDS if source_values.get(f))
        completeness = filled / len(REQUIRED_FIELDS) if REQUIRED_FIELDS else 1.0

        # Data freshness (assume "real-time" for fresh queries)
        freshness = "real-time" if n_sources > 0 else "unknown"

        # Compute confidence
        confidence = self._compute_confidence(
            agreement=agreement,
            freshness=freshness,
            completeness=completeness,
            anomaly_count=len(discrepancies),
            source_count=n_sources,
        )

        return CrossValidationResult(
            values=source_values,
            discrepancies=discrepancies,
            reconciled=reconciled,
            confidence=confidence,
        )

    def detect_anomalies(
        self,
        periods: list[dict],
        currency: str = "USD",
    ) -> list[AnomalyFlag]:
        """Run anomaly detection rules on a time series of financial periods.

        periods: list of dicts with keys like year, revenue, gross_profit,
                 net_income, operating_cash_flow, total_assets, total_liabilities
        Sorted most-recent-first.
        """
        flags: list[AnomalyFlag] = []
        if not periods:
            return flags

        for i, p in enumerate(periods):
            period_label = str(p.get("year", f"period_{i}"))
            if p.get("quarter"):
                period_label += f"-{p['quarter']}"

            # Rule 1: Revenue QoQ spike
            if i < len(periods) - 1:
                prev = periods[i + 1]
                rev = p.get("revenue")
                prev_rev = prev.get("revenue")
                if rev and prev_rev and prev_rev != 0:
                    qoq = (rev - prev_rev) / abs(prev_rev) * 100
                    if abs(qoq) > QOQ_SPIKE_THRESHOLD:
                        flags.append(AnomalyFlag(
                            field="revenue",
                            period=period_label,
                            severity="warning",
                            rule=f"qoq_spike>{QOQ_SPIKE_THRESHOLD:.0f}%",
                            detail=f"Revenue QoQ change: {qoq:+.1f}%",
                            value=rev,
                            threshold=QOQ_SPIKE_THRESHOLD,
                        ))

            # Rule 2: Gross margin change
            gp = p.get("gross_profit")
            rev = p.get("revenue")
            if gp is not None and rev and rev != 0:
                margin = gp / rev * 100
                if i < len(periods) - 1:
                    prev = periods[i + 1]
                    prev_gp = prev.get("gross_profit")
                    prev_rev = prev.get("revenue")
                    if prev_gp is not None and prev_rev and prev_rev != 0:
                        prev_margin = prev_gp / prev_rev * 100
                        margin_change = margin - prev_margin
                        if abs(margin_change) > MARGIN_CHANGE_PP:
                            flags.append(AnomalyFlag(
                                field="gross_margin",
                                period=period_label,
                                severity="warning",
                                rule=f"margin_change>{MARGIN_CHANGE_PP:.0f}pp",
                                detail=f"Gross margin: {margin:.1f}% (prev: {prev_margin:.1f}%, Δ{margin_change:+.1f}pp)",
                                value=round(margin, 1),
                                threshold=MARGIN_CHANGE_PP,
                            ))

            # Rule 3: OCF/NI ratio
            ocf = p.get("operating_cash_flow")
            ni = p.get("net_income")
            if ocf is not None and ni and ni > 0:
                ratio = ocf / ni
                if ratio < OCF_NI_RATIO_FLOOR:
                    # Check if sustained (previous period also low)
                    sustained = False
                    if i < len(periods) - 1:
                        prev = periods[i + 1]
                        prev_ocf = prev.get("operating_cash_flow")
                        prev_ni = prev.get("net_income")
                        if prev_ocf is not None and prev_ni and prev_ni > 0:
                            if prev_ocf / prev_ni < OCF_NI_RATIO_FLOOR:
                                sustained = True
                    severity = "critical" if sustained else "warning"
                    flags.append(AnomalyFlag(
                        field="ocf_ni_ratio",
                        period=period_label,
                        severity=severity,
                        rule=f"ocf_ni_ratio<{OCF_NI_RATIO_FLOOR}",
                        detail=f"OCF/NI = {ratio:.2f} {'(sustained 2+ periods)' if sustained else ''}",
                        value=round(ratio, 2),
                        threshold=OCF_NI_RATIO_FLOOR,
                    ))

        return flags

    def reconcile_statements(
        self,
        period: dict,
        tolerance_pct: float = RECONCILIATION_TOLERANCE_PCT,
    ) -> list[ReconciliationCheck]:
        """Three-statement reconciliation for a single period.

        Checks:
        1. Equity = Assets - Liabilities
        2. Gross Profit ≈ Revenue - COGS (if COGS available)
        3. OCF quality: OCF should be positive when NI is positive
        """
        checks: list[ReconciliationCheck] = []

        ta = period.get("total_assets")
        tl = period.get("total_liabilities")
        if ta is not None and tl is not None:
            expected_equity = ta - tl
            # We don't have equity directly, so check if the balance holds
            # Assets should always be > Liabilities for a going concern
            if ta < tl:
                checks.append(ReconciliationCheck(
                    name="equity_check",
                    expected=None,
                    actual=None,
                    deviation_pct=None,
                    passed=False,
                    detail=f"Negative equity: assets ({ta}) < liabilities ({tl})",
                ))
            else:
                checks.append(ReconciliationCheck(
                    name="equity_check",
                    expected=None,
                    actual=expected_equity,
                    deviation_pct=None,
                    passed=True,
                    detail=f"Equity = {expected_equity:.0f} (Assets {ta} - Liabilities {tl})",
                ))

        # Revenue - COGS ≈ Gross Profit
        rev = period.get("revenue")
        gp = period.get("gross_profit")
        if rev is not None and gp is not None:
            implied_cogs = rev - gp
            # COGS should be positive
            if implied_cogs < 0:
                checks.append(ReconciliationCheck(
                    name="gross_profit_check",
                    expected=None,
                    actual=gp,
                    deviation_pct=None,
                    passed=False,
                    detail=f"Gross profit ({gp}) > Revenue ({rev}) — invalid",
                ))
            else:
                checks.append(ReconciliationCheck(
                    name="gross_profit_check",
                    expected=None,
                    actual=gp,
                    deviation_pct=None,
                    passed=True,
                    detail=f"COGS = {implied_cogs:.0f}, Gross Margin = {gp/rev*100:.1f}%",
                ))

        # OCF quality
        ocf = period.get("operating_cash_flow")
        ni = period.get("net_income")
        if ocf is not None and ni is not None:
            if ni > 0 and ocf < 0:
                checks.append(ReconciliationCheck(
                    name="cash_flow_quality",
                    expected=ni,
                    actual=ocf,
                    deviation_pct=None,
                    passed=False,
                    detail=f"Positive net income ({ni}) but negative OCF ({ocf}) — earnings quality concern",
                ))
            else:
                ratio = _safe_div(ocf, ni)
                checks.append(ReconciliationCheck(
                    name="cash_flow_quality",
                    expected=None,
                    actual=ocf,
                    deviation_pct=None,
                    passed=True,
                    detail=f"OCF/NI = {ratio:.2f}" if ratio else f"OCF = {ocf}",
                ))

        return checks

    def _compute_confidence(
        self,
        agreement: float,
        freshness: str,
        completeness: float,
        anomaly_count: int,
        source_count: int,
    ) -> ConfidenceScore:
        """Compute composite confidence score."""
        freshness_score = FRESHNESS_SCORES.get(freshness, 0.6)
        anomaly_penalty = min(anomaly_count * 0.1, 0.5)  # cap at 0.5

        raw = (
            W_AGREEMENT * agreement
            + W_FRESHNESS * freshness_score
            + W_COMPLETENESS * completeness
            - W_ANOMALY * anomaly_penalty
        )

        # Single source gets a floor boost (can't have agreement > 1.0 from one source)
        if source_count == 1:
            raw = min(raw + 0.1, 1.0)

        score = max(0.0, min(1.0, round(raw, 2)))

        return ConfidenceScore(
            score=score,
            source_count=source_count,
            source_agreement=round(agreement, 2),
            data_freshness=freshness,
            notes=f"agreement={agreement:.2f}, freshness={freshness}, completeness={completeness:.2f}, anomalies={anomaly_count}",
        )

    def build_confidence_for_tool(
        self,
        result: DataResult,
        anomalies: list[AnomalyFlag] | None = None,
    ) -> ConfidenceScore:
        """Build a confidence score for a single-source tool result.

        Used for tools where cross-validation isn't performed (macro_data, crypto_data, etc.)
        """
        if not result.has_data():
            return ConfidenceScore(
                score=0.0,
                source_count=0,
                notes="No data returned",
            )

        anomaly_count = len(anomalies) if anomalies else 0
        anomaly_penalty = min(anomaly_count * 0.1, 0.5)

        # Check completeness for financial data
        completeness = 1.0
        if isinstance(result.data, dict) and "data" in result.data:
            periods = result.data.get("data", [])
            if periods:
                latest = periods[0]
                filled = sum(1 for f in REQUIRED_FIELDS if latest.get(f) is not None)
                completeness = filled / len(REQUIRED_FIELDS)

        raw = (
            W_AGREEMENT * 1.0  # single source = perfect agreement with self
            + W_FRESHNESS * 1.0
            + W_COMPLETENESS * completeness
            - W_ANOMALY * anomaly_penalty
        )
        score = max(0.0, min(1.0, round(raw, 2)))

        return ConfidenceScore(
            score=score,
            source_count=1,
            source_agreement=1.0,
            data_freshness="real-time",
            anomalies=[a.detail for a in (anomalies or [])],
            notes=f"single-source({result.source}), completeness={completeness:.2f}, anomalies={anomaly_count}",
        )
