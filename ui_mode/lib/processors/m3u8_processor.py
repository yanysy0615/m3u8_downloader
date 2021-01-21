import re, os
from ..constants import LogMsg

class M3u8Processor:
    def __init__(self, handle_message_func=print):
        self.handle_message = handle_message_func

    def parse_url(self, m3u8_url):
        if "?" in m3u8_url:
            m3u8_url, _ = m3u8_url.split("?")
        match_result = re.match(r"(.*/)(.*\.m3u8)", m3u8_url)
        http_prefix = match_result.group(1)
        m3u8_name = match_result.group(2)
        return http_prefix, m3u8_name

    def parse_file(self, m3u8_path):
        segment_durations = dict()
        with open(m3u8_path, "r") as f:
            lines = f.readlines()
        for i in range(len(lines)):
            line = lines[i].strip()
            if not line.startswith("#EX"):
                segment_name = line
                previous_line =  lines[i-1].strip()
                match_result = re.match("#EXTINF:(.*),", previous_line)
                duration = float(match_result.group(1))
                duration = round(duration, 2)
                segment_durations[segment_name] = duration
        return segment_durations

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