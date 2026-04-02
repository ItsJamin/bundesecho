from collections import defaultdict

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy.orm import joinedload

from app import db
from app.models import (
    MetaPerson,
    Person,
    ReviewStatus,
    get_latest_approved_quotes_query,
    person_hashs,
)


person_bp = Blueprint(
    'person', __name__, template_folder='templates/person', url_prefix='/p'
)


@person_bp.route('/')
def list_persons():
    # load all MetaPersons with their most recent approved Person snapshot
    meta_persons = MetaPerson.query.options(joinedload(MetaPerson.persons)).all()

    persons = []
    for meta in meta_persons:
        current_person = meta.get_latest()
        if current_person:
            persons.append(current_person)

    grouped = defaultdict(list)
    for person in persons:
        names = person.name.split()
        first_letter = names[-1][0].upper()
        grouped[first_letter].append(person)

    for letter in grouped:
        grouped[letter].sort(key=lambda p: p.name.split()[-1])
    grouped = dict(sorted(grouped.items()))
    return render_template('list.html', grouped_persons=grouped)


@person_bp.route('/view/<hash_id>')
def person_detail(hash_id):
    meta_person_id = person_hashs.decode(hashid=hash_id)[0]
    meta_person = MetaPerson.query.get_or_404(meta_person_id)
    person = meta_person.get_latest()
    if not person:
        abort(404)  # no approved snapshot found

    # get latest approved quotes related to this MetaPerson
    query, QuoteAlias = get_latest_approved_quotes_query()
    quotes = (
        query
        .filter(QuoteAlias.meta_person_id == meta_person.id)
        .order_by(QuoteAlias.date_said.desc())
        .all()
    )

    tags = [tag for tag in person.tags if tag.category is not None]

    return render_template('detail.html', person=person, quotes=quotes, tags=tags)


@person_bp.route('/edit/<hash_id>', methods=['GET', 'POST'])
@login_required
def edit_person(hash_id):
    meta_person_id = person_hashs.decode(hashid=hash_id)[0]
    meta_person = MetaPerson.query.get_or_404(meta_person_id)
    person = meta_person.get_latest()

    if request.method == 'POST':
        # create new version instead of editing existing one, to preserve history and allow review
        person = Person(
            meta_person_id=meta_person_id,
            name=request.form.get('name'),
            description=request.form.get('description'),
            image_url=request.form.get('image_url')
            if request.form.get('image_url') not in [None, 'None', '']
            else None,
            image_src=request.form.get('image_src')
            if request.form.get('image_src') not in [None, 'None', '']
            else None,
            status=ReviewStatus.PENDING,
            submitted_by_id=current_user.id,
        )

        db.session.add(person)
        db.session.commit()

        flash('Deine Änderungen wurden eingereicht und werden reviewt.', 'info')
        return redirect(
            url_for(
                'person.person_detail',
                hash_id=person_hashs.encode(person.meta_person_id),
            )
        )

    # GET: show current approved version in form
    return render_template('edit.html', person=person)
