import os
import uuid

from datetime import date, timedelta

from dotenv import load_dotenv
from flask import Flask, render_template, request, session
from flask_login import LoginManager
from flask_migrate import Migrate, upgrade
from flask_sqlalchemy import SQLAlchemy


login_manager = LoginManager()

load_dotenv()

db = SQLAlchemy()
migrate = Migrate()


def create_app(config_name='development'):
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quotes.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # configure the separate database for statistics
    app.config['SQLALCHEMY_BINDS'] = {
        'stats': 'sqlite:///stats.db',
        'about': 'sqlite:///about.db',
    }

    app.secret_key = os.environ.get('SECRET_KEY', 'unsafe_default_dev_key')

    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_SAMESITE='Lax',
        PERMANENT_SESSION_LIFETIME=timedelta(days=1),
        REMEMBER_COOKIE_HTTPONLY=True,
        REMEMBER_COOKIE_SECURE=True,
        REMEMBER_COOKIE_SAMESITE='Strict',
        # REMEMBER_COOKIE_DURATION=timedelta(days=31),
    )

    db.init_app(app)
    migrate.init_app(app, db, render_as_batch=True)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    from . import models  # noqa: PLC0415
    from .about_models import InfoNews  # noqa: F401, PLC0415
    from .stats_models import VisitStat  # noqa: PLC0415

    # no need to initialize stats_db separately, as it uses the main db instance with a bind key

    with app.app_context():
        db.create_all()  # create tables for all configured binds

    @login_manager.user_loader
    def load_user(user_id):
        return models.User.query.get(int(user_id))

    from app.blueprints.auth import auth_bp  # noqa: PLC0415

    app.register_blueprint(auth_bp, url_prefix='/auth')

    from .blueprints.main import main_bp  # noqa: PLC0415

    app.register_blueprint(main_bp)

    from .blueprints.quote import quote_bp  # noqa: PLC0415

    app.register_blueprint(quote_bp)

    from .blueprints.person import person_bp  # noqa: PLC0415

    app.register_blueprint(person_bp)

    from .blueprints.review import review_bp  # noqa: PLC0415

    app.register_blueprint(review_bp)

    from .blueprints.admin import admin_bp  # noqa: PLC0415

    app.register_blueprint(admin_bp)

    @app.context_processor
    def inject_hashids():
        return {'quote_hashs': models.quote_hashs, 'person_hashs': models.person_hashs}

    @app.before_request
    def track_visit():
        if not (
            request.path.startswith('/p/')
            or request.path.startswith('/q/')
            or request.path == '/'
        ):
            return

        path = request.path
        query_params = (
            request.query_string.decode('utf-8') if request.query_string else None
        )
        today = date.today()

        session_id = session.get('visitor_id')
        if not session_id:
            session_id = str(uuid.uuid4())
            session['visitor_id'] = session_id

        stat = VisitStat.query.filter_by(
            session_id=session_id, path=path, query_params=query_params, date=today
        ).first()
        if stat:
            stat.count += 1
            stat.session_id = session_id
        else:
            stat = VisitStat(
                session_id=session_id,
                path=path,
                query_params=query_params,
                date=today,
                count=1,
            )
            db.session.add(stat)
        db.session.commit()

    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def catch_all(path):
        return render_template('404.html'), 404

    # run migrations on startup
    if False:  # this block is now for the main database only. Stats DB will be created on first access.
        with app.app_context():
            try:
                upgrade()
            except Exception as e:
                print(f'Error during database migration: {e}')  # noqa: T201

    return app
