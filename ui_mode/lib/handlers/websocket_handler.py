import json, asyncio
import tornado.websocket

class WsHandler(tornado.websocket.WebSocketHandler):
    conns = set()

    @classmethod
    def send(cls, data):
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