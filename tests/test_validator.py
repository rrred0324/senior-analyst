"""Unit tests for the cross-validation engine (offline, no network)."""

import pytest

from sources.base import (
    ConfidenceScore, CrossValidationResult, AnomalyFlag,
    ReconciliationCheck, DataResult, FinancialData,
)
from sources.validator import Validator, _deviation_pct, _median, _safe_div

pytestmark = pytest.mark.unit

_validator = Validator()


# --- Helper functions ---

def test_safe_div():
    assert _safe_div(10, 2) == 5.0
    assert _safe_div(10, 0) is None
    assert _safe_div(None, 2) is None
    assert _safe_div(10, None) is None


def test_deviation_pct():
    assert _deviation_pct(110, 100) == 10.0
    assert _deviation_pct(90, 100) == 10.0
    assert _deviation_pct(None, 100) is None
    assert _deviation_pct(100, 0) is None


def test_median():
    assert _median([1, 2, 3]) == 2
    assert _median([1, 2]) == 1.5
    assert _median([5]) == 5
    assert _median([]) is None


# --- compare_sources ---

def test_compare_single_source():
    r = DataResult(
        success=True,
        data={"company": "AAPL", "ticker": "AAPL", "data": [
            {"year": 2024, "revenue": 1000, "net_income": 200, "gross_profit": 400, "operating_cash_flow": 250, "total_assets": 5000, "total_liabilities": 3000},
        ]},
        source="eastmoney",
    )
    cv = _validator.compare_sources([r])
    assert cv.confidence.source_count == 1
    assert cv.confidence.source_agreement == 1.0
    assert cv.confidence.score >= 0.7
    assert len(cv.discrepancies) == 0


def test_compare_two_sources_agree():
    r1 = DataResult(
        success=True,
        data={"company": "AAPL", "ticker": "AAPL", "data": [
            {"year": 2024, "revenue": 1000, "net_income": 200},
        ]},
        source="eastmoney",
    )
    r2 = DataResult(
        success=True,
        data={"company": "AAPL", "ticker": "AAPL", "data": [
            {"year": 2024, "revenue": 1010, "net_income": 202},
        ]},
        source="yfinance",
    )
    cv = _validator.compare_sources([r1, r2])
    assert cv.confidence.source_count == 2
    assert len(cv.discrepancies) == 0  # <10% deviation
    assert cv.reconciled["revenue"] == 1005.0  # median


def test_compare_two_sources_disagree():
    r1 = DataResult(
        success=True,
        data={"company": "X", "data": [{"year": 2024, "revenue": 1000}]},
        source="eastmoney",
    )
    r2 = DataResult(
        success=True,
        data={"company": "X", "data": [{"year": 2024, "revenue": 1500}]},
        source="yfinance",
    )
    cv = _validator.compare_sources([r1, r2])
    assert len(cv.discrepancies) == 1
    assert cv.discrepancies[0]["severity"] == "critical"
    assert cv.discrepancies[0]["deviation_pct"] == pytest.approx(33.3, abs=0.2)


def test_compare_no_valid_sources():
    r = DataResult(success=False, error="fail")
    cv = _validator.compare_sources([r])
    assert cv.confidence.score == 0.0
    assert cv.confidence.source_count == 0


# --- detect_anomalies ---

def test_anomaly_revenue_spike():
    periods = [
        {"year": 2024, "revenue": 200, "net_income": 30, "gross_profit": 80, "operating_cash_flow": 40},
        {"year": 2023, "revenue": 100, "net_income": 20, "gross_profit": 40, "operating_cash_flow": 25},
    ]
    flags = _validator.detect_anomalies(periods)
    revenue_flags = [f for f in flags if f.field == "revenue"]
    assert len(revenue_flags) == 1
    assert revenue_flags[0].rule == "qoq_spike>50%"


def test_anomaly_margin_compression():
    periods = [
        {"year": 2024, "revenue": 100, "gross_profit": 15, "net_income": 5, "operating_cash_flow": 10},
        {"year": 2023, "revenue": 100, "gross_profit": 30, "net_income": 10, "operating_cash_flow": 15},
    ]
    flags = _validator.detect_anomalies(periods)
    margin_flags = [f for f in flags if f.field == "gross_margin"]
    assert len(margin_flags) == 1
    assert margin_flags[0].severity == "warning"


def test_anomaly_ocf_ni_ratio_sustained():
    periods = [
        {"year": 2024, "revenue": 100, "net_income": 100, "gross_profit": 50, "operating_cash_flow": 30},
        {"year": 2023, "revenue": 90, "net_income": 90, "gross_profit": 45, "operating_cash_flow": 20},
    ]
    flags = _validator.detect_anomalies(periods)
    ocf_flags = [f for f in flags if f.field == "ocf_ni_ratio"]
    assert len(ocf_flags) >= 1
    assert any(f.severity == "critical" for f in ocf_flags)


def test_no_anomalies_clean_data():
    periods = [
        {"year": 2024, "revenue": 105, "net_income": 21, "gross_profit": 42, "operating_cash_flow": 25},
        {"year": 2023, "revenue": 100, "net_income": 20, "gross_profit": 40, "operating_cash_flow": 24},
    ]
    flags = _validator.detect_anomalies(periods)
    assert len(flags) == 0


# --- reconcile_statements ---

def test_reconcile_positive_equity():
    period = {
        "total_assets": 5000, "total_liabilities": 3000,
        "revenue": 1000, "gross_profit": 400,
        "net_income": 200, "operating_cash_flow": 250,
    }
    checks = _validator.reconcile_statements(period)
    equity_check = next(c for c in checks if c.name == "equity_check")
    assert equity_check.passed is True


def test_reconcile_negative_equity():
    period = {
        "total_assets": 2000, "total_liabilities": 3000,
        "revenue": 1000, "gross_profit": 400,
        "net_income": 200, "operating_cash_flow": 250,
    }
    checks = _validator.reconcile_statements(period)
    equity_check = next(c for c in checks if c.name == "equity_check")
    assert equity_check.passed is False


def test_reconcile_ocf_quality_negative():
    period = {
        "total_assets": 5000, "total_liabilities": 3000,
        "revenue": 1000, "gross_profit": 400,
        "net_income": 200, "operating_cash_flow": -50,
    }
    checks = _validator.reconcile_statements(period)
    cf_check = next(c for c in checks if c.name == "cash_flow_quality")
    assert cf_check.passed is False


def test_reconcile_invalid_gross_profit():
    period = {
        "total_assets": 5000, "total_liabilities": 3000,
        "revenue": 100, "gross_profit": 200,
        "net_income": 50, "operating_cash_flow": 60,
    }
    checks = _validator.reconcile_statements(period)
    gp_check = next((c for c in checks if c.name == "gross_profit_check"), None)
    assert gp_check is not None
    assert gp_check.passed is False


# --- build_confidence_for_tool ---

def test_confidence_for_successful_result():
    r = DataResult(
        success=True,
        data={"company": "AAPL", "data": [{"year": 2024, "revenue": 1000, "net_income": 200}]},
        source="eastmoney",
    )
    conf = _validator.build_confidence_for_tool(r)
    assert conf.score >= 0.7
    assert conf.source_count == 1
    assert conf.data_freshness == "real-time"


def test_confidence_for_failed_result():
    r = DataResult(success=False, error="fail")
    conf = _validator.build_confidence_for_tool(r)
    assert conf.score == 0.0
    assert conf.source_count == 0


def test_confidence_with_anomalies():
    r = DataResult(
        success=True,
        data={"company": "X", "data": [{"year": 2024, "revenue": 1000, "net_income": 200}]},
        source="eastmoney",
    )
    anomalies = [AnomalyFlag(field="revenue", detail="spike")]
    conf = _validator.build_confidence_for_tool(r, anomalies=anomalies)
    base_conf = _validator.build_confidence_for_tool(r)
    assert conf.score < base_conf.score  # anomaly should lower confidence
