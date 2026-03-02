"""
数据转换模块：生成唯一 ID，计算衍生指标。
"""
from typing import List, Dict, Any, Optional


def generate_unique_id(date: str, project: str) -> str:
    """生成去重主键: YYYY-MM-DD_protocol_name"""
    return f"{date}_{project.lower().replace(' ', '_')}"


def calculate_capital_efficiency(
    volume: Optional[float], open_interest: Optional[float]
) -> Optional[float]:
    """资金效率 = Volume / Open Interest"""
    if volume is None or open_interest is None or open_interest == 0:
        return None
    return round(volume / open_interest, 4)


def calculate_market_share(
    rows: List[Dict[str, Any]], metric: str = "volume"
) -> List[Dict[str, Any]]:
    """计算每个协议在当日的市场份额百分比。"""
    daily_totals: Dict[str, float] = {}
    for row in rows:
        d = row["date"]
        val = row.get(metric)
        if val is not None:
            daily_totals[d] = daily_totals.get(d, 0) + val

    for row in rows:
        d = row["date"]
        val = row.get(metric)
        total = daily_totals.get(d, 0)
        if val is not None and total > 0:
            row["market_share_pct"] = round(val / total * 100, 2)
        else:
            row["market_share_pct"] = None

    return rows


def calculate_growth_rate(
    rows: List[Dict[str, Any]], metric: str = "volume"
) -> List[Dict[str, Any]]:
    """计算每个协议的日环比增长率。"""
    by_project: Dict[str, List[Dict[str, Any]]] = {}
    for row in rows:
        by_project.setdefault(row["project"], []).append(row)

    for prows in by_project.values():
        prows.sort(key=lambda r: r["date"])
        for i, row in enumerate(prows):
            if i == 0:
                row["growth_rate_pct"] = None
                continue
            prev_val = prows[i - 1].get(metric)
            curr_val = row.get(metric)
            if prev_val and curr_val and prev_val > 0:
                row["growth_rate_pct"] = round(
                    (curr_val - prev_val) / prev_val * 100, 2
                )
            else:
                row["growth_rate_pct"] = None

    return rows


def enrich_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    主入口：为每行添加衍生字段。
    - unique_id
    - market_share_pct
    - growth_rate_pct
    """
    for row in rows:
        row["unique_id"] = generate_unique_id(row["date"], row["project"])

    rows = calculate_market_share(rows, metric="volume")
    rows = calculate_growth_rate(rows, metric="volume")
    return rows
