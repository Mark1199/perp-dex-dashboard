"""
DefiLlama API 客户端。
免费、无需 API Key，覆盖全部 9 个目标协议。
"""
import time
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from config import (
    DEFILLAMA_BASE_URL, PROTOCOL_SLUGS,
    MAX_RETRIES, RETRY_DELAY_SECONDS, API_CALL_INTERVAL,
)


class DefiLlamaClient:
    """DefiLlama Derivatives API 封装"""

    def __init__(self):
        self.base_url = DEFILLAMA_BASE_URL

    def _get_with_retry(self, url: str, params: dict = None) -> dict:
        """带重试和限流处理的 GET 请求。"""
        for attempt in range(MAX_RETRIES):
            try:
                resp = requests.get(url, params=params, timeout=30)
                if resp.status_code == 429:
                    wait = 30 * (attempt + 1)  # 30s, 60s, 90s
                    print(f"    Rate limited, waiting {wait}s...")
                    time.sleep(wait)
                    continue
                resp.raise_for_status()
                return resp.json()
            except requests.exceptions.RequestException as e:
                if attempt == MAX_RETRIES - 1:
                    raise
                wait = RETRY_DELAY_SECONDS * (2 ** attempt)
                print(f"    Request failed ({e}), retrying in {wait}s...")
                time.sleep(wait)
        raise RuntimeError(f"All retries exhausted for {url}")

    def fetch_overview(self) -> List[Dict[str, Any]]:
        """
        获取所有协议的最新快照（24h volume 等）。
        单次调用，返回当日数据。

        GET /overview/derivatives?excludeTotalDataChart=true&excludeTotalDataChartBreakdown=true
        """
        print("  Fetching derivatives overview...")
        url = f"{self.base_url}/overview/derivatives"
        data = self._get_with_retry(url, params={
            "excludeTotalDataChart": "true",
            "excludeTotalDataChartBreakdown": "true",
        })

        protocols = data.get("protocols", [])
        target_modules = set(PROTOCOL_SLUGS.values())
        today = datetime.utcnow().strftime("%Y-%m-%d")

        rows = []
        for p in protocols:
            module = p.get("module", "")
            if module not in target_modules:
                continue

            # 反查协议名
            name = next(
                (k for k, v in PROTOCOL_SLUGS.items() if v == module),
                p.get("name", module)
            )

            rows.append({
                "date": today,
                "project": name,
                "blockchain": (p.get("chains") or ["unknown"])[0],
                "volume": p.get("total24h"),
                "volume_7d": p.get("total7d"),
                "volume_30d": p.get("total30d"),
                "change_1d": p.get("change_1d"),
                "change_7d": p.get("change_7d"),
                "change_1m": p.get("change_1m"),
            })

        print(f"  Found {len(rows)}/{len(PROTOCOL_SLUGS)} target protocols")
        return rows

    def fetch_protocol_history(
        self, name: str, slug: str
    ) -> List[Dict[str, Any]]:
        """
        获取单个协议的完整历史每日 volume。

        GET /summary/derivatives/{slug}?dataType=dailyVolume
        """
        url = f"{self.base_url}/summary/derivatives/{slug}"
        data = self._get_with_retry(url, params={"dataType": "dailyVolume"})

        chart = data.get("totalDataChart", [])
        chain = (data.get("chains") or ["unknown"])[0]

        rows = []
        for ts, volume in chart:
            rows.append({
                "date": datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d"),
                "project": name,
                "blockchain": chain,
                "volume": volume,
            })

        return rows

    def fetch_all_history(self) -> List[Dict[str, Any]]:
        """
        获取所有目标协议的完整历史数据。
        每个协议间隔 API_CALL_INTERVAL 秒以避免限流。
        """
        all_rows = []
        total = len(PROTOCOL_SLUGS)

        for i, (name, slug) in enumerate(PROTOCOL_SLUGS.items(), 1):
            print(f"  [{i}/{total}] Fetching history: {name} ({slug})...")
            try:
                rows = self.fetch_protocol_history(name, slug)
                all_rows.extend(rows)
                print(f"    Got {len(rows)} days of data")
            except Exception as e:
                print(f"    FAILED: {e}")

            if i < total:
                time.sleep(API_CALL_INTERVAL)

        print(f"  Total: {len(all_rows)} historical data points")
        return all_rows
