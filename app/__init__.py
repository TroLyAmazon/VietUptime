__version__ = "1.0.0"


import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from flask_login import LoginManager

from .config import Config

db = SQLAlchemy()
csrf = CSRFProtect()
login_manager = LoginManager()
login_manager.login_view = "owner.login"

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)

    # Ensure instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)

    with app.app_context():
        from . import models  # noqa
        db.create_all()

        # Optional seed target
        _seed_target_if_needed(app)

    # Register blueprints
    from .routes.public import bp as public_bp
    from .routes.owner import bp as owner_bp
    app.register_blueprint(public_bp)
    app.register_blueprint(owner_bp)

    # Start scheduler (avoid double-run in Flask reloader)
    from .services.scheduler import start_scheduler, poll_all
    if (not app.debug) or (os.environ.get("WERKZEUG_RUN_MAIN") == "true"):
        start_scheduler(app)
        poll_all(app)  # chạy 1 lần ngay lập tức


    return app

def _seed_target_if_needed(app: Flask):
    from .models import Target
    if Target.query.count() > 0:
        return

    name = app.config.get("SEED_TARGET_NAME") or ""
    base = app.config.get("SEED_TARGET_BASE_URL") or ""
    path = app.config.get("SEED_TARGET_STATS_PATH") or "/api/stats"
    if name and base:
        t = Target(name=name, base_url=base.rstrip("/"), stats_path=path)
        db.session.add(t)
        db.session.commit()
