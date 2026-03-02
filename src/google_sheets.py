"""
Google Sheets 写入模块。
使用服务账号认证，无需交互式登录。
"""
import json
import base64
import os
from typing import List, Dict, Any

from config import GOOGLE_SHEETS_ID, GOOGLE_CREDENTIALS_JSON


def is_configured() -> bool:
    """检查 Google Sheets 是否已配置。"""
    return bool(GOOGLE_SHEETS_ID and GOOGLE_CREDENTIALS_JSON)


def _get_client():
    """获取 gspread 客户端（惰性导入）。"""
    import gspread
    from google.oauth2.service_account import Credentials

    # 从 base64 环境变量解码凭证
    creds_json = base64.b64decode(GOOGLE_CREDENTIALS_JSON).decode("utf-8")
    creds_dict = json.loads(creds_json)

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(credentials)


def sync_to_sheets(rows: List[Dict[str, Any]]):
    """
    将数据写入 Google Sheets。
    - Sheet1 "Latest": 最新快照（覆盖写入）
    - Sheet2 "History": 追加历史数据（增量写入）
    """
    if not is_configured():
        print("  Google Sheets not configured, skipping.")
        return

    print("  Connecting to Google Sheets...")
    gc = _get_client()
    spreadsheet = gc.open_by_key(GOOGLE_SHEETS_ID)

    # ---- Sheet "Latest": 最新一天的数据（覆盖） ----
    latest_date = max(r["date"] for r in rows) if rows else ""
    latest_rows = [r for r in rows if r["date"] == latest_date]

    if latest_rows:
        _write_sheet(spreadsheet, "Latest", latest_rows, clear=True)
        print(f"  Updated 'Latest' sheet: {len(latest_rows)} rows ({latest_date})")

    # ---- Sheet "History": 全部数据（覆盖写入，因为含衍生指标需重新计算） ----
    if rows:
        _write_sheet(spreadsheet, "History", rows, clear=True)
        print(f"  Updated 'History' sheet: {len(rows)} rows")


def _write_sheet(spreadsheet, sheet_name: str, rows: List[Dict[str, Any]], clear: bool = False):
    """写入指定 sheet。"""
    # 获取或创建 sheet
    try:
        ws = spreadsheet.worksheet(sheet_name)
    except Exception:
        ws = spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=20)

    if clear:
        ws.clear()

    if not rows:
        return

    # 定义列顺序
    columns = [
        "date", "project", "blockchain", "volume",
        "market_share_pct", "growth_rate_pct",
        "volume_7d", "volume_30d", "change_1d", "change_7d", "change_1m",
        "unique_id",
    ]
    # 只输出实际存在的列
    columns = [c for c in columns if any(r.get(c) is not None for r in rows)]

    # 表头
    header = columns
    data = [header]

    # 数据行
    for row in sorted(rows, key=lambda r: (r["date"], r["project"])):
        data.append([_format_cell(row.get(c)) for c in columns])

    ws.update(range_name="A1", values=data)


def _format_cell(val) -> Any:
    """格式化单元格值。"""
    if val is None:
        return ""
    if isinstance(val, float):
        return round(val, 2)
    return val
