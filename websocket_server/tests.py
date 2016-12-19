import unittest
import hashlib

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import User, Base
import config


class UserModelTestCase(unittest.TestCase):

    def setUp(self):
        self.engine = create_engine('sqlite://')
        config.SQLALCHEMY_ENGINE = self.engine
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine, expire_on_commit=False)
        self.session = Session()

    def tearDown(self):
        Base.metadata.drop_all(self.engine)
        self.session.close()

    def test_correct_init(self):
        username = 'username'
        password = 'passwd'
        password_hashed = hashlib.md5(password.encode('utf-8')).hexdigest()
        user = User(username, password)
        self.assertEqual(user.password, password_hashed)

    def test_correct_adding_answer(self):
        username = 'username'
        password = 'passwd'

        correct_user = User(username, password)
        duplicated_user = User(username, password)

        correct_result = correct_user.save_to_db()
        duplicated_result = duplicated_user.save_to_db()

        self.assertEqual(correct_result, correct_user)
        self.assertEqual(duplicated_result, None)

    def test_correct_score_update(self):
        username = 'username'
        password = 'passwd'
        score_count = 10
        user = User(username, password)

        user.save_to_db()
        self.assertEqual(User.get_user_by_username(username).scores, 0)

        user.update_highscore(score_count)
        self.assertEqual(User.get_user_by_username(username).scores, score_count)

        user.update_highscore(score_count)
        self.assertEqual(User.get_user_by_username(username).scores, score_count)


if __name__ == '__main__':
    unittest.main()
