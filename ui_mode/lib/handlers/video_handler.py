import os, json, asyncio
from queue import Queue
from threading import Thread
from concurrent.futures import ThreadPoolExecutor
import tornado.web
from ..constants import LogMsg, VIDEO_ROOT_DIR

class VideoHandler(tornado.web.RequestHandler):
    # {"task_id":xx, "m3u8_name":xxx, "http_prefix":xxx, "video_name":xxx, "segment_states":{}, "segment_durations":{}, "logs":[], "task_status":xx}
    current_task = None

    lock = None
    file_downloader = None
    m3u8_processor = None
    handle_message = lambda x: None

    download_thread_pool = ThreadPoolExecutor(1,"segments-download-thread-")

    @classmethod
    def set_lock(cls, lock):
        cls.lock = lock
        return cls
    
    @classmethod
    def set_file_downloader(cls, file_downloader):
        cls.file_downloader = file_downloader
        return cls
    
    @classmethod
    def set_m3u8_processor(cls, m3u8_processor):
        cls.m3u8_processor = m3u8_processor
        return cls

    @classmethod
    def set_handle_message(cls, handle_message_func):
        cls.handle_message = lambda cc, message: handle_message_func(message)

    @classmethod
    def get_task(cls):
        return cls.current_task

    @classmethod
    def set_task(cls, task):
        cls.current_task = task

    @classmethod
    def is_task_stopping(cls):
        if cls.current_task == None:
            return False
        return cls.current_task.get("task_status") == "stopping"
    
    @classmethod
    def set_task_status(cls, task_status):
        if cls.current_task == None:
            return
        cls.current_task.update({"task_status":task_status})

    @classmethod
    def update_task(cls, message):
        if cls.current_task == None or cls.current_task.get("task_status") == "finished":
            return
        cls.current_task.get("logs").append(message)
        if message["msg"] == LogMsg.START_TASK:
            cls.current_task.update({"task_status": "running"})
        if message["msg"] == LogMsg.STOP_TASK:
            cls.current_task.update({"task_status": "stopping"})
        if message["msg"] == LogMsg.TASK_DONE:
            cls.current_task.update({"task_status": "finished"})
        if message["msg"] in [LogMsg.FILE_EXIST, LogMsg.DOWNLOAD_SUCCESS]:
            file_name = message["info"]["file_name"]
            if file_name in cls.current_task.get("segment_states").keys():
                cls.current_task.get("segment_states").update({file_name: 2})
        if message["msg"] == LogMsg.DOWNLOADING:
            file_name = message["info"]["file_name"]
            if file_name in cls.current_task.get("segment_states").keys():
                cls.current_task.get("segment_states").update({file_name: 1})
        if message["msg"] == LogMsg.DOWNLOAD_FAIL:
            file_name = message["info"]["file_name"]
            if file_name in cls.current_task.get("segment_states").keys():
                if "retry" in message["info"].keys() and message["info"]["retry"] > 0:
                    cls.current_task.get("segment_states").update({file_name: 1})
                else:
                    cls.current_task.get("segment_states").update({file_name: 0})


    # 接收：None
    # 返回：{"msg":"free/busy", "info":{}}
    #       "info": {"task_id":xx, "m3u8_name":xxx, "http_prefix":xxx, "video_name":xxx, "segment_states":{}, "segment_durations":{}, "logs":[], "task_status":xx}
    def get(self):
        if self.get_task() == None or self.get_task().get("task_status") == "finished":
            response = {"msg":"free"}
            self.write(json.dumps(response))
            return
        response = {"msg":"busy", "info":self.get_task()}
        self.write(json.dumps(response))


    # 接收：{"task_id":xx}
    # 返回：{"msg":"free/success/inconstant","info":{"stack_id":xx}}
    def put(self):
        if self.get_task() == None or self.get_task().get("task_status") == "finished":
            response = {"msg":"free"}
            self.write(json.dumps(response))
            return
        request = json.loads(self.request.body.decode())
        task_id = request["task_id"]
        if task_id != self.get_task().get("task_id"):
            response = {"res":"inconstant", "info":{"task_id":self.get_task().get("task_id")}}
            self.write(json.dumps(response))
            return
        if not self.get_task().get("task_status") == "stopping":
            self.set_task_status("stopping")
            self.file_downloader.set_stop_flag(True)
            self.get_task().get("logs").append({"msg":LogMsg.STOP_TASK})
        response = {"msg":"success", "info":{"task_id":task_id}}
        self.write(json.dumps(response))
        return


    # 接收：{"task_id":xx, "m3u8_name":xxx, "http_prefix":xxx, "video_name":xxx, "segment_durations":{}, "task_status":xx,"logs":[]}
    # 返回：{"msg":busy/success/fail, "info":{"task_id":xx, "segment_states":{}}
    def post(self):
        if self.lock.is_locked() or (self.get_task() != None and self.get_task().get("task_status") != "finished") :
            response = {"msg":"busy"}
            self.write(json.dumps(response))
            return
        request = json.loads(self.request.body.decode())
        if request["task_status"] != "prepare":
            response = {"msg":"fail"}
            self.write(json.dumps(response))
            return
        self.lock.set(True)
        try:
            segment_durations = request["segment_durations"]
            m3u8_basename = request["m3u8_name"].split(".")[0]
            temp_dir = os.path.join(VIDEO_ROOT_DIR, "temp", m3u8_basename)
            segment_states = {}
            for segment_name in segment_durations:
                segment_path = os.path.join(temp_dir, segment_name)
                segment_states[segment_name] = 2 if os.path.exists(segment_path) else 0
            request.update({"segment_states":segment_states, "task_status": "running"})
            self.set_task(request)
            self.get_task().get("logs").append({"msg":LogMsg.START_TASK})
            response = {"msg":"success", "info":{"task_id": request["task_id"], "segment_states":segment_states}}
            future = self.download_thread_pool.submit(self.download_and_merge, self.get_task())
            future.add_done_callback(self.download_and_merge_callback)
            self.write(json.dumps(response))
        except:
            self.set_task(None)
            self.lock.set(False)

    def download_and_merge(self, data):
        http_prefix = data["http_prefix"]
        segment_durations = data["segment_durations"]
        m3u8_basename = data["m3u8_name"].split(".")[0]
        temp_dir = os.path.join(VIDEO_ROOT_DIR, "temp", m3u8_basename)
        download_infos = []
        for segment_name in segment_durations:
            segment_url = http_prefix + segment_name
            segment_path = os.path.join(temp_dir, segment_name)
            download_info = (segment_url, segment_path)
            download_infos.append(download_info)
        try:
            self.file_downloader.batch_download(download_infos)
            if(self.is_task_stopping()):
                return
            segment_paths = [download_info[1] for download_info in download_infos]
            video_name = data["video_name"]
            video_export_path = os.path.join(VIDEO_ROOT_DIR, video_name)
            self.m3u8_processor.merge_segments(segment_paths, video_export_path)
        except:
            self.handle_message({"msg":LogMsg.MERGE_CANCEL, "info":{"file_name": video_name, "file_path": video_export_path}})
        finally:
            self.handle_message({"msg":LogMsg.TASK_DONE})
    
    
    def download_and_merge_callback(self, future):
        self.set_task(None)
        self.lock.set(False)
        self.file_downloader.set_stop_flag(False)