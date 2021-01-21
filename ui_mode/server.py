import os
import tornado.ioloop
import tornado.web
from lib.handlers.index_handler import IndexHandler
from lib.handlers.m3u8_handler import M3u8Handler
from lib.handlers.video_handler import VideoHandler
from lib.handlers.websocket_handler import WsHandler
from lib.processors.file_downloader import FileDownloader
from lib.processors.m3u8_processor import M3u8Processor
from lib.processors.simple_lock import SimpleLock

settings = {
    "static_path": os.path.join(".", "statics"),
    "static_url_prefix": "/static/",
    "template_path": os.path.join(".", "templates"),
    "debug":True,
    "serve_traceback":True,
    # "default_handler_class":None,
    # "log_function": None,
}

handlerMapping = {
    r"/": IndexHandler,
    r"/m3u8":M3u8Handler,
    r"/v":VideoHandler,
    r"/ws":WsHandler,
}


# message:{"msg":xx, "info":{}}
# ws_send:{"msg":xx, "task_id":xx, "info":{}}
def handle_message(message):
    if VideoHandler.get_task() == None:
        return
    task_id = VideoHandler.get_task().get("task_id")
    VideoHandler.update_task(message)
    ws_message = message.copy()
    ws_message.update({"task_id":task_id})
    WsHandler.send(ws_message)

if __name__ == "__main__":

    file_downloader = FileDownloader(handle_message)
    m3u8_processor = M3u8Processor(handle_message)
    lock = SimpleLock(False)
    M3u8Handler.set_file_downloader(file_downloader).set_m3u8_processor(m3u8_processor).set_lock(lock).set_handle_message(handle_message)
    VideoHandler.set_file_downloader(file_downloader).set_m3u8_processor(m3u8_processor).set_lock(lock).set_handle_message(handle_message)

    app = tornado.web.Application(handlerMapping.items(), **settings)
    app.listen(80)
    tornado.ioloop.IOLoop.current().start()
