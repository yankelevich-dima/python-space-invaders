import getpass
import argparse
import requests
import logging

from models import Game

from config import SERVER_URI, LOGGER


class APIConnectorException(BaseException):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return 'APIConnectorException {}'.format(self.message)


class APIConnector(object):

    @staticmethod
    def registration():
        username = input('Login: ')
        password = getpass.getpass()
        repeated_password = getpass.getpass('Repeat your password: ')
        if password == repeated_password:
            credentials = {
                'username': username,
                'password': password,
            }
            try:
                response = requests.post('{}/api/v1/registration/'.format(SERVER_URI), data=credentials)
                if response.status_code == requests.codes.ok:
                    if response.json()['status'] == 'ok':
                        LOGGER.info('Have a nice game')
                    elif response.json()['status'] == 'failed':
                        raise APIConnectorException(response.json()['message'])
                else:
                    raise APIConnectorException(response.text)
            except requests.exceptions.ConnectionError as e:
                raise APIConnectorException(e)

    @staticmethod
    def login():
        username = input('Login: ')
        password = getpass.getpass()
        credentials = {
            'username': username,
            'password': password,
        }
        try:
            response = requests.post('{}/api/v1/login/'.format(SERVER_URI), data=credentials)
            if response.status_code == requests.codes.ok:
                if response.json()['status'] == 'ok':
                    LOGGER.info('Have a nice game')
                elif response.json()['status'] == 'failed':
                    raise APIConnectorException(response.json()['message'])
            else:
                raise APIConnectorException(response.text)
        except requests.exceptions.ConnectionError as e:
            raise APIConnectorException(e)

    @staticmethod
    def send_game_results(username, score):
        credentials = {
            'username': username,
            'score': score,
        }
        try:
            response = requests.post('{}/api/v1/game_result/'.format(SERVER_URI), data=credentials)
            if response.status_code == requests.codes.ok:
                # TODO: log as info
                LOGGER.info('Score has been saved')
        except requests.exceptions.ConnectionError as e:
            raise APIConnectorException(e)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--login', action='store_true', help='Login')
    parser.add_argument('--register', action='store_true', help='Registration')
    parser.add_argument('--debug', action='store_true', help='Debug Mode')

    args = parser.parse_args()

    # Run game in debug mode
    if args.debug:
        LOGGER.setLevel(logging.DEBUG)

    elif args.login:
        LOGGER.setLevel(logging.INFO)
        try:
            APIConnector.login()
        except APIConnectorException as e:
            LOGGER.error(e)
            raise SystemExit
    elif args.register:
        LOGGER.setLevel(logging.INFO)
        try:
            APIConnector.registration()
        except APIConnectorException as e:
            LOGGER.error(e)
            raise SystemExit

    game = Game(args.debug)
    score = game.run()
    LOGGER.info('Your score: {} points'.format(score))
