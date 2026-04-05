from datetime import date, timedelta

from flask import Blueprint, abort, flash, redirect, render_template, url_for
from flask_login import current_user, login_required
from sqlalchemy import text

from app import db as stats_db
from app.models import MetaPerson, MetaQuote, Person, Quote, ReviewStatus, User, db
from app.stats_models import VisitStat


admin_bp = Blueprint(
    'admin', __name__, url_prefix='/ajmin', template_folder='templates/admin/'
)


def is_admin():
    return current_user.is_authenticated and current_user.role in ['admin']


@admin_bp.before_request
@login_required
def require_moderator():
    if not is_admin():
        abort(404)


@admin_bp.route('/')
def index():
    users_raw = User.query.all()
    users = [{'username': u.username, 'role': u.role} for u in users_raw]

    # count MetaQuotes with at least one approved Quote
    count_quotes = (
        db.session
        .query(MetaQuote)
        .join(Quote)
        .filter(Quote.status == ReviewStatus.APPROVED)
        .distinct()
        .count()
    )

    # Count MetaPersons with at least one approved Person
    count_persons = (
        db.session
        .query(MetaPerson)
        .join(Person)
        .filter(Person.status == ReviewStatus.APPROVED)
        .distinct()
        .count()
    )

    return render_template(
        'admin.html',
        users=users,
        count_quotes=count_quotes,
        count_persons=count_persons,
    )


@admin_bp.route('/clean')
def clean_stat():
    VisitStat.query.delete()
    stats_db.session.commit()
    with stats_db.engine.connect() as conn:
        conn.execute(text('VACUUM'))
        conn.commit()
    flash('Statistiken wurden zurückgesetzt.', 'success')
    return redirect(url_for('admin.index'))


@admin_bp.route('/stats')
def stats():
    today = date.today()

    clicks_today = (
        db.session
        .query(db.func.sum(VisitStat.count))
        .filter(VisitStat.date == today)
        .scalar()
    )
    if clicks_today is None:
        clicks_today = 0

    unique_visitors_today = (
        db.session
        .query(VisitStat.session_id)
        .filter(VisitStat.date == today)
        .distinct()
        .count()
    )

    # top 5 most visited routes for today, filtered by /p/view/* and /q/view/*
    top_routes_today = (
        db.session
        .query(VisitStat.path, db.func.sum(VisitStat.count).label('total_clicks'))
        .filter(
            db.or_(VisitStat.path.like('/p/view/%'), VisitStat.path.like('/q/view/%'))
        )
        .group_by(VisitStat.path)
        .order_by(db.func.sum(VisitStat.count).desc())
        .limit(10)
        .all()
    )

    # data for the last 7 days including today
    dates = [(today - timedelta(days=i)) for i in range(6, -1, -1)]

    daily_stats = []
    for d in dates:
        daily_clicks = (
            db.session
            .query(db.func.sum(VisitStat.count))
            .filter(
                VisitStat.date == d,
            )
            .scalar()
            or 0
        )
        daily_unique_visitors = (
            db.session
            .query(VisitStat.session_id)
            .filter(
                VisitStat.date == d,
            )
            .distinct()
            .count()
        )
        daily_stats.append({
            'date': d.strftime('%Y-%m-%d'),
            'clicks': daily_clicks,
            'unique_visitors': daily_unique_visitors,
        })

    return render_template(
        'stats.html',
        clicks_today=clicks_today,
        unique_visitors_today=unique_visitors_today,
        top_routes_today=top_routes_today,
        daily_stats=daily_stats,
    )
