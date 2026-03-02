"""
Perp DEX 竞对分析 - ETL 主流程。

数据源: DefiLlama (免费)
输出: data/perp_data.json (GitHub Pages) + Google Sheets (可选)

Usage:
    cd src && python main.py                    # 增量更新（最新快照）
    cd src && python main.py --history          # 首次运行：拉取全部历史
"""
import sys
import os
import json
import argparse
import traceback
from datetime import datetime

from config import DATA_DIR, DATA_FILE
from defillama_client import DefiLlamaClient
from transform import enrich_rows
from google_sheets import sync_to_sheets, is_configured as sheets_configured


def load_existing_data() -> list:
    """从本地 JSON 加载已有数据。"""
    if not os.path.isfile(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(rows: list):
    """保存数据到本地 JSON。"""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)


def merge_data(existing: list, new_rows: list) -> list:
    """合并新旧数据，按 unique_id 去重（新数据覆盖旧数据）。"""
    by_id = {}
    for row in existing:
        uid = row.get("unique_id")
        if uid:
            by_id[uid] = row
    for row in new_rows:
        uid = row.get("unique_id")
        if uid:
            by_id[uid] = row
    merged = list(by_id.values())
    merged.sort(key=lambda r: (r["date"], r["project"]))
    return merged


def run_snapshot():
    """增量模式：获取最新快照数据。"""
    print("\n[1/3] EXTRACT: Fetching latest snapshot from DefiLlama...")
    client = DefiLlamaClient()
    new_rows = client.fetch_overview()
    if not new_rows:
        print("  No data returned. Exiting.")
        return

    print(f"\n[2/3] TRANSFORM: Merging + calculating metrics...")
    # 先给新数据生成 unique_id，再合并
    from transform import generate_unique_id
    for row in new_rows:
        row["unique_id"] = generate_unique_id(row["date"], row["project"])

    existing = load_existing_data()
    all_rows = merge_data(existing, new_rows)
    all_rows = enrich_rows(all_rows)
    new_count = len(all_rows) - len(existing)
    print(f"  Total: {len(all_rows)} rows (+{max(0, new_count)} new)")

    print(f"\n[3/3] LOAD: Saving outputs...")
    save_data(all_rows)
    print(f"  Saved {len(all_rows)} rows to {DATA_FILE}")

    if sheets_configured():
        sync_to_sheets(all_rows)
    else:
        print("  Google Sheets not configured, skipping.")

    return all_rows


def run_history():
    """历史模式：获取所有协议的完整历史数据。"""
    print("\n[1/3] EXTRACT: Fetching full history from DefiLlama...")
    print("  (This may take ~1 minute due to rate limiting)")
    client = DefiLlamaClient()
    new_rows = client.fetch_all_history()
    if not new_rows:
        print("  No data returned. Exiting.")
        return

    print(f"\n[2/3] TRANSFORM: Merging + calculating metrics...")
    from transform import generate_unique_id
    for row in new_rows:
        row["unique_id"] = generate_unique_id(row["date"], row["project"])

    existing = load_existing_data()
    all_rows = merge_data(existing, new_rows)
    all_rows = enrich_rows(all_rows)
    print(f"  Total: {len(all_rows)} rows")

    print(f"\n[3/3] LOAD: Saving outputs...")
    save_data(all_rows)
    print(f"  Saved {len(all_rows)} rows to {DATA_FILE}")

    if sheets_configured():
        sync_to_sheets(all_rows)
    else:
        print("  Google Sheets not configured, skipping.")

    return all_rows


def main():
    parser = argparse.ArgumentParser(description="Perp DEX Dashboard Sync")
    parser.add_argument(
        "--history", action="store_true",
        help="Fetch full history (initial pull, ~1 min)"
    )
    args = parser.parse_args()

    print(f"{'=' * 50}")
    print(f"Perp DEX Dashboard Sync - {datetime.now().isoformat()}")
    mode = "HISTORY" if args.history else "SNAPSHOT"
    print(f"Mode: {mode}")
    print(f"{'=' * 50}")

    try:
        if args.history:
            rows = run_history()
        else:
            rows = run_snapshot()

        if rows:
            print(f"\n{'=' * 50}")
            print("SYNC COMPLETE")
            print(f"  Data file: {DATA_FILE}")
            print(f"  Total records: {len(rows)}")
            print(f"  Google Sheets: {'enabled' if sheets_configured() else 'not configured'}")
            print(f"{'=' * 50}")

    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(130)
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
