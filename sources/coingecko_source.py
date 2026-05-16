"""CoinGecko data source — Tier 0 (no API key required for public endpoints).

Provides cryptocurrency market data: price, market cap, volume, supply.
Optional Pro key (SENIOR_ANALYST_COINGECKO_KEY) unlocks higher rate limits.
Docs: https://www.coingecko.com/en/api/documentation
"""

import logging
from typing import Any

import httpx

from .base import BaseSource, DataResult, CryptoAssetData
from .config import COINGECKO_PRO_KEY, cache_key, get_cache

logger = logging.getLogger(__name__)

PUBLIC_BASE = "https://api.coingecko.com/api/v3"
PRO_BASE = "https://pro-api.coingecko.com/api/v3"


SYMBOL_TO_ID = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "USDT": "tether",
    "USDC": "usd-coin",
    "BNB": "binancecoin",
    "SOL": "solana",
    "XRP": "ripple",
    "ADA": "cardano",
    "DOGE": "dogecoin",
    "TRX": "tron",
    "AVAX": "avalanche-2",
    "DOT": "polkadot",
    "MATIC": "matic-network",
    "LINK": "chainlink",
    "TON": "the-open-network",
    "SHIB": "shiba-inu",
    "LTC": "litecoin",
    "BCH": "bitcoin-cash",
    "ATOM": "cosmos",
    "UNI": "uniswap",
    "ETC": "ethereum-classic",
    "XLM": "stellar",
    "OKB": "okb",
    "NEAR": "near",
    "APT": "aptos",
    "FIL": "filecoin",
    "ARB": "arbitrum",
    "OP": "optimism",
    "VET": "vechain",
    "ICP": "internet-computer",
    "HBAR": "hedera-hashgraph",
    "MKR": "maker",
    "SUI": "sui",
    "STX": "blockstack",
    "TAO": "bittensor",
    "INJ": "injective-protocol",
    "AAVE": "aave",
    "RUNE": "thorchain",
    "GRT": "the-graph",
    "RNDR": "render-token",
    "WLD": "worldcoin-wld",
    "SEI": "sei-network",
    "TIA": "celestia",
    "FET": "fetch-ai",
    "IMX": "immutable-x",
    "FTM": "fantom",
    "ALGO": "algorand",
    "FLOW": "flow",
    "XMR": "monero",
    "PEPE": "pepe",
}


def _resolve_id(identifier: str) -> str:
    s = identifier.strip()
    if s.upper() in SYMBOL_TO_ID:
        return SYMBOL_TO_ID[s.upper()]
    # If it's lowercase-with-dashes, assume it's already a coingecko id
    return s.lower().replace(" ", "-")


class CoinGeckoSource(BaseSource):
    name = "coingecko"

    def __init__(self):
        self._has_pro = bool(COINGECKO_PRO_KEY)
        self._base = PRO_BASE if self._has_pro else PUBLIC_BASE

    def _headers(self) -> dict:
        if self._has_pro:
            return {"x-cg-pro-api-key": COINGECKO_PRO_KEY}
        return {}

    async def _get(self, path: str, params: dict | None = None, timeout: float = 5.0) -> Any:
        try:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True, headers=self._headers()) as client:
                resp = await client.get(f"{self._base}/{path}", params=params or {})
                resp.raise_for_status()
                return resp.json()
        except httpx.HTTPStatusError as e:
            logger.warning(f"CoinGecko HTTP {e.response.status_code} for {path}")
            return None
        except Exception as e:
            logger.warning(f"CoinGecko request failed ({path}): {e}")
            return None

    async def get_crypto_data(
        self, identifier: str, metrics: str = "price,marketcap,volume"
    ) -> DataResult:
        coin_id = _resolve_id(identifier)
        ck = cache_key("crypto", coin_id, metrics)
        cache = get_cache("crypto")
        if ck in cache:
            return cache[ck]

        # Use /coins/{id} for full data; fallback to /simple/price for price-only
        data = await self._get(
            f"coins/{coin_id}",
            params={"localization": "false", "tickers": "false", "community_data": "false", "developer_data": "false"},
        )
        if data is None:
            # Try simple price as last resort
            simple = await self._get(
                "simple/price",
                params={
                    "ids": coin_id,
                    "vs_currencies": "usd",
                    "include_market_cap": "true",
                    "include_24hr_vol": "true",
                    "include_24hr_change": "true",
                },
            )
            if simple and coin_id in simple:
                asset = CryptoAssetData(
                    symbol=identifier.upper(),
                    name=identifier,
                    coingecko_id=coin_id,
                    price_usd=simple[coin_id].get("usd"),
                    market_cap_usd=simple[coin_id].get("usd_market_cap"),
                    volume_24h_usd=simple[coin_id].get("usd_24h_vol"),
                    price_change_24h_pct=simple[coin_id].get("usd_24h_change"),
                )
                result = DataResult(success=True, data=asset, source="coingecko")
                cache[ck] = result
                return result
            return DataResult(success=False, error=f"CoinGecko returned no data for {identifier}")

        market = data.get("market_data") or {}
        asset = CryptoAssetData(
            symbol=(data.get("symbol") or identifier).upper(),
            name=data.get("name", identifier),
            coingecko_id=data.get("id", coin_id),
            price_usd=_nested(market, "current_price", "usd"),
            market_cap_usd=_nested(market, "market_cap", "usd"),
            volume_24h_usd=_nested(market, "total_volume", "usd"),
            price_change_24h_pct=market.get("price_change_percentage_24h"),
            circulating_supply=market.get("circulating_supply"),
            max_supply=market.get("max_supply"),
            rank=data.get("market_cap_rank"),
        )

        result = DataResult(success=True, data=asset, source="coingecko")
        cache[ck] = result
        return result


def _nested(d: dict, *keys):
    cur = d
    for k in keys:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(k)
        if cur is None:
            return None
    return cur
