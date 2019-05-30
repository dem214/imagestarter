import hashlib
from datetime import datetime
from flask import request
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from . import db, login_manager

class Permission:
    COMMENT = 1
    WRITE = 2
    MODERATE = 4
    ADMIN = 8

class User(UserMixIn, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    email = db.Column(db.String(64), unique=True)
    confirmed = db.Column(db.Boolean, default=False)
    permission = db.Column(db.Integer)
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    avatar_hash = db.Column(db.String(32))
    member_since = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    about_me = db.Column(db.Text)

    def can(self, perm):
        return self.permission & perm == perm

    def reset_permission(self, perm):
        self.permission = 0
        db.session.add(self)
        db.session.commit()

    def add_permission(self, perm):
        if not self.can(perm):
            self.permission += perm
            db.session.add(self)
            db.session.commit()

    def remove_permission(self, perm):
        if self.can(perm):
            self.permission -= perm
            db.session.add(self)
            db.session.commit()

    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)
        db.session.commit()

    def change_email(self, token):
        self.email = new_email
        self.avatar_hash = self.gravatar_hash()
        db.session.add(self)
        db.session.commit()
        return True

    def gravatar_hash(self):
        return hashlib.md5(self.email.lower().encode('utf-8')).hexdigest()

    def gravatar(self, size=100, default='identicon', rating='g'):
        if request.is_secure:
            url = 'https://www.gravatar.com/avatar'
        else:
            url = 'http://www.gravatar.com/avatar'
        hash = self.avatar_hash or self.gravatar_hash()
        return f'{url}/{hash}?s={size}&d={default}&r={rating}'

    def generate_auth_token(self, expiration):
        s = Serializer(current_app.config['SECRET_KEY'],
            expires_in=expiration)
        return s.dumps({'id':self.id}).decode('utf-8')

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return None
        return User.query.get(data['id'])

class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    comments = db.relationship('Comment', backref='post', lazy='dynamic')

class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))
