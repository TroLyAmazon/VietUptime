from flask import Blueprint, current_app, render_template, jsonify, abort
from urllib.parse import urlparse

from ..models import Target, Event
from ..services import metrics

bp = Blueprint("public", __name__)


def _host_only(url: str) -> str:
    p = urlparse(url or "")
    host = p.netloc or (url or "")
    host = host.replace("https://", "").replace("http://", "")
    return host.rstrip("/")


@bp.get("/")
def index():
    tz = current_app.config["TIMEZONE"]
    targets = Target.query.order_by(Target.id.asc()).all()

    cards = []
    for t in targets:
        last = metrics.get_latest_snapshot(t.id)

        cards.append({
            "target": t,
            "host": _host_only(t.base_url),
            "clickable": bool(getattr(t, "public_click", True)),
            "href": t.base_url,

            "last": last,
            "uptime_24h": metrics.uptime_percent(t.id, 24, tz),
            "uptime_7d": metrics.uptime_percent(t.id, 24 * 7, tz),
            "uptime_30d": metrics.uptime_percent(t.id, 24 * 30, tz),
            "uptime_90d": metrics.uptime_percent(t.id, 24 * 90, tz),
            "bars_90d": metrics.bars_90d(t.id, tz),
        })

    events = (
        Event.query
        .order_by(Event.started_at.desc())
        .limit(20)
        .all()
    )

    enabled_targets = [t for t in targets if t.enabled]
    default_target_id = enabled_targets[0].id if enabled_targets else (targets[0].id if targets else None)

    return render_template(
        "index.html",
        cards=cards,
        events=events,
        tz=tz,
        default_target_id=default_target_id,
        targets=targets,
    )


@bp.get("/api/target/<int:target_id>/latency")
def api_latency(target_id: int):
    tz = current_app.config["TIMEZONE"]
    t = Target.query.get(target_id)
    if not t:
        abort(404)
    payload = metrics.latency_series(target_id, hours=48, tz_name=tz)
    return jsonify(payload)
