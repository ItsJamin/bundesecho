from datetime import datetime
from operator import and_, or_

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import func
from sqlalchemy.orm import aliased

from app import db
from app.models import (
    MetaPerson,
    MetaQuote,
    Person,
    Quote,
    QuoteRequest,
    RelatedMetaQuote,
    ReviewStatus,
    Tag,
    get_latest_approved_quotes_query,
    quote_hashs,
    quote_tag,
)


quote_bp = Blueprint(
    'quote', __name__, template_folder='templates/quote/', url_prefix='/q'
)


@quote_bp.route('/latest')
def latest_quotes():
    quotes = Quote.query.order_by(Quote.date_created.desc()).limit(10).all()
    return render_template('latest.html', quotes=quotes)


@quote_bp.route('/random')
def random_quote_detail():
    # get a random approved quote
    random_quote = (
        Quote.query
        .filter_by(status=ReviewStatus.APPROVED.name)
        .order_by(func.random())
        .first()
    )
    if random_quote:
        return redirect(
            url_for(
                'quote.quote_detail',
                hash_id=quote_hashs.encode(random_quote.meta_quote_id),
            )
        )
    else:
        flash('Keine Zitate gefunden.', 'info')
        return redirect(url_for('main.home'))


@quote_bp.route('/submit', methods=['GET', 'POST'])
@login_required
def submit_quote():
    if request.method == 'POST':
        quoteid = request.form.get('quoteid', '').strip()
        text = request.form.get('text', '').strip()
        context = request.form.get('context', '').strip()
        person_name = request.form.get('person', '').strip()
        source = request.form.get('source', '').strip()
        tags_raw = request.form.get('tags', '').strip()
        date_said_raw = request.form.get('date_said')
        date_said = None
        orig_text = request.form.get('orig_text', '').strip()
        orig_lang = request.form.get('orig_lang', '').strip()

        if date_said_raw:
            try:
                date_said = datetime.strptime(date_said_raw, '%Y-%m-%d')
            except ValueError:
                flash('Ungültiges Datum (Format: YYYY-MM-DD)', 'warning')

        errors = []
        if not text:
            errors.append('Aussage ist erforderlich.')
        if not person_name:
            errors.append('Person ist erforderlich.')
        if not source:
            errors.append('Quelle ist erforderlich.')
        if request.form.get('is_translation') == '1':
            if not orig_text:
                errors.append('Originaltext ist erforderlich.')
            if not orig_lang:
                errors.append('Originalsprache ist erforderlich.')

        if errors:
            return render_template('submit.html', errors=errors, form_data=request.form)

        # find or create MetaPerson and Person
        # TODO: replace with more robust logic to create in review stop not submit
        meta_person = MetaPerson.query.filter(
            MetaPerson.persons.any(
                and_(
                    Person.name == person_name,
                    Person.status != ReviewStatus.REJECTED.value,
                )
            )
        ).first()
        if not meta_person:
            meta_person = MetaPerson()
            db.session.add(meta_person)
            db.session.flush()

            person = Person(
                name=person_name,
                meta_person_id=meta_person.id,
                status=ReviewStatus.PENDING.value,
                submitted_by_id=current_user.id,
            )
            db.session.add(person)
            db.session.flush()
        else:
            # get latest approved Person for this MetaPerson
            person = meta_person.get_latest(status=ReviewStatus.APPROVED.value)
            if not person:
                person = meta_person.get_latest(status=ReviewStatus.PENDING.value)
            if not person:
                # if none approved, fallback: create new Person linked to MetaPerson
                person = Person(
                    name=person_name,
                    metaperson_id=meta_person.id,
                    status=ReviewStatus.PENDING.value,
                    submitted_by_id=current_user.id,
                )
                db.session.add(person)
                db.session.flush()

        # process tags: find existing or create new ones
        # TODO: replace with more robust logic to create in review stop not submit
        tag_names = [t.strip() for t in tags_raw.split(',') if t.strip()]
        tags = []
        for name in tag_names:
            tag = Tag.query.filter_by(name=name).first()
            if not tag:
                tag = Tag(name=name)
                db.session.add(tag)
                db.session.flush()
            tags.append(tag)

        # MetaQuote: find or create
        if quoteid is not None and quoteid != '':
            meta_quote = MetaQuote.query.filter(MetaQuote.id == int(quoteid)).first()
        else:
            meta_quote = MetaQuote()
            db.session.add(meta_quote)
            db.session.flush()

        # create quote
        quote = Quote(
            text=text,
            context=context,
            orig_text=orig_text if orig_text else None,
            orig_lang=orig_lang if orig_lang else None,
            source=source if source else None,
            meta_person=meta_person,
            date_said=date_said,
            meta_quote_id=meta_quote.id,
            status=ReviewStatus.PENDING.name,
            submitted_by_id=current_user.id,
        )
        db.session.add(quote)
        db.session.commit()

        entries = [
            {'quote_id': quote.id, 'tag_id': tag.id, 'order': idx}
            for idx, tag in enumerate(tags)
        ]

        if entries:
            db.session.execute(quote_tag.insert(), entries)

        db.session.commit()

        flash('Zitat erfolgreich eingereicht!', 'success')
        return redirect(url_for('quote.latest_quotes'))

    return render_template('submit.html')


@quote_bp.route('/submit_request', methods=['GET', 'POST'])
def submit_request():
    if request.method == 'POST':
        text = request.form.get('text', '').strip()

        errors = []
        if not text:
            errors.append('Ein Text ist erforderlich.')

        if errors:
            return render_template(
                'submit_request.html', errors=errors, form_data=request.form
            )

        # save request
        req = QuoteRequest(text=text)
        db.session.add(req)
        db.session.commit()

        flash('Anfrage erfolgreich eingereicht!', 'success')
        return redirect(url_for('quote.latest_quotes'))

    return render_template('submit_request.html')


@quote_bp.route('/', methods=['GET'])
@quote_bp.route('/search', methods=['GET'])
def search():
    people = Person.query.order_by(Person.name).all()
    tags = Tag.query.order_by(Tag.name).all()

    mode = request.args.get('mode', 'simple')

    query, QuoteAlias = get_latest_approved_quotes_query()

    # ----- simple search -----
    if mode == 'simple':
        q = request.args.get('q', '').strip()
        if q:
            query = query.join(QuoteAlias.meta_person).join(
                Person, QuoteAlias.meta_person_id == Person.meta_person_id
            )
            query = query.outerjoin(QuoteAlias.tags)
            query = query.filter(
                or_(
                    or_(
                        or_(
                            QuoteAlias.text.ilike(f'%{q}%'),
                            or_(
                                QuoteAlias.orig_text.ilike(f'%{q}%'),
                                QuoteAlias.context.ilike(f'%{q}%'),
                            ),
                        ),
                        or_(
                            or_(Person.name.ilike(f'%{q}%'), Tag.name.ilike(f'%{q}%')),
                            Person.tags.any(Tag.name.ilike(f'%{q}%')),
                        ),
                    ),
                    or_(
                        QuoteAlias.source.ilike(f'%{q}%'),
                        QuoteAlias.secondary_source.ilike(f'%{q}%'),
                    ),
                )
            )
        query = query.order_by(QuoteAlias.date_said.desc())
    else:
        # ----- advanced search -----
        selected_meta_person_id = request.args.get('meta_person')
        selected_tag_ids = request.args.getlist('tags')
        selected_tag_neg_ids = request.args.getlist('tags_neg')
        selected_person_tag_ids = request.args.getlist('person_tags')
        selected_person_tag_neg_ids = request.args.getlist('person_tags_neg')
        text_query = request.args.get('text_query', '').strip()
        date_from_str = request.args.get('date_from', '').strip()
        date_to_str = request.args.get('date_to', '').strip()
        sort_by = request.args.get('sort_by', 'date_said')
        sort_order = request.args.get('sort_order', 'desc')

        if selected_meta_person_id:
            query = query.filter(QuoteAlias.meta_person_id == selected_meta_person_id)

        # positive tags
        if selected_tag_ids:
            pos_ids = list(map(int, selected_tag_ids))
            query = (
                query
                .join(QuoteAlias.tags)
                .filter(Tag.id.in_(pos_ids))
                .group_by(QuoteAlias.id)
                .having(func.count(func.distinct(Tag.id)) == len(pos_ids))
            )

        # negative tags
        if selected_tag_neg_ids:
            neg_ids = list(map(int, selected_tag_neg_ids))
            if neg_ids:
                subquery = (
                    db.session
                    .query(QuoteAlias.id)
                    .join(QuoteAlias.tags)
                    .filter(Tag.id.in_(neg_ids))
                    .subquery()
                )
                query = query.filter(~QuoteAlias.id.in_(subquery))

        # person tags (AND logic for positive selections)
        if selected_person_tag_ids:
            person_tag_ids = list(map(int, selected_person_tag_ids))
            if person_tag_ids:
                person_tag_meta_ids = (
                    db.session
                    .query(Person.meta_person_id)
                    .join(Person.tags)
                    .filter(Tag.id.in_(person_tag_ids))
                    .group_by(Person.meta_person_id)
                    .having(func.count(func.distinct(Tag.id)) == len(person_tag_ids))
                    .subquery()
                )
                query = query.filter(QuoteAlias.meta_person_id.in_(person_tag_meta_ids))

        if selected_person_tag_neg_ids:
            person_tag_neg_ids = list(map(int, selected_person_tag_neg_ids))
            if person_tag_neg_ids:
                person_tag_neg_meta_ids = (
                    db.session
                    .query(Person.meta_person_id)
                    .join(Person.tags)
                    .filter(Tag.id.in_(person_tag_neg_ids))
                    .subquery()
                )
                query = query.filter(
                    ~QuoteAlias.meta_person_id.in_(person_tag_neg_meta_ids)
                )

        # text query
        if text_query:
            query = query.filter(
                or_(
                    QuoteAlias.text.ilike(f'%{text_query}%'),
                    or_(
                        QuoteAlias.orig_text.ilike(f'%{text_query}%'),
                        QuoteAlias.context.ilike(f'%{text_query}%'),
                    ),
                )
            )

        # date filters
        if date_from_str:
            try:
                date_from = datetime.strptime(date_from_str, '%Y-%m-%d').date()
                query = query.filter(QuoteAlias.date_said >= date_from)
            except ValueError:
                pass
        if date_to_str:
            try:
                date_to = datetime.strptime(date_to_str, '%Y-%m-%d').date()
                query = query.filter(QuoteAlias.date_said <= date_to)
            except ValueError:
                pass

        # sorting
        if sort_by == 'date_said':
            sort_column = QuoteAlias.date_said
        elif sort_by == 'author_name':
            PersonAlias = aliased(Person)
            query = query.join(QuoteAlias.meta_person).join(
                PersonAlias, QuoteAlias.meta_person_id == PersonAlias.meta_person_id
            )
            sort_column = PersonAlias.name
        else:
            sort_column = QuoteAlias.date_said

        query = query.order_by(
            sort_column.asc() if sort_order == 'asc' else sort_column.desc()
        )

    # Ensure unique quotes by grouping
    query = query.group_by(QuoteAlias.id)

    # ----- pagination -----
    page = int(request.args.get('page', 1))
    per_page = 10
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    quotes = paginated.items

    # ----- AJAX / infinite scroll (return HTML) -----
    if request.args.get('ajax'):
        html = render_template('quote_boxes_ajax.html', quotes=quotes)
        return {'html': html, 'has_next': paginated.has_next}

    # -------- prepare tags and person tags for rendering in order --------
    selected_tags = []
    selected_person_tags = []
    if mode == 'advanced':
        ordered_tag_ids = selected_tag_ids + selected_tag_neg_ids
        ordered_person_tag_ids = selected_person_tag_ids + selected_person_tag_neg_ids
        tags_dict = {str(tag.id): tag for tag in tags}

        for tid in ordered_tag_ids:
            if tid in tags_dict:
                selected_tags.append({
                    'id': tags_dict[tid].id,
                    'name': tags_dict[tid].name,
                    'negative': tid in selected_tag_neg_ids,
                })

        for tid in ordered_person_tag_ids:
            if tid in tags_dict:
                selected_person_tags.append({
                    'id': tags_dict[tid].id,
                    'name': tags_dict[tid].name,
                    'negative': tid in selected_person_tag_neg_ids,
                })

    return render_template(
        'search.html',
        quotes=quotes,
        people=people,
        tags=tags,  # for autocomplete
        selected_tags=selected_tags,
        selected_meta_person_id=request.args.get('meta_person'),
        selected_tag_ids=selected_tag_ids if mode == 'advanced' else [],
        selected_tag_neg_ids=selected_tag_neg_ids if mode == 'advanced' else [],
        selected_person_tag_ids=selected_person_tag_ids if mode == 'advanced' else [],
        selected_person_tag_neg_ids=selected_person_tag_neg_ids
        if mode == 'advanced'
        else [],
        selected_person_tags=selected_person_tags,
        text_query=request.args.get('text_query', '')
        if mode == 'advanced'
        else request.args.get('q', ''),
        date_from=request.args.get('date_from', '') if mode == 'advanced' else None,
        date_to=request.args.get('date_to', '') if mode == 'advanced' else None,
        mode=mode,
        page=page,
        has_next=paginated.has_next,
    )


@quote_bp.route('/view/<hash_id>')
def quote_detail(hash_id):
    meta_quote_id = quote_hashs.decode(hash_id)[0]
    meta_quote = MetaQuote.query.get_or_404(meta_quote_id)

    quote = meta_quote.get_latest()
    if not quote:
        quote = meta_quote.get_latest(status=ReviewStatus.PENDING)
    if not quote:
        abort(404)

    person = quote.meta_person.get_latest()
    if not person:
        person = quote.meta_person.get_latest(status=ReviewStatus.PENDING)

    # collect related meta_quotes (only APPROVED)
    related_relations = RelatedMetaQuote.query.filter(
        RelatedMetaQuote.status == ReviewStatus.APPROVED,
        or_(
            RelatedMetaQuote.meta_quote_a_id == meta_quote.id,
            RelatedMetaQuote.meta_quote_b_id == meta_quote.id,
        ),
    ).all()

    # extract the *other* meta_quote from each relation
    related_quotes = []
    for rel in related_relations:
        other_id = (
            rel.meta_quote_b_id
            if rel.meta_quote_a_id == meta_quote_id
            else rel.meta_quote_a_id
        )
        related_mq = MetaQuote.query.get(other_id)
        if related_mq:
            latest = related_mq.get_latest(ReviewStatus.APPROVED)
            if latest:
                related_quotes.append(latest)

    # related_quotes = sorted(related_quotes, key=lambda q: q.date_said)

    return render_template(
        'quote.html', quote=quote, person=person, related_quotes=related_quotes
    )


@quote_bp.route('/embed/<hash_id>')
def quote_embed(hash_id):
    meta_quote_id = quote_hashs.decode(hash_id)[0]
    meta_quote = MetaQuote.query.get_or_404(meta_quote_id)

    quote = meta_quote.get_latest()
    if not quote:
        quote = meta_quote.get_latest(status=ReviewStatus.PENDING)
    if not quote:
        abort(404)

    person = quote.meta_person.get_latest()
    if not person:
        person = quote.meta_person.get_latest(status=ReviewStatus.PENDING)

    return render_template(
        'quote_embed.html',
        quote=quote,
        person=person,
        embed_mode=True,
    )


@quote_bp.route('/edit/<hash_id>', methods=['GET'])
@login_required
def edit_quote(hash_id):
    meta_quote_id = quote_hashs.decode(hash_id)[0]
    # Get latest approved quote for this MetaQuote
    meta_quote = MetaQuote.query.get_or_404(meta_quote_id)
    quote = meta_quote.get_latest(status=ReviewStatus.APPROVED)

    if not quote:
        flash('Keine freigeschaltete Version für dieses Zitat gefunden.', 'warning')
        return redirect(url_for('quote.latest_quotes'))

    form_data = {
        'text': quote.text,
        'context': quote.context,
        'source': quote.source,
        'person': quote.meta_person.get_latest(status=ReviewStatus.APPROVED).name
        if quote.meta_person
        else '',
        'tags': ','.join(tag.name for tag in quote.tags),
        'date_said': quote.date_said.strftime('%Y-%m-%d') if quote.date_said else '',
    }

    return render_template('submit.html', form_data=form_data, quoteid=meta_quote.id)


@quote_bp.route('/quote/<hash_id>/suggest_related', methods=['POST'])
@login_required
def suggest_related(hash_id):
    # decode main quote
    try:
        meta_quote_a_id = quote_hashs.decode(hash_id)[0]
    except Exception:
        abort(400, 'Ungültiger Hash')

    # get submitted link
    submitted_link = request.form.get('related_link', '').strip()
    if not submitted_link:
        flash('Kein Link angegeben', 'danger')
        return redirect(url_for('quote.quote_detail', hash_id=hash_id))

    # extract hash_id from link
    try:
        # assumes format like: https://bundesecho.de/q/quote/ABCdef
        quote_hash = submitted_link.rstrip('/').split('/')[-1]
        meta_quote_b_id = quote_hashs.decode(quote_hash)[0]
    except Exception:
        flash('Ungültiger Link', 'danger')
        return redirect(url_for('quote.quote_detail', hash_id=hash_id))

    # don't allow self-link
    if meta_quote_a_id == meta_quote_b_id:
        flash('Zitat kann nicht mit sich selbst verknüpft werden', 'warning')
        return redirect(url_for('quote.quote_detail', hash_id=hash_id))

    # check if it already exists
    exists = RelatedMetaQuote.query.filter(
        or_(
            and_(
                RelatedMetaQuote.meta_quote_a_id == meta_quote_a_id,
                RelatedMetaQuote.meta_quote_b_id == meta_quote_b_id,
            ),
            and_(
                RelatedMetaQuote.meta_quote_a_id == meta_quote_b_id,
                RelatedMetaQuote.meta_quote_b_id == meta_quote_a_id,
            ),
        )
    ).first()

    if exists:
        flash('Diese Beziehung existiert bereits oder wurde vorgeschlagen.', 'info')
        return redirect(url_for('quote.quote_detail', hash_id=hash_id))

    # create relation (PENDING)
    new_relation = RelatedMetaQuote(
        meta_quote_a_id=meta_quote_a_id,
        meta_quote_b_id=meta_quote_b_id,
        status=ReviewStatus.PENDING,
    )
    db.session.add(new_relation)
    db.session.commit()
    flash('Verwandtes Zitat vorgeschlagen', 'success')
    return redirect(url_for('quote.quote_detail', hash_id=hash_id))
