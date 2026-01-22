# app/services/scheduler.py
from datetime import datetime
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from .. import db
from ..models import Target, Snapshot, Event
from .fetcher import fetch_stats

_scheduler: BackgroundScheduler | None = None


def start_scheduler(app):
    """Start APScheduler once. Runs hourly at minute 0 in TIMEZONE."""
    global _scheduler
    if _scheduler:
        return _scheduler

    tz_name = app.config.get("TIMEZONE", "Asia/Bangkok")
    _scheduler = BackgroundScheduler(timezone=tz_name)

    _scheduler.add_job(
        func=lambda: poll_all(app),
        trigger=CronTrigger(minute=0),
        id="poll_all_targets",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=15 * 60,
    )
    _scheduler.start()
    return _scheduler


def poll_all(app):
    """Poll all enabled targets for current hour bucket."""
    tz = ZoneInfo(app.config.get("TIMEZONE", "Asia/Bangkok"))
    now = datetime.now(tz)
    hour_bucket = _floor_hour(now)

    with app.app_context():
        targets = Target.query.filter_by(enabled=True).all()
        for t in targets:
            _poll_one_target(t.id, now, hour_bucket)


def poll_target(app, target_id: int, force: bool = True):
    """
    Poll a single target immediately and store snapshot.
    Use after Add Target to get data right away.
    """
    tz = ZoneInfo(app.config.get("TIMEZONE", "Asia/Bangkok"))
    now = datetime.now(tz)
    hour_bucket = _floor_hour(now)

    with app.app_context():
        t = Target.query.get(target_id)
        if not t:
            return None
        if (not t.enabled) and (not force):
            return None
        return _poll_one_target(t.id, now, hour_bucket)


def _poll_one_target(target_id: int, polled_at_tz: datetime, hour_bucket_tz: datetime):
    t = Target.query.get(target_id)
    if not t or not t.enabled:
        return None

    # Fetch (ALWAYS returns dict with ok/http_status/latency_ms/.../raw_json/reason)
    result = fetch_stats(t.base_url, t.stats_path, timeout_s=8, retries=1)

    # Store as naive datetimes in SQLite
    polled_at = polled_at_tz.replace(tzinfo=None)
    hour_bucket = hour_bucket_tz.replace(tzinfo=None)

    # Upsert snapshot for (target_id, hour_bucket)
    snap = Snapshot.query.filter_by(target_id=t.id, hour_bucket=hour_bucket).first()
    if snap is None:
        snap = Snapshot(target_id=t.id, hour_bucket=hour_bucket)
        db.session.add(snap)

    snap.polled_at = polled_at
    snap.ok = bool(result.get("ok"))
    snap.http_status = result.get("http_status")
    snap.latency_ms = result.get("latency_ms")
    snap.cpu_percent = result.get("cpu_percent")
    snap.mem_percent = result.get("mem_percent")
    snap.disk_percent = result.get("disk_percent")
    snap.swap_percent = result.get("swap_percent")
    snap.raw_json = result.get("raw_json")

    db.session.commit()

    # Update events (DOWN periods only)
    _update_events(
        target_id=t.id,
        hour_bucket=hour_bucket,
        is_ok=snap.ok,
        reason=result.get("reason"),
        http_status=snap.http_status,
    )

    return snap


def _update_events(target_id: int, hour_bucket: datetime, is_ok: bool, reason: str | None, http_status: int | None):
    prev = (
        Snapshot.query
        .filter(Snapshot.target_id == target_id, Snapshot.hour_bucket < hour_bucket)
        .order_by(Snapshot.hour_bucket.desc())
        .first()
    )
    if not prev:
        return  # don't create events at first data point

    # UP -> DOWN : open new event
    if prev.ok and (not is_ok):
        ev = Event(
            target_id=target_id,
            state="down",
            started_at=hour_bucket,
            ended_at=None,
            reason=reason,
            http_status=http_status,
        )
        db.session.add(ev)
        db.session.commit()
        return

    # DOWN -> UP : close latest open DOWN event
    if (not prev.ok) and is_ok:
        open_ev = (
            Event.query
            .filter_by(target_id=target_id, state="down", ended_at=None)
            .order_by(Event.started_at.desc())
            .first()
        )
        if open_ev:
            open_ev.ended_at = hour_bucket
            db.session.commit()


def _floor_hour(dt: datetime) -> datetime:
    return dt.replace(minute=0, second=0, microsecond=0)
