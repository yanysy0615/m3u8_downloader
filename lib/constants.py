import os

VIDEO_ROOT_DIR = os.path.join(os.path.dirname(__file__), "..", "videos")

class LogMsg:
    PARSE_SUCCESS = "parse_success"
    
    START_TASK = "start_task"
    STOP_TASK = "stop_task"
    TASK_DONE = "task_done"

    FILE_EXIST = "file_exist"
    DOWNLOADING = "downloading"
    DOWNLOAD_SUCCESS = "download_success"
    DOWNLOAD_FAIL = "download_fail"
    BATCH_DOWNLOAD_SUCCESS = "batch_download_success"
    BATCH_DOWNLOAD_FAIL = "batch_download_fail"

    MERGING = "merging"
    MERGE_CANCEL = "merge_cancel"
    MERGE_DONE = "merge_done"