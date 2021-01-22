import json, asyncio
import tornado.websocket

class WsHandler(tornado.websocket.WebSocketHandler):
    conns = set()

    @classmethod
    def send(cls, data):
        try:
            loop = asyncio.get_event_loop()
        except:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        for conn in cls.conns:
            conn.write_message(json.dumps(data))

    def open(self):
        self.conns.add(self)
        print("new websocket established.")
        self.write_message(json.dumps({"msg":"websocket_connected"}))
        
    def on_message(self, message):
        print(message)

    def on_close(self):
        print("websocket closed.")
        if self in self.conns:
            self.conns.remove(self)