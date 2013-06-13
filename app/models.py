from app import db
from flask.ext.login import UserMixin
from datetime import datetime

ROLE_USER = 0
ROLE_ADMIN = 1

STATUS_WAITING_FOR_CONFIRM = 0
STATUS_ACTIVE = 1

OP_CREATE = 0
OP_MODIFY = 1
OP_CHECKOUT = 2


tags = db.Table('tags',
                db.Column('tag_id', db.Integer, db.ForeignKey('tag.id')),
                db.Column('page_id', db.Integer, db.ForeignKey('page.id')))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), index=True, unique=True)
    password = db.Column(db.String(32))
    email = db.Column(db.String(120), unique=True)
    role = db.Column(db.SmallInteger, default=ROLE_USER)
    status = db.Column(db.SmallInteger, default=STATUS_WAITING_FOR_CONFIRM)

    logs = db.relationship('Log', backref='operator', lazy='dynamic')
    # marks = db.relationship('Mark', backref='marker', lazy='dynamic')

    def __init__(self, username, password, email, role=ROLE_USER, status=STATUS_WAITING_FOR_CONFIRM):
        self.username = username
        self.password = password
        self.email = email
        self.role = role
        self.status = status

    def __repr__(self):
        return '<User %r>' % self.username


class Page(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), unique=True)
    locked = db.Column(db.Boolean)
    pub_date = db.Column(db.DateTime)
    last_edit_date = db.Column(db.DateTime)
    score_avg = db.Column(db.Float)
    scorer_num = db.Column(db.Integer, default=0)
    score_5 = db.Column(db.Integer, default=0)
    score_4 = db.Column(db.Integer, default=0)
    score_3 = db.Column(db.Integer, default=0)
    score_2 = db.Column(db.Integer, default=0)
    score_1 = db.Column(db.Integer, default=0)

    tags = db.relationship('Tag', secondary=tags, backref='pages')
    logs = db.relationship('Log', backref='page', lazy='dynamic')
    marks = db.relationship('Mark', backref='page', lazy='dynamic')

    def __init__(self, title, locked=False):
        self.title = title
        self.locked = locked
        self.pub_date = self.last_edit_date = datetime.now()
        self.score_1 = 0
        self.score_2 = 0
        self.score_3 = 0
        self.score_4 = 0
        self.score_5 = 0
        self.scorer_num = 0
        self.score_avg = 0

    def __repr__(self):
        return '<Page %r>' % self.title


class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True)

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '<Tag %r>' % self.name


class Log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.DateTime)
    operation = db.Column(db.SmallInteger, default=OP_MODIFY)
    commitMSG = db.Column(db.String(300))
    commitSHA = db.Column(db.String(40))

    page_id = db.Column(db.Integer, db.ForeignKey('page.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, operator, page, operation, commitSHA, commitMSG):
        self.operator = operator
        self.page = page
        self.operation = operation
        self.commitSHA = commitSHA
        self.commitMSG = commitMSG
        self.time = datetime.now()

    def __repr__(self):
        return '<Log %r>' % self.commitSHA


class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    score = db.Column(db.SmallInteger)

    page_id = db.Column(db.Integer, db.ForeignKey('page.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<user:%d,page:%d,score:%d>' % (self.user_id, self.page_id, self.score)


class Mark(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    notify = db.Column(db.Boolean, default=False)

    page_id = db.Column(db.Integer, db.ForeignKey('page.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<user:%d,page:%d,score:%d>' % (self.user_id, self.page_id, self.score)
