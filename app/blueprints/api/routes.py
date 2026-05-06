from datetime import datetime

from flask import Blueprint, jsonify, request
from werkzeug.security import check_password_hash

from app import db
from app.about_models import APIToken
from app.models import MetaQuote, quote_hashs


api_bp = Blueprint('api', __name__,  url_prefix='/api')



@api_bp.before_request
def require_token():
    token = request.headers.get('X-API-KEY')

    if not token:
        return jsonify({"error": "Invalid API token"}), 403

    matching_token = None

    all_tokens = APIToken.query.all()

    for t in all_tokens:
        if check_password_hash(t.token_hash, token):
            matching_token = t
            break

    if not matching_token:
        return jsonify({"error": "Invalid API token"}), 403

    if matching_token.is_expired():
        return jsonify({"error": "API token has expired"}), 403

    matching_token.last_used_at = datetime.utcnow()
    db.session.commit()

@api_bp.route('/q/<hash_id>', methods=['GET'])
def quote_detail(hash_id):
    try:
        meta_quote_id = quote_hashs.decode(hash_id)[0]
        meta_quote = MetaQuote.query.get_or_404(meta_quote_id)
    except:
        return jsonify({"error": "invalid quote"}), 404

    quote = meta_quote.get_latest()
    person = quote.meta_person.get_latest()

    common_tags = []
    for tag in quote.tags:
        if tag in person.tags:
            common_tags.append(tag.name)


    return jsonify({
        "quote": quote.to_dict(),
        "person": person.to_dict(),
        "tags": common_tags
        })
