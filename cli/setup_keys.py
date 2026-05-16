"""senior_analyst setup-keys — interactive API key configuration.

Stores keys in ~/.config/senior_analyst/.env (chmod 600).
Existing keys in process environment or project .env are NOT overwritten;
user .env takes precedence on next process start.

Usage:
    python -m cli.setup_keys                # interactive menu
    python -m cli.setup_keys --service fred # configure one service
    python -m cli.setup_keys --list         # show current key status only
"""

import argparse
import asyncio
import logging
import os
import stat
import sys
from pathlib import Path

logging.basicConfig(level=logging.ERROR)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from sources.config import KEY_SERVICES, USER_ENV_PATH, USER_CONFIG_DIR

GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"


def _color(s: str, c: str) -> str:
    if not sys.stdout.isatty():
        return s
    return f"{c}{s}{RESET}"


def _read_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    out = {}
    try:
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip().strip('"').strip("'")
    except Exception:
        pass
    return out


def _write_env_file(path: Path, kv: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# senior_analyst — user API keys", "# Stored by senior_analyst-setup-keys; chmod 600", ""]
    for k in sorted(kv.keys()):
        v = kv[k]
        lines.append(f'{k}="{v}"')
    path.write_text("\n".join(lines) + "\n")
    try:
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
    except Exception:
        pass


async def _validate_key(service: str, key: str) -> tuple[bool, str]:
    """Live-test a key. Returns (ok, message)."""
    import httpx
    try:
        if service == "fred":
            async with httpx.AsyncClient(timeout=8.0) as client:
                r = await client.get(
                    "https://api.stlouisfed.org/fred/series/observations",
                    params={"series_id": "GDP", "api_key": key, "file_type": "json", "limit": 1},
                )
                if r.status_code == 200 and "observations" in r.json():
                    return True, "✓ key valid (test query: GDP)"
                return False, f"✗ FRED rejected key (HTTP {r.status_code})"

        elif service == "fmp":
            async with httpx.AsyncClient(timeout=8.0) as client:
                r = await client.get(
                    f"https://financialmodelingprep.com/api/v3/profile/AAPL?apikey={key}",
                )
                if r.status_code == 200 and isinstance(r.json(), list) and len(r.json()) > 0:
                    return True, "✓ key valid (test query: AAPL profile)"
                return False, f"✗ FMP rejected key (HTTP {r.status_code})"

        elif service == "av":
            async with httpx.AsyncClient(timeout=8.0) as client:
                r = await client.get(
                    "https://www.alphavantage.co/query",
                    params={"function": "OVERVIEW", "symbol": "AAPL", "apikey": key},
                )
                data = r.json() if r.status_code == 200 else {}
                if isinstance(data, dict) and data.get("Symbol") == "AAPL":
                    return True, "✓ key valid (test query: AAPL overview)"
                if "Note" in data:
                    return False, f"✗ rate-limited or invalid: {data['Note'][:80]}"
                return False, "✗ Alpha Vantage rejected key or returned no data"

        elif service == "newsapi":
            async with httpx.AsyncClient(timeout=8.0) as client:
                r = await client.get(
                    "https://newsapi.org/v2/everything",
                    params={"q": "apple", "pageSize": 1, "apiKey": key},
                )
                if r.status_code == 200 and r.json().get("status") == "ok":
                    return True, "✓ key valid (test query: apple)"
                return False, f"✗ NewsAPI rejected key (HTTP {r.status_code})"

        elif service == "coingecko":
            async with httpx.AsyncClient(timeout=8.0, headers={"x-cg-pro-api-key": key}) as client:
                r = await client.get("https://pro-api.coingecko.com/api/v3/ping")
                if r.status_code == 200:
                    return True, "✓ key valid (test query: ping)"
                return False, f"✗ CoinGecko Pro rejected key (HTTP {r.status_code})"

        return False, f"unknown service: {service}"
    except Exception as e:
        return False, f"✗ network error: {str(e)[:120]}"


def _print_status():
    env = _read_env_file(USER_ENV_PATH)
    proc_env = os.environ
    print(_color("\nCurrent key status:\n", BOLD))
    for sid, svc in KEY_SERVICES.items():
        var = svc["env_var"]
        in_user_env = var in env
        in_proc = var in proc_env and proc_env[var]
        if in_user_env:
            mark = _color("✓", GREEN) + " set (user .env)"
        elif in_proc:
            mark = _color("✓", GREEN) + " set (process env)"
        else:
            mark = _color("·", DIM) + " not set"
        tier_label = svc["tier"]
        print(f"  {sid.ljust(12)} {mark.ljust(35)} {_color(tier_label, DIM)}")
        print(f"    {_color(svc['unlocks'], DIM)}")
    print()


async def _configure_one(service: str) -> bool:
    if service not in KEY_SERVICES:
        print(_color(f"unknown service: {service}", RED))
        print(f"available: {', '.join(KEY_SERVICES.keys())}")
        return False

    svc = KEY_SERVICES[service]
    print(_color(f"\n{svc['label']}", BOLD))
    print(f"  Tier:      {svc['tier']}")
    print(f"  Unlocks:   {svc['unlocks']}")
    print(f"  Free tier: {svc['free_tier_note']}")
    print(f"  Sign up:   {_color(svc['signup_url'], DIM)}")
    print()

    try:
        key = input(f"Paste your {svc['label']} API key (or blank to cancel): ").strip()
    except EOFError:
        return False
    if not key:
        print("  cancelled")
        return False

    print("  validating...", end=" ", flush=True)
    ok, msg = await _validate_key(service, key)
    print(msg)
    if not ok:
        try:
            confirm = input("  save anyway? [y/N]: ").strip().lower()
        except EOFError:
            confirm = "n"
        if confirm not in ("y", "yes"):
            print("  not saved")
            return False

    env = _read_env_file(USER_ENV_PATH)
    env[svc["env_var"]] = key
    _write_env_file(USER_ENV_PATH, env)
    print(f"  saved to {USER_ENV_PATH} (chmod 600)")
    print(_color("  Restart Claude Code (or your MCP host) for changes to take effect.", YELLOW))
    return True


async def _interactive_menu():
    print(_color("\nsenior_analyst setup-keys", BOLD))
    print()
    services_list = list(KEY_SERVICES.items())
    for i, (sid, svc) in enumerate(services_list, 1):
        print(f"  {i}) {svc['label']:<22} {_color(svc['tier'], DIM)}  {_color(svc['unlocks'], DIM)}")
    print(f"  s) show current key status")
    print(f"  q) quit")
    print()

    while True:
        try:
            choice = input("choice: ").strip().lower()
        except EOFError:
            return
        if choice in ("q", "quit", "exit", ""):
            return
        if choice == "s":
            _print_status()
            continue
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(services_list):
                sid = services_list[idx][0]
                await _configure_one(sid)
                continue
        if choice in KEY_SERVICES:
            await _configure_one(choice)
            continue
        print(_color("  unknown choice", RED))


async def run(args: argparse.Namespace) -> int:
    USER_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if args.list:
        _print_status()
        return 0
    if args.service:
        ok = await _configure_one(args.service)
        return 0 if ok else 1
    await _interactive_menu()
    return 0


def main():
    parser = argparse.ArgumentParser(description="Configure senior_analyst API keys.")
    parser.add_argument("--service", help="configure one service (fmp/av/newsapi/fred/coingecko)")
    parser.add_argument("--list", action="store_true", help="show current key status and exit")
    args = parser.parse_args()
    try:
        sys.exit(asyncio.run(run(args)))
    except KeyboardInterrupt:
        print("\n  cancelled")
        sys.exit(130)


if __name__ == "__main__":
    main()
