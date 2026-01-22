from datetime import datetime
from . import db


class Target(db.Model):
    __tablename__ = "targets"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    base_url = db.Column(db.String(512), nullable=False)
    stats_path = db.Column(db.String(256), nullable=False, default="/api/stats")

    enabled = db.Column(db.Boolean, nullable=False, default=True)
    public_click = db.Column(db.Boolean, nullable=False, default=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    snapshots = db.relationship("Snapshot", back_populates="target", cascade="all,delete-orphan")
    events = db.relationship("Event", back_populates="target", cascade="all,delete-orphan")


class Snapshot(db.Model):
    __tablename__ = "snapshots"

    id = db.Column(db.Integer, primary_key=True)
    target_id = db.Column(db.Integer, db.ForeignKey("targets.id"), nullable=False)

    polled_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    hour_bucket = db.Column(db.DateTime, nullable=False)

    ok = db.Column(db.Boolean, nullable=False, default=False)
    http_status = db.Column(db.Integer, nullable=True)
    latency_ms = db.Column(db.Integer, nullable=True)

    cpu_percent = db.Column(db.Float, nullable=True)
    mem_percent = db.Column(db.Float, nullable=True)
    disk_percent = db.Column(db.Float, nullable=True)
    swap_percent = db.Column(db.Float, nullable=True)

    raw_json = db.Column(db.Text, nullable=True)

    target = db.relationship("Target", back_populates="snapshots")

    __table_args__ = (
        db.Index("ix_snapshots_target_hour", "target_id", "hour_bucket"),
    )


class Event(db.Model):
    __tablename__ = "events"

    id = db.Column(db.Integer, primary_key=True)
    target_id = db.Column(db.Integer, db.ForeignKey("targets.id"), nullable=False)

    state = db.Column(db.String(10), nullable=False)  # "up" / "down"
    started_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime, nullable=True)

    reason = db.Column(db.String(255), nullable=True)
    http_status = db.Column(db.Integer, nullable=True)

    target = db.relationship("Target", back_populates="events")

    __table_args__ = (
        db.Index("ix_events_target_started", "target_id", "started_at"),
    )
