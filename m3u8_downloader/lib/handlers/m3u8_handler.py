import json, uuid, os
import tornado.web
import tornado.gen
from ..constants import LogMsg, VIDEO_ROOT_DIR

class M3u8Handler(tornado.web.RequestHandler):
    lock = None
    file_downloader = None
    m3u8_processor = None
    handle_message = lambda x: None

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
        cls.handle_message = handle_message_func
        return cls

    # 接收：{"m3u8_url":"http://xxx/xx.m3u8?xxx"}
    # 返回：{"msg":"busy/fail/success","info":{}}
    #       "info": {"task_id":xx, "m3u8_name":xx, "http_prefix":xx, "video_name":xx "segment_states":[], "segment_durations":[], "logs": [], "task_status":xx}
    @tornado.gen.coroutine
    def post(self):
        request = json.loads(self.request.body.decode())
        m3u8_url = request["m3u8_url"]
        if self.lock.is_locked():
            response = {"msg":"busy"}
            self.write(json.dumps(response))
            return
        self.lock.set(True)
        try:
            info = yield self.download_and_parse(m3u8_url)
        except:
            response = {"msg":"fail"}
            self.write(json.dumps(response))
            return
        else:
            http_prefix = info["http_prefix"]
            m3u8_name = info["m3u8_name"]
            m3u8_basename = m3u8_name.split(".")[0]
            video_name = m3u8_basename + ".mp4"
            task_id = "".join(str(uuid.uuid4()).split("-"))
            log = {"msg":LogMsg.PARSE_SUCCESS, "info":{"file_name":m3u8_name, "http_prefix":http_prefix, "url":m3u8_url}}
            info.update({"task_id":task_id, "video_name":video_name, "logs":[log], "task_status":"prepare"})
            response = {"msg":"success", "info":info}
            self.write(json.dumps(response))
        finally:
            self.lock.set(False)
            self.finish()
    
    @tornado.gen.coroutine
    def download_and_parse(self, m3u8_url):
        http_prefix, m3u8_name = self.m3u8_processor.parse_url(m3u8_url)
        m3u8_basename = m3u8_name.split(".")[0]
        temp_dir = os.path.join(VIDEO_ROOT_DIR, "temp", m3u8_basename)
        m3u8_path = os.path.join(temp_dir, m3u8_name)
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        yield self.file_downloader.async_download(m3u8_url, m3u8_path)
        segment_durations = self.m3u8_processor.parse_file(m3u8_path)
        segment_states = {}
        for segment_name in segment_durations:
            segment_path = os.path.join(temp_dir, segment_name)
            segment_states[segment_name] = 2 if os.path.exists(segment_path) else 0
        info = {"m3u8_name":m3u8_name, "http_prefix":http_prefix, "segment_states":segment_states, "segment_durations":segment_durations}
        return info