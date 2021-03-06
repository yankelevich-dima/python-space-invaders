import hashlib
import datetime

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy import exc
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

import config

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    password = Column(String)
    registration_date = Column(DateTime, default=datetime.datetime.utcnow)
    scores = Column(Integer, default=0)

    def __init__(self, username, password):
        self.username = username
        self.password = hashlib.md5(password.encode('utf-8')).hexdigest()

    @staticmethod
    def get_session():
        Session = sessionmaker(bind=config.SQLALCHEMY_ENGINE)
        session = Session()
        return session

    def save_to_db(self):
        session = User.get_session()
        try:
            session.add(self)
            session.commit()
            return self
        except exc.IntegrityError:
            session.rollback()
            return
        finally:
            session.close()

    def update_highscore(self, score):
        session = User.get_session()
        try:
            session.add(self)
            self.scores = max(self.scores, score)
            session.add(self)
            session.commit()
        finally:
            session.close()

    @staticmethod
    def get_user_by_username(username):
        session = User.get_session()
        try:
            user = session.query(User).filter_by(username=username).first()
            return user
        finally:
            session.close()

    @staticmethod
    def check_user_login(username, password):
        user = User.get_user_by_username(username)
        if user is not None and user.password == hashlib.md5(password.encode('utf-8')).hexdigest():
            return user
