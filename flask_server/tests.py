import json
import unittest
from unittest.mock import patch
import hashlib

import requests
from flask import request

from app import app, db
from models import User
import views  # NOQA


class UserModelTestCase(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'

        db.session.close()
        db.drop_all()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

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

        correct_answer = {
            'status': 'ok',
            'message': 'user successfully added'
        }
        duplicated_answer = {
            'status': 'failed',
            'message': 'user already exists',
        }

        correct_result = correct_user.save_to_db()
        duplicated_result = duplicated_user.save_to_db()

        self.assertEqual(correct_answer, correct_result)
        self.assertEqual(duplicated_answer, duplicated_result)

    def test_correct_rollback(self):
        username = 'username'
        password = 'passwd'

        correct_user = User(username, password)
        duplicated_user = User(username, password)

        correct_user.save_to_db()
        # First user should be added
        self.assertIn(correct_user, db.session)

        duplicated_user.save_to_db()
        # And duplicated not
        self.assertNotIn(duplicated_user, db.session)

    def test_adding_multiply_users(self):

        user_1 = User('one', 'passwd')
        user_2 = User('two', 'passwd')

        user_1.save_to_db()
        user_2.save_to_db()

        self.assertIn(user_1, db.session)
        self.assertIn(user_2, db.session)

        self.assertIn(user_1, User.query.all())
        self.assertIn(user_2, User.query.all())

    def test_correct_score_update(self):
        username = 'username'
        password = 'passwd'
        score_count = 10
        user = User(username, password)

        user.save_to_db()
        self.assertEqual(User.get_user_by_username(username).scores, 0)

        user.update_score(score_count)
        self.assertEqual(User.get_user_by_username(username).scores, score_count)

        user.update_score(score_count)
        self.assertEqual(User.get_user_by_username(username).scores, score_count * 2)

    def test_check_user_login(self):
        username = 'username'
        password = 'passwd'
        fake_username = 'fake_username'
        fake_password = 'notpasswd'

        incorrect_password_answer = {
            'status': 'failed',
            'message': 'incorrect password',
        }

        correct_password_anser = {
            'status': 'ok',
            'message': 'login and password are correct',
        }

        user_not_exists_answer = {
            'status': 'failed',
            'message': 'user "{}" not exists'.format(fake_username),
        }

        User(username, password).save_to_db()

        self.assertEqual(User.check_user_login(username, password), correct_password_anser)
        self.assertEqual(User.check_user_login(username, fake_password), incorrect_password_answer)
        self.assertEqual(User.check_user_login(fake_username, fake_password), user_not_exists_answer)


class ResponseTestCase(unittest.TestCase):

    def setUp(self):
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
        app.config['TESTING'] = True
        self.app = app.test_client()
        with app.app_context():
            db.session.close()
            db.drop_all()
            db.create_all()

    def tearDown(self):
        pass

    def test_api_post_only(self):
        response = self.app.get('/api/v1/login/')
        self.assertEqual(response.status_code, requests.codes.method_not_allowed)

        response = self.app.get('/api/v1/game_result/')
        self.assertEqual(response.status_code, requests.codes.method_not_allowed)

        response = self.app.get('/api/v1/registration/')
        self.assertEqual(response.status_code, requests.codes.method_not_allowed)

    def test_api_400_on_empty_post(self):
        response = self.app.post('/api/v1/login/')
        self.assertEqual(response.status_code, requests.codes.bad_request)

        response = self.app.post('/api/v1/game_result/')
        self.assertEqual(response.status_code, requests.codes.bad_request)

        response = self.app.post('/api/v1/registration/')
        self.assertEqual(response.status_code, requests.codes.bad_request)

    @patch('models.User.save_to_db')
    def test_register_new_user(self, mock_saving):
        credentials = {
            'username': 'username',
            'password': 'passwd'
        }

        mock_saving.return_value = {
            'status': 'ok'
        }

        with self.app as test_client:
            response = test_client.post('/api/v1/registration/', data=credentials)
            for key, value in credentials.items():
                self.assertEqual(request.form.get(key), value)
            self.assertEqual(response.status_code, requests.codes.ok)
            self.assertEqual('ok', json.loads(response.data.decode('utf-8'))['status'])
            mock_saving.assert_called_once_with()

    @patch('models.User.check_user_login')
    def test_correct_login(self, mock_login):
        credentials = {
            'username': 'username',
            'password': 'passwd'
        }

        mock_login.return_value = {
            'status': 'ok'
        }

        user = User(credentials['username'], credentials['password'])
        with self.app as test_client:
            user.save_to_db()
            response = test_client.post('/api/v1/login/', data=credentials)
            self.assertEqual(response.status_code, requests.codes.ok)
            self.assertEqual('ok', json.loads(response.data.decode('utf-8'))['status'])
            mock_login.assert_called_once_with(credentials['username'], credentials['password'])


if __name__ == '__main__':
    unittest.main()
