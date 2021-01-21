import os
from processors.file_downloader import FileDownloader
from processors.m3u8_processor import M3u8Processor
from processors import logger

file_downloader = FileDownloader(logger.log)
m3u8_processor = M3u8Processor(logger.log)

def execute(remote_url, save_dir, video_base_name = None):
    http_prefix, m3u8_name = m3u8_processor.parse_url(remote_url)
    m3u8_basename = m3u8_name.split(".")[0]

    if video_base_name == None:
        video_base_name = m3u8_basename
    video_name = video_base_name + ".mp4"

    print("开始下载<%s>"%video_name)

    temp_dir = os.path.join(save_dir, video_base_name, "temp")
    m3u8_path = os.path.join(temp_dir, m3u8_name)
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    file_downloader.download(remote_url, m3u8_path)
    segment_durations = m3u8_processor.parse_file(m3u8_path)

    download_infos = []
    for segment_name in segment_durations:
        segment_url = http_prefix + segment_name
        segment_path = os.path.join(temp_dir, segment_name)
        download_info = (segment_url, segment_path)
        download_infos.append(download_info)
    file_downloader.batch_download(download_infos)

    segment_paths = [download_info[1] for download_info in download_infos]
    video_export_path = os.path.join(save_dir, video_base_name, video_name)
    m3u8_processor.merge_segments(segment_paths, video_export_path)

    print("<%s>下载完成！"%video_name)



def batch(download_infos, save_dir):
    for download_info in download_infos:
        try:
            if isinstance(download_info, str):
                remote_url = download_info
                execute(remote_url, save_dir)
            elif len(download_info) == 1:
                remote_url = download_info[0]
                execute(remote_url, save_dir)
            else:
                remote_url, video_name = download_info[:2]
                execute(remote_url, save_dir, video_name)
        except:
            print("<%s>下载失败！"%remote_url)
    print("所有任务结束！")