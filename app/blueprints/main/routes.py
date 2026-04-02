import os
import random  # Import random module for seeding

from datetime import date  # Import datetime
from xml.sax.saxutils import escape

from flask import (
    Blueprint,
    Response,
    jsonify,
    redirect,
    render_template,
    render_template_string,
    request,
    send_from_directory,
    session,
    url_for,
)
from sqlalchemy import func

from app.models import MetaPerson, MetaQuote, Person, Tag, person_hashs


main_bp = Blueprint('main', __name__, template_folder='templates/main/')


@main_bp.route('/')
def home():
    count_quotes = MetaQuote.query.all()
    valid_quotes = [mq for mq in count_quotes if mq.get_latest() is not None]

    count_persons = MetaPerson.query.all()
    valid_persons = [mp for mp in count_persons if mp.get_latest() is not None]

    quotes_to_display = []
    daily_quote = get_daily_quote()
    if daily_quote:
        quotes_to_display.append(daily_quote)

    return render_template(
        'home.html',
        quotes=quotes_to_display,
        quote_count=round_down_to_magnitude(len(valid_quotes)),
        person_count=round_down_to_magnitude(len(valid_persons)),
    )


@main_bp.route('/api/random_quote')
def api_random_quote():
    random_q = random_quotes(1)
    if not random_q:
        return jsonify({'html': '<p>Kein Zitat verfügbar.</p>'}), 200

    # render the quote using the same template fragment
    quote_html = render_template_string(
        '{% include "quote_box.html" %}', quote=random_q[0]
    )
    return jsonify({'html': quote_html})


@main_bp.route('/api/person')
def list_person():
    term = request.args.get('q', '').strip()
    if not term:
        return jsonify([])

    # all MetaPersons, with at least one Person whose name matches the search term
    meta_persons = (
        MetaPerson.query
        .join(MetaPerson.persons)
        .filter(Person.name.ilike(f'%{term}%'))
        .all()
    )

    # for each MetaPerson, get the latest approved Person
    results = []
    for meta in meta_persons:
        latest_person = meta.get_latest()
        if latest_person and term.lower() in latest_person.name.lower():
            results.append({'id': meta.id, 'text': latest_person.name})

    return jsonify(results)


@main_bp.route('/api/tag')
def list_tag():
    term = request.args.get('q', '')
    tags = Tag.query.filter(Tag.name.ilike(f'%{term}%')).all()
    return jsonify([{'id': t.id, 'text': t.name} for t in tags])


@main_bp.route('/robots.txt')
def robots_txt():
    return send_from_directory(
        directory=os.path.join(main_bp.root_path, '../../static/info'),
        path='robots.txt',
        mimetype='text/plain',
    )


@main_bp.route('/sitemap.xml')
def sitemap():
    base_url = 'https://www.bundesecho.de'

    # static sites with higher priority
    static_urls = [
        ('/', '1.0', 'weekly'),
        ('/p/', '0.9', 'weekly'),
        ('/q/', '0.9', 'daily'),
    ]

    # quote_urls = [f"/q/view/{quote_hashs.encode(q.id)}" for q in MetaQuote.query.all()]

    # dynamic person URLs with medium priority
    person_urls = [
        (f'/p/view/{person_hashs.encode(p.id)}', '0.6', 'monthly')
        for p in MetaPerson.query.all()
    ]

    all_urls = static_urls + person_urls

    # build XML sitemap
    sitemap_xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    sitemap_xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'

    for path, priority, freq in all_urls:
        loc = escape(f'{base_url}{path}')
        sitemap_xml += (
            f'  <url>\n'
            f'    <loc>{loc}</loc>\n'
            f'    <priority>{priority}</priority>\n'
            f'    <changefreq>{freq}</changefreq>\n'
            f'  </url>\n'
        )

    sitemap_xml += '</urlset>'

    return Response(sitemap_xml, mimetype='application/xml')


@main_bp.route('/service-worker.js')
def service_worker():
    return send_from_directory(
        directory=os.path.join(main_bp.root_path, '../../static/js'),
        path='service-worker.js',
    )


@main_bp.route('/toggle-theme')
def toggle_theme():
    current_theme = session.get('theme', 'dark')
    new_theme = 'light' if current_theme == 'dark' else 'dark'
    session['theme'] = new_theme

    return redirect(request.referrer or url_for('main.home'))


# ----- helping functions -----


def random_quotes(count):
    """returns a list of random approved MetaQuote objects, up to the specified count."""
    all_metaquotes = MetaQuote.query.order_by(func.random()).all()

    latest_quotes = []
    for metaquote in all_metaquotes:
        if len(latest_quotes) >= count:
            break
        latest_quote = metaquote.get_latest()
        if latest_quote:
            latest_quotes.append(latest_quote)

    return latest_quotes


def round_down_to_magnitude(n: int) -> int:
    """rounds down the given number to the nearest magnitude (1, 10, 100, etc.) with a factor of 1 or 5."""
    if n == 0:
        return 0
    magnitude = 10 ** (len(str(n)) - 1)
    normalized = n / magnitude
    rounded = int(normalized * 2) / 2
    return int(rounded * magnitude)


def get_daily_quote():
    """
    deterministically selects a quote for the current day.
    this ensures the same quote is shown to all users on a given day.
    """

    today_ordinal = date.today().toordinal()

    all_metaquotes = MetaQuote.query.all()
    valid_metaquotes = [mq for mq in all_metaquotes if mq.get_latest() is not None]

    if not valid_metaquotes:
        return None

    # use the day's ordinal number as a seed for the random number generator
    # this ensures the same "random" quote is picked for everyone on a given day
    random.seed(today_ordinal + 67)
    daily_metaquote = random.choice(valid_metaquotes)

    return daily_metaquote.get_latest()
