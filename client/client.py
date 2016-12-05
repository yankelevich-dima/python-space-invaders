from autobahn.asyncio.websocket import WebSocketClientProtocol, WebSocketClientFactory
import asyncio
import time
import sys
import ntplib

from game import Game

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

    async def onMessage(self, payload, isBinary):
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
                base_time = ntplib.NTPClient().request('europe.pool.ntp.org', version=3).tx_time
                client_offset = time.time() - base_time
                self.Game.syncronize_time(request['base_time'], request['base_time_offset'], client_offset)

    def onClose(self, wasClean, code, reason):
        if reason:
            print(reason)
        loop.stop()


if __name__ == '__main__':

    # TODO: ip and port to config
    factory = WebSocketClientFactory(u'ws://127.0.0.1:9000')
    factory.protocol = GameClientProtocol

    loop = asyncio.get_event_loop()
    coro = loop.create_connection(factory, '193.124.177.175', 9003)
    loop.run_until_complete(coro)

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        loop.close()
