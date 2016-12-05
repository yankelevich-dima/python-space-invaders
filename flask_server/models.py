import hashlib
import datetime

from sqlalchemy import exc

from app import db


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True)
    password = db.Column(db.String)
    registration_date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    scores = db.Column(db.Integer, default=0)

    def __init__(self, username, password):
        self.username = username
        self.password = hashlib.md5(password.encode('utf-8')).hexdigest()

    def save_to_db(self):
        try:
            db.session.add(self)
            db.session.commit()
            return {
                'status': 'ok',
                'message': 'user successfully added'
            }
        except exc.IntegrityError:
            db.session.rollback()
            return {
                'status': 'failed',
                'message': 'user already exists',
            }

    def update_score(self, score):
        self.scores += score
        db.session.commit()

    @staticmethod
    def get_user_by_username(username):
        return User.query.filter_by(username=username).first()

    @staticmethod
    def check_user_login(username, password):
        user = User.get_user_by_username(username)
        if user is None:
            return {
                'status': 'failed',
                'message': 'user "{}" not exists'.format(username),
            }
        elif user.password == hashlib.md5(password.encode('utf-8')).hexdigest():
            return {
                'status': 'ok',
                'message': 'login and password are correct',
            }
        else:
            return {
                'status': 'failed',
                'message': 'incorrect password',
            }
