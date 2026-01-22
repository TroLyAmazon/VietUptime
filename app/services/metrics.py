from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from ..models import Snapshot


def get_latest_snapshot(target_id: int):
    return (
        Snapshot.query
        .filter_by(target_id=target_id)
        .order_by(Snapshot.hour_bucket.desc())
        .first()
    )


def latency_series(target_id: int, hours: int = 48, tz_name: str = "Asia/Bangkok"):
    """
    Return JSON-ready payload for Chart.js:
    { labels: [...], values: [...] }
    Only points that exist in DB are included.
    """
    tz = ZoneInfo(tz_name)
    end = datetime.now(tz).replace(minute=0, second=0, microsecond=0)
    start = end - timedelta(hours=hours)

    start_n = start.replace(tzinfo=None)
    end_n = end.replace(tzinfo=None)

    rows = (
        Snapshot.query
        .filter(
            Snapshot.target_id == target_id,
            Snapshot.hour_bucket >= start_n,
            Snapshot.hour_bucket < end_n,
        )
        .order_by(Snapshot.hour_bucket.asc())
        .all()
    )

    labels = []
    values = []
    for s in rows:
        # assume stored as naive => display as local time string
        labels.append(s.hour_bucket.strftime("%m-%d %H:%M"))
        values.append(s.latency_ms if s.latency_ms is not None else None)

    return {"labels": labels, "values": values}


def _classify(pct: float) -> str:
    # <10 đỏ, 10-80 vàng, >80 xanh
    if pct < 10:
        return "bad"
    if pct < 80:
        return "warn"
    return "ok"


def uptime_percent(target_id: int, hours: int, tz_name: str):
    """
    Tính uptime chỉ dựa trên samples có trong DB.
    Nếu không có snapshot trong khoảng => None (UI hiển thị —).
    """
    tz = ZoneInfo(tz_name)
    end = datetime.now(tz).replace(minute=0, second=0, microsecond=0)
    start = end - timedelta(hours=hours)

    start_n = start.replace(tzinfo=None)
    end_n = end.replace(tzinfo=None)

    rows = (
        Snapshot.query
        .with_entities(Snapshot.ok)
        .filter(
            Snapshot.target_id == target_id,
            Snapshot.hour_bucket >= start_n,
            Snapshot.hour_bucket < end_n,
        )
        .all()
    )

    total = len(rows)
    if total == 0:
        return None

    ok = sum(1 for (v,) in rows if v)
    return round(ok * 100.0 / total, 1)


def bars_90d(target_id: int, tz_name: str):
    """
    90 days daily bars:
    - no data => cls='unk', pct=None (xám)
    - data => pct=ok/total*100 + cls theo ngưỡng
    """
    tz = ZoneInfo(tz_name)
    today = datetime.now(tz).date()
    out = []

    for i in range(89, -1, -1):
        d = today - timedelta(days=i)
        day_start = datetime(d.year, d.month, d.day, 0, 0, 0, tzinfo=tz)
        day_end = day_start + timedelta(days=1)

        s = day_start.replace(tzinfo=None)
        e = day_end.replace(tzinfo=None)

        rows = (
            Snapshot.query
            .with_entities(Snapshot.ok)
            .filter(
                Snapshot.target_id == target_id,
                Snapshot.hour_bucket >= s,
                Snapshot.hour_bucket < e,
            )
            .all()
        )

        total = len(rows)
        if total == 0:
            out.append({"date": d.isoformat(), "pct": None, "cls": "unk"})
            continue

        ok = sum(1 for (v,) in rows if v)
        pct = ok * 100.0 / total
        out.append({"date": d.isoformat(), "pct": round(pct, 1), "cls": _classify(pct)})

    return out
