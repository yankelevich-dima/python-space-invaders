import asyncio
import json

from autobahn.asyncio.websocket import WebSocketServerProtocol, WebSocketServerFactory

from game import Game


class GameServerProtocol(WebSocketServerProtocol):

    def onConnect(self, request):
        print('Connected with {}'.format(request.peer))

    def onOpen(self):
        print('Opened')

    async def onMessage(self, payload, isBinary):
        if not isBinary:
            request = json.loads(payload.decode('utf8'))

            if request['type'] == 'run_game':
                self.Game = Game(self)
                self.Game.run()
            elif request['type'] == 'player_event':
                self.Game.handle_event(request['message'])

    def onClose(self, wasClean, code, reason):
        if reason:
            self.Game.end_game('Game was crashed unexpectedly')
            print(reason)

if __name__ == '__main__':

    factory = WebSocketServerFactory(u'ws://0.0.0.0:9000')
    factory.protocol = GameServerProtocol

    loop = asyncio.get_event_loop()
    coro = loop.create_server(factory, '0.0.0.0', 9000)
    server = loop.run_until_complete(coro)

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.close()
        loop.close()
