import asyncio
import json
from autobahn.asyncio.websocket import WebSocketServerProtocol, WebSocketServerFactory

from game import Game
from models import User


class GameServerProtocol(WebSocketServerProtocol):

    def onConnect(self, request):
        self.Game = None
        print('Connected with {}'.format(request.peer))

    def onOpen(self):
        print('Opened')

    def opPing(self, payload):
        if self.state == WebSocketServerProtocol.STATE_OPEN:
            self.sendPong(payload)

    async def onMessage(self, payload, isBinary):
        if not isBinary:
            request = json.loads(payload.decode('utf8'))

            if request['type'] == 'login':
                user = User.check_user_login(request['username'], request['password'])
                if not user:
                    self.sendMessage(json.dumps({
                        'type': 'auth_error',
                        'message': 'Wrong login or password'
                    }).encode('utf8'))
                else:
                    self.Game = Game(self, user)
                    self.Game.run()

            elif request['type'] == 'registration':
                user = User(request['username'], request['password']).save_to_db()
                if not user:
                    self.sendMessage(json.dumps({
                        'type': 'auth_error',
                        'message': 'User already exists'
                    }).encode('utf8'))
                else:
                    print(user)
                    self.Game = Game(self, user)
                    self.Game.run()

            elif request['type'] == 'player_event':
                self.Game.handle_event(request['message'])

    def onClose(self, wasClean, code, reason):
        if reason:
            if self.Game is not None:
                self.Game.end_game('Game was crashed unexpectedly', wasClean=False)
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
