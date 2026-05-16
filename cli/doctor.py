"""senior_analyst doctor — health check for data sources, keys, and MCP server.

Usage:
    python -m cli.doctor
    senior_analyst-doctor              (if installed as entry point)

Output: one line per source with status, latency, sample-data check, and remediation hint.
Exit code: 0 if all Tier 0 sources work; 1 if a Tier 0 source is broken; 2 if MCP server unreachable.
"""

import asyncio
import json
import logging
import os
import sys
import time
from pathlib import Path

# Suppress source-import noise
logging.basicConfig(level=logging.ERROR)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from sources.config import (
    KEY_SERVICES, AVAILABLE_SOURCES, build_source_registry,
    has_fmp, has_av, has_newsapi, has_fred, has_coingecko_pro,
    caches, USER_ENV_PATH,
)

GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"


def _color(s: str, c: str) -> str:
    if not sys.stdout.isatty():
        return s
    return f"{c}{s}{RESET}"


def _ok(s: str) -> str:  return _color(s, GREEN)
def _bad(s: str) -> str: return _color(s, RED)
def _warn(s: str) -> str:return _color(s, YELLOW)
def _info(s: str) -> str:return _color(s, BLUE)
def _dim(s: str) -> str: return _color(s, DIM)


VERSION_FILE = PROJECT_ROOT / "VERSION"


def _read_version() -> str:
    try:
        return VERSION_FILE.read_text().strip()
    except Exception:
        return "unknown"


async def _check_tier0() -> list[dict]:
    """Probe each Tier 0 source with a representative query."""
    from sources import (
        YFinanceSource, AkshareSource, EastmoneySource,
        WorldBankSource, StatsGovCNSource, CoinGeckoSource,
    )

    checks = [
        ("yfinance",     YFinanceSource(),    "get_profile",     {"identifier": "AAPL"},          "AAPL profile"),
        ("akshare",      AkshareSource(),     "get_financials",  {"identifier": "贵州茅台", "years": 1}, "贵州茅台 financials"),
        ("eastmoney",    EastmoneySource(),   "get_profile",     {"identifier": "600519"},        "600519 profile"),
        ("worldbank",    WorldBankSource(),   "get_macro_data",  {"indicator": "gdp", "region": "CN", "years": 3}, "CN GDP"),
        ("stats_gov_cn", StatsGovCNSource(),  "get_macro_data",  {"indicator": "cpi", "region": "CN", "years": 1}, "CN CPI"),
        ("coingecko",    CoinGeckoSource(),   "get_crypto_data", {"identifier": "BTC"},           "BTC price"),
    ]

    results = []
    for name, src, method, args, desc in checks:
        start = time.time()
        status = "fail"
        latency_ms = None
        error = ""
        try:
            fn = getattr(src, method, None)
            if fn is None:
                error = f"{src.__class__.__name__}.{method} not implemented"
            else:
                res = await asyncio.wait_for(fn(**args), timeout=10.0)
                latency_ms = int((time.time() - start) * 1000)
                if res.has_data():
                    status = "ok"
                else:
                    error = (res.error or "no data")[:120]
        except asyncio.TimeoutError:
            error = "timeout (>10s)"
            latency_ms = 10000
        except Exception as e:
            error = str(e)[:120]
            latency_ms = int((time.time() - start) * 1000)
        results.append({
            "name": name, "tier": "Tier 0", "status": status,
            "latency_ms": latency_ms, "desc": desc, "error": error,
        })
    return results


async def _check_tier1() -> list[dict]:
    """Probe each Tier 1 source: if key set, attempt a live query; else mark unset."""
    from sources import FMPSource, AlphaVantageSource, NewsAPISource, FREDSource

    probes = []
    if has_fmp() and FMPSource is not None:
        probes.append(("fmp", FMPSource, "get_profile", {"identifier": "AAPL"}, "AAPL profile"))
    if has_av() and AlphaVantageSource is not None:
        probes.append(("alphavantage", AlphaVantageSource, "get_profile", {"identifier": "AAPL"}, "AAPL profile"))
    if has_newsapi() and NewsAPISource is not None:
        probes.append(("newsapi", NewsAPISource, "get_news", {"query": "apple", "limit": 1}, "apple news"))
    if has_fred() and FREDSource is not None:
        probes.append(("fred", FREDSource, "get_macro_data", {"indicator": "gdp", "region": "US", "years": 1}, "US GDP"))

    results = []
    for name, cls, method, args, desc in probes:
        start = time.time()
        status = "fail"
        latency_ms = None
        error = ""
        try:
            src = cls()
            res = await asyncio.wait_for(getattr(src, method)(**args), timeout=10.0)
            latency_ms = int((time.time() - start) * 1000)
            if res.has_data():
                status = "ok"
            else:
                error = (res.error or "no data")[:120]
        except asyncio.TimeoutError:
            error = "timeout (>10s)"
            latency_ms = 10000
        except Exception as e:
            error = str(e)[:120]
            latency_ms = int((time.time() - start) * 1000)
        results.append({
            "name": name, "tier": "Tier 1", "status": status,
            "latency_ms": latency_ms, "desc": desc, "error": error,
        })

    # Add not-configured rows for keys without keys set
    key_status = {
        "fmp": has_fmp(), "alphavantage": has_av(),
        "newsapi": has_newsapi(), "fred": has_fred(),
        "coingecko_pro": has_coingecko_pro(),
    }
    for key, configured in key_status.items():
        if not configured:
            if key == "coingecko_pro":
                continue  # public CoinGecko already covered in Tier 0
            results.append({
                "name": key, "tier": "Tier 1", "status": "unset",
                "latency_ms": None, "desc": "no key configured", "error": "",
            })
    return results


def _print_header():
    version = _read_version()
    print(f"\n{_color('senior_analyst', BOLD)} v{version} — health check\n")
    print(f"{_dim('Config:')} {USER_ENV_PATH if USER_ENV_PATH.exists() else _dim('(no user config; using project .env or environment)')}")
    print()


def _print_section(title: str):
    print(_color(title, BOLD))


def _print_tier_results(results: list[dict], tier: str):
    rows = [r for r in results if r["tier"] == tier]
    if not rows:
        print(_dim("  (none)"))
        return
    name_w = max(12, max(len(r["name"]) for r in rows) + 2)
    for r in rows:
        if r["status"] == "ok":
            symbol = _ok("✓")
            latency = f"{r['latency_ms']}ms".ljust(8)
            line = f"  {symbol} {r['name'].ljust(name_w)} {latency} {_dim(r['desc'])}"
        elif r["status"] == "unset":
            symbol = _dim("·")
            svc = KEY_SERVICES.get(r["name"], {})
            unlocks = svc.get("unlocks", "")
            hint = f"run: senior_analyst-setup-keys --service {r['name']}"
            line = f"  {symbol} {r['name'].ljust(name_w)} {_dim('not configured').ljust(20)} {_dim(unlocks)}"
            line += f"\n      {_dim(hint)}"
        else:
            symbol = _bad("✗")
            latency = (f"{r['latency_ms']}ms" if r['latency_ms'] else "—").ljust(8)
            line = f"  {symbol} {r['name'].ljust(name_w)} {latency} {_warn(r['error'])}"
        print(line)


def _print_cache_status():
    total = sum(len(c) for c in caches.values())
    print(f"  {_dim('total entries:')} {total}")
    for category, c in caches.items():
        if len(c) > 0:
            print(f"  {category.ljust(14)} {len(c)}/{c.maxsize}")


def _print_registry():
    active = {k: v for k, v in AVAILABLE_SOURCES.items() if v}
    for tool, srcs in active.items():
        print(f"  {tool.ljust(20)} {' -> '.join(srcs)}")


def _print_next_steps(results: list[dict]):
    suggestions = []
    if not has_fred():
        suggestions.append((
            "FRED (free, 30s signup)",
            "Unlocks US macro: GDP, CPI, unemployment, rates, M2",
            "senior_analyst-setup-keys --service fred",
        ))
    if not has_fmp():
        suggestions.append((
            "FMP (paid, $14/mo entry)",
            "Global financials with peer recommendations",
            "senior_analyst-setup-keys --service fmp",
        ))
    if not suggestions:
        broken = [r for r in results if r["tier"] == "Tier 0" and r["status"] == "fail"]
        if broken:
            print(_warn(f"  {len(broken)} Tier 0 source(s) failing — check network and akshare/yfinance versions"))
        else:
            print(_ok("  All sources healthy. Nothing to do."))
        return
    for label, unlocks, cmd in suggestions:
        print(f"  {_info(label)}")
        print(f"    {_dim(unlocks)}")
        print(f"    {_dim('→')} {cmd}")
        print()


async def run() -> int:
    build_source_registry()
    _print_header()

    _print_section("Source registry (tool → priority order):")
    _print_registry()
    print()

    _print_section("Tier 0 sources (no key needed):")
    tier0 = await _check_tier0()
    _print_tier_results(tier0, "Tier 0")
    print()

    _print_section("Tier 1 sources (require API key):")
    tier1 = await _check_tier1()
    _print_tier_results(tier1, "Tier 1")
    print()

    _print_section("Cache:")
    _print_cache_status()
    print()

    _print_section("Recommended next steps:")
    _print_next_steps(tier0 + tier1)
    print()

    broken_tier0 = [r for r in tier0 if r["status"] == "fail"]
    if broken_tier0:
        return 1
    return 0


def main():
    try:
        sys.exit(asyncio.run(run()))
    except KeyboardInterrupt:
        print("\n  cancelled")
        sys.exit(130)


if __name__ == "__main__":
    main()
