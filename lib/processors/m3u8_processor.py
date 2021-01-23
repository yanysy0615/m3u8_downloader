import re, os, random
from ..constants import LogMsg
from . import m3u8

class M3u8Processor:
    def __init__(self, handle_message_func=print):
        self.handle_message = handle_message_func

    def parse_url(self, m3u8_url):
        temp_url = m3u8_url
        if "?" in temp_url:
            temp_url = temp_url.split("?")[0]
        match_res = re.match(r"(.*/)(.*?\.m3u8)", temp_url)
        base_uri = match_res.group(1)
        m3u8_name = match_res.group(2)
        result = m3u8.load(m3u8_url)
        if result.is_variant:
            new_url = result.playlists[0].absolute_uri
            return self.parse_url(new_url)
        else:
            segment_infos = []
            for i in range(len(result.segments)):
                segment = result.segments[i]
                url = base_uri + segment.uri
                name = "seg-%03d.ts"%(i+1)
                duration = segment.duration
                segment_infos.append((name, duration, url))
            return m3u8_name, segment_infos



    def merge_segments(self, segment_paths, video_export_path):
        video_name = os.path.basename(video_export_path)
        if os.path.exists(video_export_path):
            self.handle_message({"msg":LogMsg.FILE_EXIST, "info":{"file_name":video_name, "file_path":os.path.abspath(video_export_path)}})
            raise Exception("file already exists.")
        self.handle_message({"msg":LogMsg.MERGING, "info":{"file_name":video_name, "file_path":os.path.abspath(video_export_path)}})
        segment_paths.sort(key=lambda segment_path:int(re.match(r".*?(\d+)", os.path.basename(segment_path).split(".")[0]).group(1)))
        export_dir = os.path.dirname(video_export_path)
        if not os.path.exists(export_dir):
            os.makedirs(export_dir)
        with open(video_export_path, "wb") as v:
            for segment_path in segment_paths:
                with open(segment_path, "rb") as s:
                    sblock = s.read()
                    v.write(sblock)
        self.handle_message({"msg":LogMsg.MERGE_DONE, "info":{"file_name":video_name, "file_path":os.path.abspath(video_export_path)}})