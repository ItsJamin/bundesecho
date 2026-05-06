
import secrets
from datetime import datetime

from werkzeug.security import generate_password_hash

from . import db


class InfoNews(db.Model):
    __bind_key__ = 'about'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date = db.Column(db.Date, nullable=False)

# API stuff
class APIToken(db.Model):
    __bind_key__ = 'about'

    id = db.Column(db.Integer, primary_key=True)
    token_hash = db.Column(db.String(128), unique=True, nullable=False)

    name = db.Column(db.String(50), nullable=True)
    last_used_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)

    def is_expired(self):
        if self.expires_at and self.expires_at < datetime.utcnow():
            return True
        return False

    def __repr__(self):
        return f'<APIToken {self.name or "unnamed"}>'

def generate_new_token(token_name="Default Token", expires_in_days=None):
    """Helper function to create a new token.
    Returns the RAW token (to show the user once) and saves the HASH to the DB.
    """
    raw_token = secrets.token_urlsafe(32)

    hashed_token = generate_password_hash(raw_token)

    expiry = None
    if expires_in_days:
        from datetime import timedelta
        expiry = datetime.utcnow() + timedelta(days=expires_in_days)

    new_token = APIToken(
        token_hash=hashed_token,
        name=token_name,
        expires_at=expiry
    )

    db.session.add(new_token)
    db.session.commit()

    return raw_token
