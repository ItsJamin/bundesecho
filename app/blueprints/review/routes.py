from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.models import (
    Person,
    Quote,
    QuoteRequest,
    RelatedMetaQuote,
    ReviewStatus,
    Tag,
    TagCategory,
    db,
)


review_bp = Blueprint(
    'review', __name__, url_prefix='/review', template_folder='templates/review/'
)


def is_moderator():
    return current_user.is_authenticated and current_user.role in ['moderator', 'admin']


@review_bp.before_request
@login_required
def require_moderator():
    if not is_moderator():
        flash('Kein Zugriff – Moderatorrechte erforderlich', 'danger')
        return redirect(url_for('main.index'))


@review_bp.route('/')
def index():
    pending_persons = Person.query.filter_by(status=ReviewStatus.PENDING).all()
    pending_quotes = Quote.query.filter_by(status=ReviewStatus.PENDING).all()
    pending_related = RelatedMetaQuote.query.filter_by(
        status=ReviewStatus.PENDING
    ).all()
    pending_requests = QuoteRequest.query.order_by(
        QuoteRequest.date_created.desc()
    ).all()

    return render_template(
        'index.html',
        persons=pending_persons,
        quotes=pending_quotes,
        related_quotes=pending_related,
        quote_requests=pending_requests,
    )


@review_bp.route('/person/<int:id>', methods=['GET', 'POST'])
def review_person(id):
    person = Person.query.get_or_404(id)
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'approve':
            person.status = ReviewStatus.APPROVED

        elif action == 'reject':
            person.status = ReviewStatus.REJECTED

        elif action == 'edit':
            person.name = request.form.get('name', '').strip()
            person.description = request.form.get('description', '').strip()
            person.image_url = request.form.get('image_url', '').strip()
            person.image_src = request.form.get('image_src', '').strip()
            person.image_copyright = request.form.get('image_copyright', '').strip()
            person.status = ReviewStatus.APPROVED

        person.reviewed_by = current_user

        db.session.commit()
        return redirect(url_for('review.index'))

    return render_template('person_review.html', person=person)


@review_bp.route('/quote/<int:id>', methods=['GET', 'POST'])
def review_quote(id):
    quote = Quote.query.get_or_404(id)

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'approve':
            quote.status = ReviewStatus.APPROVED
            quote.reviewed_by = current_user

        elif action == 'reject':
            quote.status = ReviewStatus.REJECTED
            quote.reviewed_by = current_user

        elif action == 'edit':
            quote.text = request.form.get('text', '').strip()
            quote.context = request.form.get('context', '').strip()
            quote.source = request.form.get('source', '').strip()
            quote.secondary_source = request.form.get('secondary_source', '').strip()
            date_said = request.form.get('date_said', '').strip()
            if date_said:
                try:
                    quote.date_said = datetime.strptime(date_said, '%Y-%m-%d')
                except ValueError:
                    flash('Ungültiges Datum (Format: YYYY-MM-DD)', 'danger')

            # get tags from form
            tags_raw = request.form.get('tags', '').strip()
            tag_names = [t.strip() for t in tags_raw.split(',') if t.strip()]

            # resolve or create tags
            tags = []
            for name in tag_names:
                tag = Tag.query.filter_by(name=name).first()
                if not tag:
                    tag = Tag(name=name)
                    db.session.add(tag)
                    db.session.flush()
                tags.append(tag)

            quote.tags = tags

            quote.status = ReviewStatus.APPROVED

        db.session.commit()
        return redirect(url_for('review.index'))

    return render_template('quote_review.html', quote=quote)


@review_bp.route('/related_quote/<int:id>', methods=['GET', 'POST'])
def review_related_quote(id):
    related = RelatedMetaQuote.query.get_or_404(id)

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'approve':
            related.status = ReviewStatus.APPROVED
            related.reviewed_by = current_user

        elif action == 'reject':
            related.status = ReviewStatus.REJECTED
            related.reviewed_by = current_user

        db.session.commit()
        return redirect(url_for('review.index'))

    meta_quote_a = related.meta_quote_a.get_latest()
    meta_quote_b = related.meta_quote_b.get_latest()

    return render_template(
        'related_quote_review.html',
        related=related,
        meta_quote_a=meta_quote_a,
        meta_quote_b=meta_quote_b,
    )


@review_bp.route('/quote_request/<int:id>/delete', methods=['POST'])
def delete_quote_request(id):
    req = QuoteRequest.query.get_or_404(id)
    db.session.delete(req)
    db.session.commit()
    flash('QuoteRequest wurde gelöscht.', 'success')
    return redirect(url_for('review.index'))


@review_bp.route('/tags', methods=['GET', 'POST'])
def review_tags():
    tags = Tag.query.all()

    if request.method == 'POST':
        for tag in tags:
            new_category = request.form.get(f'category_{tag.id}', '').strip()

            if new_category not in TagCategory._value2member_map_:
                continue

            # TODO: add enum value to category field of tag
            tag.category = TagCategory(new_category)
            db.session.commit()

        flash('Kategorien wurden aktualisiert.', 'success')
        return redirect(url_for('review.review_tags'))

    return render_template('tag_review.html', tags=tags, categories=TagCategory)
