from .constants import LogMsg

def log(message):
    pass
    # if message["msg"] == LogMsg.PARSE_SUCCESS:
    #     file_name = message["info"]["file_name"]
    #     txt = "<" + file_name + ">解析成功！"
    # if message["msg"] == LogMsg.START_TASK:
    #     txt = "已开始执行任务"
    # if message["msg"] == LogMsg.STOP_TASK:
    #     txt = "正在停止当前任务"
    # if message["msg"] == LogMsg.TASK_DONE:
    #     txt = "任务已结束"
    # if message["msg"] == LogMsg.FILE_EXIST:
    #     txt = "文件<" + message["info"]["file_name"] + ">已存在！"
    # if message["msg"] == LogMsg.DOWNLOADING:
    #     txt = "正在下载文件<"+ message["info"]["file_name"] +">"
    # if message["msg"] == LogMsg.DOWNLOAD_SUCCESS:
    #     txt = "文件<" + message["info"]["file_name"] + ">下载成功！"
    # if message["msg"] == LogMsg.DOWNLOAD_FAIL:
    #     txt = "文件<" + message["info"]["file_name"] + ">下载失败"
    #     if "retry" in message["info"].keys() and message["info"]["retry"] > 0:
    #         txt += ",正在进行第" + message["info"]["retry"] + "次重试…"
    #     else:
    #         txt += "o(╥﹏╥)o"
    # if message["msg"] == LogMsg.BATCH_DOWNLOAD_FAIL:
    #     if "retry" in message["info"].keys() and message["info"]["retry"] > 0:
    #         txt = "将进行第" + message["info"]["retry"] + "轮重新下载"
    #     else:
    #         txt = "下载结束"
    #     txt += "，下载失败的文件有<" + message["info"]["file_names"] + ">"
    # if message["msg"] == LogMsg.BATCH_DOWNLOAD_SUCCESS:
    #     txt = "下载结束，全部文件下载完成！"
    # if message["msg"] == LogMsg.MERGING:
    #     txt = "正在合并视频片段，生成视频文件<" + message["info"]["file_name"] + ">"
    # if message["msg"] == LogMsg.MERGE_CANCEL:
    #     txt = "视频合并取消执行"
    # if message["msg"] == LogMsg.MERGE_DONE:
    #     txt = "视频合并完成，保存路径为<" + message["info"]["file_path"] + ">"
    # print(txt)
