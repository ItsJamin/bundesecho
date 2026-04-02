import enum

from datetime import datetime

from flask_login import UserMixin
from hashids import Hashids
from sqlalchemy.orm import aliased
from sqlalchemy.sql import func
from werkzeug.security import check_password_hash, generate_password_hash

from . import db


person_hashs = Hashids(min_length=6, salt='!wshmfw1k')
quote_hashs = Hashids(min_length=6, salt='bAwIVSp_')


class ReviewStatus(enum.Enum):
    PENDING = 'PENDING'
    APPROVED = 'APPROVED'
    REJECTED = 'REJECTED'


# Main Info Models

quote_tag = db.Table(
    'quote_tag',
    db.Column(
        'quote_id',
        db.Integer,
        db.ForeignKey('quote.id', name='fk_quote_tag_quote_id'),
        primary_key=True,
    ),
    db.Column(
        'tag_id',
        db.Integer,
        db.ForeignKey('tag.id', name='fk_quote_tag_tag_id'),
        primary_key=True,
    ),
    db.Column('order', db.Integer, default=0),
)


class MetaPerson(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    persons = db.relationship('Person', backref='meta', lazy=True)

    def get_latest(self, status=ReviewStatus.APPROVED):
        return (
            Person.query
            .filter_by(meta_person_id=self.id, status=status)
            .order_by(Person.date_created.desc())
            .first()
        )


class Person(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(300), nullable=True)
    image_src = db.Column(db.String(300), nullable=True)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    meta_person_id = db.Column(
        db.Integer, db.ForeignKey('meta_person.id'), nullable=False
    )
    status = db.Column(db.Enum(ReviewStatus), default=ReviewStatus.PENDING)
    submitted_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    submitted_by = db.relationship('User', foreign_keys=[submitted_by_id])
    reviewed_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    reviewed_by = db.relationship('User', foreign_keys=[reviewed_by_id])


class MetaQuote(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    def get_latest(self, status=ReviewStatus.APPROVED):
        return (
            Quote.query
            .filter_by(meta_quote_id=self.id, status=status)
            .order_by(Quote.date_created.desc())
            .first()
        )


class Quote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    context = db.Column(db.Text, nullable=True)
    source = db.Column(db.String(255))
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    date_said = db.Column(db.DateTime, nullable=True)

    meta_person_id = db.Column(
        db.Integer, db.ForeignKey('meta_person.id'), nullable=False
    )
    meta_person = db.relationship('MetaPerson', backref=db.backref('quotes', lazy=True))

    tags = db.relationship(
        'Tag',
        secondary=quote_tag,
        backref=db.backref('quotes', lazy='dynamic'),
        order_by=quote_tag.c.order,
    )

    meta_quote_id = db.Column(
        db.Integer, db.ForeignKey('meta_quote.id'), nullable=False
    )

    status = db.Column(db.Enum(ReviewStatus), default=ReviewStatus.PENDING)

    submitted_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    submitted_by = db.relationship('User', foreign_keys=[submitted_by_id])

    reviewed_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    reviewed_by = db.relationship('User', foreign_keys=[reviewed_by_id])


class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)


# User Models
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default='user')  # 'user', 'moderator', 'admin'
    is_active = db.Column(db.Boolean, default=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


class RelatedMetaQuote(db.Model):
    __tablename__ = 'related_meta_quotes'

    id = db.Column(db.Integer, primary_key=True)
    meta_quote_a_id = db.Column(
        db.Integer, db.ForeignKey('meta_quote.id'), nullable=False
    )
    meta_quote_b_id = db.Column(
        db.Integer, db.ForeignKey('meta_quote.id'), nullable=False
    )
    status = db.Column(
        db.Enum(ReviewStatus), nullable=False, default=ReviewStatus.PENDING
    )

    meta_quote_a = db.relationship(
        'MetaQuote', foreign_keys=[meta_quote_a_id], backref='related_from'
    )
    meta_quote_b = db.relationship(
        'MetaQuote', foreign_keys=[meta_quote_b_id], backref='related_to'
    )


class QuoteRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)


# ----- helping functions -----


def get_latest_approved_quotes_query():
    QuoteAlias = aliased(Quote)

    subq = (
        db.session
        .query(Quote.meta_quote_id, func.max(Quote.date_created).label('max_created'))
        .filter(Quote.status == ReviewStatus.APPROVED)
        .group_by(Quote.meta_quote_id)
        .subquery()
    )

    query = db.session.query(QuoteAlias).join(
        subq,
        (QuoteAlias.meta_quote_id == subq.c.meta_quote_id)
        & (QuoteAlias.date_created == subq.c.max_created),
    )

    return query, QuoteAlias
