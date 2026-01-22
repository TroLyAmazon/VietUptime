import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from flask import (
    Blueprint, current_app, render_template, redirect, url_for,
    request, flash, send_file, Response
)
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Length
from werkzeug.security import check_password_hash
from flask_login import login_user, logout_user, login_required, UserMixin

from .. import db, login_manager
from ..models import Target, Snapshot
from ..services.scheduler import poll_target
from ..services.updates import check_update

bp = Blueprint("owner", __name__, url_prefix="/owner")


# ---- Auth: single owner user ----
class OwnerUser(UserMixin):
    id = "owner"


@login_manager.user_loader
def load_user(user_id):
    if user_id == "owner":
        return OwnerUser()
    return None


def _owner_credentials_ok(username: str, password: str) -> bool:
    cfg_user = current_app.config.get("OWNER_USERNAME", "owner")
    cfg_hash = current_app.config.get("OWNER_PASSWORD_HASH", "")
    if not cfg_hash:
        return False
    return username == cfg_user and check_password_hash(cfg_hash, password)


# ---- Forms ----
class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(max=120)])
    password = PasswordField("Password", validators=[DataRequired(), Length(max=200)])


class TargetForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(max=120)])
    base_url = StringField("Base URL", validators=[DataRequired(), Length(max=512)])
    stats_path = StringField("Stats Path", validators=[DataRequired(), Length(max=256)])


# ---- Login / Logout ----
@bp.get("/login")
def login():
    form = LoginForm()
    return render_template("owner_login.html", form=form)


@bp.post("/login")
def login_post():
    form = LoginForm()
    if not form.validate_on_submit():
        flash("Invalid form.", "bad")
        return render_template("owner_login.html", form=form), 400

    if _owner_credentials_ok(form.username.data.strip(), form.password.data):
        login_user(OwnerUser())
        return redirect(url_for("owner.targets"))

    flash("Login failed.", "bad")
    return render_template("owner_login.html", form=form), 401


@bp.post("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("public.index"))


# ---- Targets CRUD ----
@bp.get("/")
@login_required
def targets():
    form = TargetForm()
    targets_list = Target.query.order_by(Target.id.asc()).all()
    return render_template("owner_targets.html", targets=targets_list, form=form)


@bp.post("/targets/add")
@login_required
def targets_add():
    form = TargetForm()
    if not form.validate_on_submit():
        flash("Invalid data.", "bad")
        return redirect(url_for("owner.targets"))

    t = Target(
        name=form.name.data.strip(),
        base_url=form.base_url.data.strip().rstrip("/"),
        stats_path=form.stats_path.data.strip(),
        enabled=True,
    )
    db.session.add(t)
    db.session.commit()

    # poll thử 1 lần ngay khi add (để lên xanh liền)
    poll_target(current_app._get_current_object(), t.id, force=True)

    flash("Target added + tested.", "ok")
    return redirect(url_for("owner.targets"))


@bp.post("/targets/<int:target_id>/toggle")
@login_required
def targets_toggle(target_id: int):
    t = Target.query.get_or_404(target_id)
    t.enabled = not bool(t.enabled)
    db.session.commit()
    flash("Updated.", "ok")
    return redirect(url_for("owner.targets"))


@bp.post("/targets/<int:target_id>/toggle_click")
@login_required
def targets_toggle_click(target_id: int):
    t = Target.query.get_or_404(target_id)
    t.public_click = not bool(t.public_click)
    db.session.commit()
    flash("Public click updated.", "ok")
    return redirect(url_for("owner.targets"))


@bp.post("/targets/<int:target_id>/delete")
@login_required
def targets_delete(target_id: int):
    t = Target.query.get_or_404(target_id)
    db.session.delete(t)
    db.session.commit()
    flash("Deleted.", "ok")
    return redirect(url_for("owner.targets"))


# ---- Update checker (GitHub latest release) ----
@bp.get("/update")
@login_required
def update_page():
    info = None
    err = None
    try:
        info = check_update(current_app)
        if info is None:
            err = 'Missing GITHUB_REPO env. Set: GITHUB_REPO="TroLyAmazon/VietUptime"'
    except Exception as e:
        err = str(e)
    return render_template("owner_update.html", info=info, err=err)



# ---- DB viewer / export ----
@bp.get("/db")
@login_required
def db_page():
    uri = current_app.config["SQLALCHEMY_DATABASE_URI"]
    db_path = None
    if uri.startswith("sqlite:///"):
        rel = uri.replace("sqlite:///", "", 1)
        db_path = os.path.join(current_app.instance_path, rel)

    size = os.path.getsize(db_path) if (db_path and os.path.exists(db_path)) else 0
    targets_count = Target.query.count()
    snaps_count = Snapshot.query.count()

    latest_snaps = (
        Snapshot.query
        .order_by(Snapshot.hour_bucket.desc())
        .limit(100)
        .all()
    )

    return render_template(
        "owner_db.html",
        db_path=db_path,
        db_size=size,
        targets_count=targets_count,
        snaps_count=snaps_count,
        latest_snaps=latest_snaps,
    )


@bp.get("/db/export")
@login_required
def db_export():
    uri = current_app.config["SQLALCHEMY_DATABASE_URI"]
    if not uri.startswith("sqlite:///"):
        flash("Export only supported for SQLite.", "bad")
        return redirect(url_for("owner.db_page"))

    rel = uri.replace("sqlite:///", "", 1)
    db_path = os.path.join(current_app.instance_path, rel)
    if not os.path.exists(db_path):
        flash("DB not found.", "bad")
        return redirect(url_for("owner.db_page"))

    return send_file(db_path, as_attachment=True, download_name="status.sqlite")


@bp.get("/db/snapshots.csv")
@login_required
def snapshots_csv():
    """
    /owner/db/snapshots.csv?target_id=1&start=2026-01-01&end=2026-01-22
    dates are in Asia/Bangkok (day boundaries)
    """
    tz = ZoneInfo(current_app.config["TIMEZONE"])
    q = Snapshot.query

    target_id = request.args.get("target_id", type=int)
    if target_id:
        q = q.filter(Snapshot.target_id == target_id)

    start_s = request.args.get("start", "").strip()
    end_s = request.args.get("end", "").strip()

    if start_s:
        start_d = datetime.fromisoformat(start_s).date()
        start_dt = datetime.combine(start_d, datetime.min.time(), tzinfo=tz).replace(tzinfo=None)
        q = q.filter(Snapshot.hour_bucket >= start_dt)

    if end_s:
        end_d = datetime.fromisoformat(end_s).date()
        end_dt = (datetime.combine(end_d, datetime.min.time(), tzinfo=tz) + timedelta(days=1)).replace(tzinfo=None)
        q = q.filter(Snapshot.hour_bucket < end_dt)

    q = q.order_by(Snapshot.hour_bucket.asc()).limit(200000)

    def generate():
        header = [
            "target_id", "hour_bucket", "polled_at", "ok", "http_status", "latency_ms",
            "cpu_percent", "mem_percent", "disk_percent", "swap_percent"
        ]
        yield ",".join(header) + "\n"
        for s in q.all():
            row = [
                str(s.target_id),
                s.hour_bucket.isoformat(),
                s.polled_at.isoformat(),
                "1" if s.ok else "0",
                "" if s.http_status is None else str(s.http_status),
                "" if s.latency_ms is None else str(s.latency_ms),
                "" if s.cpu_percent is None else str(s.cpu_percent),
                "" if s.mem_percent is None else str(s.mem_percent),
                "" if s.disk_percent is None else str(s.disk_percent),
                "" if s.swap_percent is None else str(s.swap_percent),
            ]
            yield ",".join(row) + "\n"

    return Response(
        generate(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=snapshots.csv"},
    )
