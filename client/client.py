from autobahn.asyncio.websocket import WebSocketClientProtocol, WebSocketClientFactory
import asyncio
import time
import sys

from game import Game
from login_interface import RequestInterface

import json


class GameClientProtocol(WebSocketClientProtocol):

    def onConnect(self, response):
        print('Server connected: {0}'.format(response.peer))

    def onOpen(self):
        self.Game = None
        RequestInterface(self).run()

    def onMessage(self, payload, isBinary):
        if not isBinary:
            request = json.loads(payload.decode('utf8'))

            if request['type'] == 'auth_error':
                print(request['message'])
                RequestInterface(self).run()

            if request['type'] == 'game_action':
                if self.Game is None:
                    self.run_game()
                self.Game.last_frames.append({
                    'client_time': time.time(),
                    'size': sys.getsizeof(payload)
                })
                self.Game.handle_event(request['message'])

            if request['type'] == 'game_over':
                self.Game.game_over(request['message'])

    def run_game(self):
        self.Game = Game(self, debug=False)
        self.Game.run()
        self.loop = asyncio.get_event_loop()
        self.ping_server()
        self.latency = 0

    def ping_server(self):
        current_time = str(time.time()).encode('utf8')
        self.sendPing(current_time)

    def onPong(self, payload):
        current_time = time.time()
        self.latency = int((current_time - float(payload)) * 10 ** 3)
        self.loop.call_later(1 / 5, self.ping_server)

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


if __name__ == '__main__':
    GameClient().run()
