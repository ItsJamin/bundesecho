from . import db  # import the main db instance


class VisitStat(db.Model):  # use the main db instance
    __bind_key__ = 'stats'  # specify the bind key for this model
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(20), nullable=False)
    path = db.Column(db.String(200), nullable=False)
    query_params = db.Column(db.Text, nullable=True)
    date = db.Column(db.Date, nullable=False)
    count = db.Column(db.Integer, default=1)

    __table_args__ = (
        db.UniqueConstraint(
            'session_id',
            'path',
            'query_params',
            'date',
            name='unique_session_path_query_date',
        ),
    )
