from autobahn.asyncio.websocket import WebSocketClientProtocol, WebSocketClientFactory
import asyncio
import time
import sys
import ntplib
import requests

from game import Game
from login_interface import RequestInterface

from config import SERVER_URI
import json


class GameClientProtocol(WebSocketClientProtocol):

    def onOpen(self):
        data = {
            'type': 'run_game'
        }
        self.sendMessage(json.dumps(data).encode('utf8'))
        self.Game = Game(self, debug=False)
        self.Game.run()

    def onConnect(self, response):
        print('Server connected: {0}'.format(response.peer))

    def onMessage(self, payload, isBinary):
        if not isBinary:
            request = json.loads(payload.decode('utf8'))
            if request['type'] == 'game_action':
                self.Game.last_frames.append({
                    'client_time': time.time(),
                    'size': sys.getsizeof(payload),
                    'server_time': float(request['server_time'])
                })
                self.Game.handle_event(request['message'])
            if request['type'] == 'time_sync':
                offset = ntplib.NTPClient().request('europe.pool.ntp.org', version=3).offset
                self.Game.syncronize_time(request['offset'], offset)
            if request['type'] == 'game_over':
                self.Game.game_over(request['message'])

    def onClose(self, wasClean, code, reason):
        if reason:
            print(reason)
        raise KeyboardInterrupt


class GameClient(object):

    def __init__(self):
        # TODO: ip and port to config
        self.factory = WebSocketClientFactory(u'ws://127.0.0.1:9000')
        self.factory.protocol = GameClientProtocol

    def run(self):
        self.loop = asyncio.get_event_loop()
        coro = self.loop.create_connection(self.factory, '193.124.177.175', 9003)
        self.loop.run_until_complete(coro)

        try:
            self.loop.run_forever()
        except KeyboardInterrupt:
            pass
        finally:
            self.loop.close()


class APIConnectorException(BaseException):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return 'APIConnectorException {}'.format(self.message)


class APIConnector(object):

    @staticmethod
    def registration(username, password):
        try:
            credentials = {
                'username': username,
                'password': password,
            }
            response = requests.post('{}/api/v1/registration/'.format(SERVER_URI), data=credentials)
            if response.status_code == requests.codes.ok:
                if response.json()['status'] == 'ok':
                    pass
                elif response.json()['status'] == 'failed':
                    raise APIConnectorException(response.json()['message'])
            else:
                raise APIConnectorException(response.text)
        except requests.exceptions.ConnectionError as e:
            raise APIConnectorException(e)

    @staticmethod
    def login(username, password):
        credentials = {
            'username': username,
            'password': password,
        }
        try:
            response = requests.post('{}/api/v1/login/'.format(SERVER_URI), data=credentials)
            if response.status_code == requests.codes.ok:
                if response.json()['status'] == 'ok':
                    pass
                elif response.json()['status'] == 'failed':
                    raise APIConnectorException(response.json()['message'])
            else:
                raise APIConnectorException(response.text)
        except requests.exceptions.ConnectionError as e:
            raise APIConnectorException(e)

if __name__ == '__main__':

    while 1:
        username, password, auth_type = RequestInterface().run()
        if auth_type == 'login':
            try:
                APIConnector.login(username, password)
            except APIConnectorException:
                continue
        elif auth_type == 'registration':
            try:
                APIConnector.registration(username, password)
            except APIConnectorException:
                continue
        break

    GameClient().run()
