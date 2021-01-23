import os, asyncio
from functools import partial
import aiohttp
from threading import Thread
from concurrent.futures import ThreadPoolExecutor
from ..constants import LogMsg
from .coroutine_pool import AsyncPool

SINGLE_DOWNLOAD_RETRY = 3
BATCH_DOWNLOAD_RETRY = 3
MAX_DOWNLOAD_CONNECTION_COUNT = 123

class FileDownloader:
    def __init__(self, handle_message_func=print):
        self.handle_message = handle_message_func
        self.stop_flag = False
        self.coroutine_pool = None
    
    def set_stop_flag(self, flag):
        self.stop_flag = flag
    
    async def async_download(self, remote_url, file_save_path):
        if self.stop_flag:
            return
        file_name = os.path.basename(file_save_path)
        if os.path.exists(file_save_path):
            self.handle_message({"msg":LogMsg.FILE_EXIST, "info":{"file_name": file_name, "file_path": file_save_path}})
            return
        retry = 0
        while retry <= SINGLE_DOWNLOAD_RETRY:
            if retry > 0:
                self.handle_message({"msg":LogMsg.DOWNLOAD_FAIL, "info":{"file_name": file_name, "file_path": file_save_path, "retry": retry}})
            elif retry == 0:
                self.handle_message({"msg":LogMsg.DOWNLOADING, "info":{"file_name": file_name, "file_path": file_save_path}})
            timeout = aiohttp.ClientTimeout(total=30, sock_connect=5, sock_read=10)
            try:
                async with aiohttp.request("GET", remote_url, timeout=timeout) as resp:
                    data = await resp.read()
            except:
                retry += 1
            else:
                with open(file_save_path, "wb") as f:
                    f.write(data)
                self.handle_message({"msg":LogMsg.DOWNLOAD_SUCCESS, "info":{"file_name": file_name, "file_path": file_save_path}})
                return
            if self.stop_flag:
                break
        self.handle_message({"msg":LogMsg.DOWNLOAD_FAIL, "info":{"file_name": file_name, "file_path": file_save_path, "retry": -1}})
        raise Exception("<%s> download fails."%file_save_path)


    def download(self, remote_url, file_save_path):
        try:
            loop = asyncio.get_event_loop()
        except:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        task = asyncio.ensure_future(self.async_download(remote_url, file_save_path))
        loop.run_until_complete(task)


    def batch_download(self, download_infos):
        def download_callback(task, download_info, new_download_infos):
            if task.exception() != None:
                new_download_infos.append(download_info)
        
        if self.coroutine_pool == None:
            self.coroutine_pool = AsyncPool(MAX_DOWNLOAD_CONNECTION_COUNT, 2)
        retry = 0
        while retry <= BATCH_DOWNLOAD_RETRY:
            if retry > 0:
                file_paths = [download_info[1] for download_info in download_infos]
                file_names = [os.path.basename(file_path) for file_path in file_paths]
                self.handle_message({"msg":LogMsg.BATCH_DOWNLOAD_FAIL,"info":{"file_names":file_names, "file_paths":file_paths, "retry": retry}})
            new_download_infos = []
            for download_info in download_infos:
                remote_url, file_save_path = download_info
                self.coroutine_pool.submit(self.async_download, remote_url, file_save_path, callback=partial(download_callback, download_info = download_info, new_download_infos = new_download_infos))
            self.coroutine_pool.wait()
            if self.stop_flag:
                return
            download_infos = new_download_infos
            if len(download_infos) == 0:
                break
            else:
                retry += 1
        file_paths = [download_info[1] for download_info in download_infos]
        file_names = [os.path.basename(file_path) for file_path in file_paths]
        if len(file_names) > 0:
            self.handle_message({"msg":LogMsg.BATCH_DOWNLOAD_FAIL,"info":{"file_names":file_names, "file_paths":file_paths, "retry": -1}})
        else:
            self.handle_message({"msg":LogMsg.BATCH_DOWNLOAD_SUCCESS})