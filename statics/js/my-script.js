// segmentState: 0-prepare/fail, 1-downloading, 2-success
// task_status: prepare, running, stopping, finished

// {"task_id":xx, "m3u8_name":xx, "http_prefix":xx, "video_name":xx, "segment_states":{}, "segment_durations":{}, "task_status":xx", video_info":{}};
var task;

var tableCol = 4

$("document").ready(function(){
    $.ajax({
        type : "GET",
        contentType: "application/json;charset=UTF-8",
        dataType:"json",
        url : "/v",
        data : "",
        success : function(data) {
            if(data["msg"] == "free"){
                $("#clear-all").trigger("click");
                console.log("No Task Now.");
            }
            if(data["msg"] == "busy"){
                task = data["info"];
                dataUpdater.refresh();
                render.renderAll();
                delete task["logs"];
            }
        },
        error : function(e){
            console.log(e.status);
            console.log(e.responseText);
        }
    });
    ws = new WebSocket("ws://"+ document.domain + ":" + location.port + "/ws");
    ws.onmessage = function(event){
        // {"msg":xx, "task_id":xx, "info":{}}
        data = JSON.parse(event.data);
        if(data["msg"]=="websocket_connected"){
            console.log("websocket connected");
            return;
        }
        if(task == undefined || task["task_id"] != data["task_id"]){
            console.log("front-end and back-end inconsistant.")
            return;
        }
        handleMessage(data);
    }
    ws.onclose = function(){
        console.log("websocket disconnected.")
    }
})



$("#parse-m3u8").click(function(){
    var m3u8_url = $("#m3u8-url").val();
    $("#parse-m3u8").attr("disabled", true);
    $("#clear-all").attr("disabled", true);
    $.ajax({
        type : "POST",
        //请求的媒体类型
        contentType: "application/json;charset=UTF-8",
        dataType:"json",
        url : "/m3u8",
        data : JSON.stringify({"m3u8_url":m3u8_url}),
        success : function(data) {
            if(data["msg"] == "busy"){
                bootbox.alert({
                    size: "small",
                    title: "忙碌",
                    message: "服务正忙，有其他视频正在解析或下载，请等待！",
                    locale: "zh_CN",
                    callback: function(){}
                });
            }
            if(data["msg"] == "fail"){
                bootbox.alert({
                    size: "small",
                    title: "无效",
                    message: "URL地址解析失败！",
                    locale: "zh_CN",
                    callback: function(){}
                });
            }
            if(data["msg"] == "success"){
                task = data["info"];
                dataUpdater.refresh();
            }
        },
        error : function(e){
            console.log(e.status);
            console.log(e.responseText);
        },
        complete : function(){
            render.renderAll();
        }
    });
});



$("#clear-all").click(function(){
    if(task != undefined && (task["task_status"] == "running" || task["task_status"] == "stopping")){
        bootbox.alert({
            size: "small",
            title: "无效",
            message: "有正在下载的任务，暂时无法清空！",
            locale: "zh_CN",
            callback: function(){}
        });
    }else{
        task = undefined;
        render.renderAll();
        render.renderLogArea([], false);
    }
})


$("#start-download").click(function(){
    if(task == undefined || task["task_status"] != "prepare"){
        bootbox.alert({
            size: "small",
            title: "无效",
            message: "请先对URL地址进行解析，再开始下载！",
            locale: "zh_CN",
            callback: function(){}
        });
        return;
    }
    var postData = JSON.parse(JSON.stringify(task));
    postData["video_name"] = $("#video-name").val();
    delete postData["segment_states"];
    delete postData["video_info"];
    $.ajax({
        //请求方式
        type : "POST",
        //请求的媒体类型
        contentType: "application/json;charset=UTF-8",
        dataType:"json",
        //请求地址
        url : "/v",
        //数据，json字符串
        data : JSON.stringify(postData),
        //请求成功
        success : function(data) {
            if(data["msg"] == "busy"){
                bootbox.alert({
                    size: "small",
                    title: "忙碌",
                    message: "服务正忙，有其他视频正在下载，请等待！",
                    locale: "zh_CN",
                    callback: function(){}
                });
                console.log("other downloading…");
                return;
            }
            info = data["info"];
            task_id = info["task_id"];
            if(task == undefined || info["task_id"] != task["task_id"]){
                console.log("front-end and back-end inconsistant.")
                return;
            }
            task["segment_states"] = info["segment_states"];
            task["task_status"] = "running";
            delete task["logs"];
            dataUpdater.refresh();
            render.renderAll();
            render.renderLogArea(convertMsg2Log({"msg":wsMsg.START_TASK}));
        },
        error : function(e){
            console.log(e.status);
            console.log(e.responseText);
        }
    });
});



$("#stop-download").click(function(){
    if(task==undefined){
        bootbox.alert({
            size: "small",
            title: "无效",
            message: "没有找到可以停止的任务！",
            locale: "zh_CN",
            callback: function(){}
        });
        return;
    }
    putData = {"task_id":task["task_id"]};
    $.ajax({
        //请求方式
        type : "PUT",
        //请求的媒体类型
        contentType: "application/json;charset=UTF-8",
        dataType:"json",
        //请求地址
        url : "/v",
        //数据，json字符串
        data : JSON.stringify(putData),
        //请求成功
        success : function(data) {
            if(data["msg"] == "free"){
                bootbox.alert({
                    size: "small",
                    title: "无效",
                    message: "当前没有任务在执行！",
                    locale: "zh_CN",
                    callback: function(){}
                });
                return;
            }
            if(data["msg"] == "inconstant"){
                bootbox.alert({
                    size: "small",
                    title: "无效",
                    message: "提交的请求与实际任务不一致，该请求被取消！",
                    locale: "zh_CN",
                    callback: function(){}
                });
                return;
            }
            if(data["msg"] == "success"){
                dataUpdater.stopTask();
                render.renderLogArea([{"msg": wsMsg.STOP_TASK}]);
                render.renderButtons();
                render.renderProgressBar();
            }
        },
        error : function(e){
            console.log(e.status);
            console.log(e.responseText);
        }
    });
});



$("#parsed-url").on("DOMNodeInserted DOMNodeRemoved", function(event){
    if(event.type == "DOMNodeRemoved"){
        $(this).css("display","none");
    }else{
        $(this).css("display","block");
    }
});



class DataUpdater {
    constructor() {
        var _this = this;
        this.refresh = function () {
            _this.setVideoInfo();
        };
        this.stopTask = function () {
            if(task == undefined){
                return;
            }
            if(task["task_status"] == "running"){
                task["task_status"] = "stopping";
            }
        }
        this.setVideoInfo = function () {
            var segmentStates = task["segment_states"];
            var segmentDurations = task["segment_durations"];
            var totalVideoDuration = 0;
            var finishedVideoDuration = 0;
            var fininshedSegmentCount = 0;
            var totalSegmentCount = 0;
            for (var segmentName in segmentDurations) {
                var segmentState = segmentStates[segmentName];
                var segmentDuration = segmentDurations[segmentName];
                if (segmentState == 2) {
                    finishedVideoDuration += segmentDuration;
                    fininshedSegmentCount += 1;
                }
                totalVideoDuration += segmentDuration;
                totalSegmentCount += 1
            }
            var videoInfo = { "finished_video_duration": finishedVideoDuration, "total_video_duration": totalVideoDuration, "finished_segment_count": fininshedSegmentCount, "total_segment_count": totalSegmentCount};
            task["video_info"] = videoInfo;
        };
        this.updateVideoInfo = function (segmentName, segmentState) {
            if (task==undefined || !task["segment_states"].hasOwnProperty(segmentName) || task["segment_states"][segmentName] == segmentState) {
                return;
            }
            if (segmentState == 2) {
                task["video_info"]["finished_video_duration"] += task["segment_durations"][segmentName];
                task["video_info"]["finished_segment_count"] += 1;
            } else if (task["segment_states"][segmentName] == 2){
                task["video_info"]["finished_video_duration"] -= task["segment_durations"][segmentName];
                task["video_info"]["finished_segment_count"] -= 1;
            }
            task["segment_states"][segmentName] = segmentState;
        };
    }
}
var dataUpdater = new DataUpdater()


class Render {
    constructor() {
        var _this = this;
        this.renderAll = function () {
            _this.renderInputBox();
            _this.renderURLReminder();
            _this.renderSegments();
            _this.renderVideoInfo();
            _this.renderProgressBar();
            _this.renderButtons();
            if (task != undefined && task.hasOwnProperty("logs")) {
                _this.renderLogArea(task["logs"], true);
            }
        };
        this.renderInputBox = function() {
            if (task == undefined || !task.hasOwnProperty("m3u8_name")) {
                $("#m3u8-url").val("")
                $("#video-name").val("")
                return
            }
            if($("#m3u8-url").val().length == 0 && task.hasOwnProperty("http_prefix")){
                $("#m3u8-url").val(task["http_prefix"] + task["m3u8_name"])
            }
            if(task.hasOwnProperty("video_name")){
                $("#video-name").val(task["video_name"])
            }else{
                $("#video-name").val(task["m3u8_name"].split(".")[0] + ".mp4")
            }
        };
        this.renderButtons = function () {
            if (task == undefined) {
                $("#parse-m3u8").attr("disabled", false);
                $("#clear-all").attr("disabled", false);
                $("#start-download").attr("disabled", true);
                $("#start-download").text("下载");
                $("#stop-download").attr("disabled", true);
                $("#stop-download").text("停止下载");
                return;
            } 
            if (task["task_status"] == "prepare" || task["task_status"] == "finished") {
                $("#parse-m3u8").attr("disabled", false);
                $("#clear-all").attr("disabled", false);
                $("#start-download").attr("disabled", false);
                $("#start-download").text("下载");
                $("#stop-download").attr("disabled", true);
                $("#stop-download").text("停止下载");
            }
            if (task["task_status"] == "running") {
                $("#parse-m3u8").attr("disabled", true);
                $("#clear-all").attr("disabled", true);
                $("#start-download").attr("disabled", true);
                $("#start-download").text("正在下载…");
                $("#stop-download").attr("disabled", false);
                $("#stop-download").text("停止下载");
            }
            if (task["task_status"] == "stopping") {
                $("#parse-m3u8").attr("disabled", true);
                $("#clear-all").attr("disabled", true);
                $("#start-download").attr("disabled", true);
                $("#start-download").text("正在下载…");
                $("#stop-download").attr("disabled", true);
                $("#stop-download").text("正在停止…");
            }
        };
        this.renderSegments = function () {
            if(task==undefined || !task.hasOwnProperty("segment_durations") || !task.hasOwnProperty("segment_states")){
                $("#segment-map-tb").html("");
                return;
            }
            var segmentNames = [];
            for (var segmentName in task["segment_durations"]) {
                segmentNames.push(segmentName);
            }
            segmentNames.sort(function (a, b) { return parseInt(a.split(".")[0].match(/.*?(\d+)/)[1]) - parseInt(b.split(".")[0].match(/.*?(\d+)/)[1]); });
            var segmentMapTbHtml = "";
            for (let i = 0; i < segmentNames.length; i = i + tableCol) {
                segmentMapTbHtml += "<tr>";
                for (let j = 0; j < tableCol; j++) {
                    if (i + j >= segmentNames.length) {
                        break;
                    }
                    var class_list = ["align-middle"];
                    if (i + tableCol > segmentNames.length) {
                        class_list.push("td-last-row");
                    }
                    if (j == tableCol - 1) {
                        class_list.push("td-last-col");
                    }
                    var segmentName = segmentNames[i + j];
                    var segmentState = task["segment_states"][segmentName];
                    if (segmentState == 1) {
                        class_list.push("segment-downloading");
                    }
                    if (segmentState == 2) {
                        class_list.push("segment-done");
                    }
                    var segmentId = "segment-" + segmentName.split(".")[0];
                    var class_text = class_list.join(" ");
                    segmentMapTbHtml += "<td id=\"" + segmentId + "\" " + "class=\"" + class_text + "\">" + segmentName + "</td>";
                }
                segmentMapTbHtml += "</tr>";
            }
            $("#segment-map-tb").html(segmentMapTbHtml);
            $("#segment-map-tb td").css("width", Math.floor(100 / tableCol) + "%");
        };
        this.renderSegmentChange = function (segmentName) {
            if(task==undefined || !task.hasOwnProperty("segment_states")){
                return;
            }
            var segmentState = task["segment_states"][segmentName];
            var segmentId = "segment-" + segmentName.split(".")[0];
            var segmentDOM = $("#" + segmentId);
            segmentDOM.removeClass("segment-downloading segment-done");
            if (segmentState == 1) {
                segmentDOM.addClass("segment-downloading");
            }
            if (segmentState == 2) {
                segmentDOM.addClass("segment-done");
            }
            _this.renderVideoInfo();
        };
        this.renderVideoInfo = function () {
            if(task == undefined || !task.hasOwnProperty("video_info")){
                $("#segment-done-count").text(0);
                $("#segment-total-count").text(0);
                $("#video-duration").text(sec2time(0));
                return;
            }
            var totalVideoDuration = task["video_info"]["total_video_duration"];
            var finishedSegmentCount = task["video_info"]["finished_segment_count"];
            var totalSegmentCount = task["video_info"]["total_segment_count"];
            $("#segment-done-count").text(finishedSegmentCount);
            $("#segment-total-count").text(totalSegmentCount);
            $("#video-duration").text(sec2time(totalVideoDuration));
        };
        this.renderProgressBar = function () {
            $("#download-progress").removeClass("active");
            var percent;
            if(task == undefined || !task.hasOwnProperty("video_info")){
                percent = 0;
            }else{
                if (task.hasOwnProperty("task_status") && (task["task_status"] == "running" || task["task_status"] == "stopping")) {
                    $("#download-progress").addClass("active");
                }
                if(task["task_status"] == "finished"){
                    percent = 100;
                }else{
                    var finishedDuration = task["video_info"]["finished_video_duration"];
                    var videoDuration = task["video_info"]["total_video_duration"];
                    percent = parseInt(100 * finishedDuration / videoDuration);
                }
            }
            $("#download-progress div span").text(percent + "%");
            $("#download-progress div").css("width", percent + "%");
            $("#download-progress div").attr("aria-valuenow", percent);
        };
        this.renderURLReminder = function() {
            if(task == undefined){
                $("#parsed-url").html("");
                return;
            }
            var httpPrefix = task["http_prefix"];
            var m3u8Name = task["m3u8_name"];
            $("#parsed-url").html("<p>当前解析地址：" + httpPrefix + m3u8Name + "</p>");
        }
        this.renderLogArea = function (messages, append = true) {
            var logAreaDOM = $("#log-area");
            var logAreaAppend = function (txt) {
                logAreaDOM.val(logAreaDOM.val() + txt + "\n");
            };
            if (!append) {
                logAreaDOM.val("");
            }
            for (let i = 0; i < messages.length; i++) {
                var log = convertMsg2Log(messages[i])
                if(log != undefined){
                    logAreaAppend(log);
                }
            }
        };
    }
}
var render = new Render()


function sec2time(s) {
    var t;
    if(s > -1){
        var hour = Math.floor(s/3600);
        var min = Math.floor(s/60) % 60;
        var sec = s % 60;
        if(hour < 10) {
            t = '0'+ hour + ":";
        } else {
            t = hour + ":";
        }
        if(min < 10){t += "0";}
        t += min + ":";
        if(sec < 10){t += "0";}
        t += Math.round(sec);
    }
    return t;
}

function handleMessage(message){
    var segmentName;
    switch(message["msg"]){
        case wsMsg.PARSE_SUCCESS:
        case wsMsg.START_TASK:
        case wsMsg.STOP_TASK:
            break;
        case wsMsg.TASK_DONE:
            if(task==undefined){
                return;
            }
            task["task_status"] = "finished";
            render.renderButtons();
            break;
        case wsMsg.FILE_EXIST:
        case wsMsg.DOWNLOAD_SUCCESS:
            if(task == undefined){
                return;
            }
            segmentName = message["info"]["file_name"];
            dataUpdater.updateVideoInfo(segmentName, 2);
            break;
        case wsMsg.DOWNLOADING:
            if(task == undefined){
                return;
            }
            segmentName = message["info"]["file_name"];
            dataUpdater.updateVideoInfo(segmentName, 1);
            break;
        case wsMsg.DOWNLOAD_FAIL:
            if(task == undefined){
                return;
            }
            segmentName = message["info"]["file_name"];
            if(message["info"].hasOwnProperty("retry") && message["info"]["retry"] > 0){
                dataUpdater.updateVideoInfo(segmentName, 1);
            }else{
                dataUpdater.updateVideoInfo(segmentName, 0);
            }
            break;
        case wsMsg.BATCH_DOWNLOAD_FAIL:
        case wsMsg.BATCH_DOWNLOAD_SUCCESS:
        case wsMsg.MERGING:
        case wsMsg.MERGE_CANCEL:
        case wsMsg.MERGE_DONE:
            break;
    }
    if(segmentName != undefined){
        render.renderSegmentChange(segmentName);
    }
    render.renderProgressBar();
    render.renderVideoInfo();
    render.renderLogArea([message], true);
}

function convertMsg2Log(message){
    var txt;
    switch(message["msg"]){
        case wsMsg.PARSE_SUCCESS:
            var file_name = message["info"]["file_name"];
            txt = "<" + file_name + ">解析成功！";
            break;
        case wsMsg.START_TASK:
            txt = "已开始执行任务";
            break;
        case wsMsg.STOP_TASK:
            txt = "正在停止当前任务";
            break;
        case wsMsg.TASK_DONE:
            txt = "任务已结束";
            break;
        case wsMsg.FILE_EXIST:
            txt = "文件<" + message["info"]["file_name"] + ">已存在！"
            break;
        case wsMsg.DOWNLOADING:
            txt = "正在下载文件<"+ message["info"]["file_name"] +">";
            break;
        case wsMsg.DOWNLOAD_SUCCESS:
            txt = "文件<" + message["info"]["file_name"] + ">下载成功！";
            break;
        case wsMsg.DOWNLOAD_FAIL:
            txt = "文件<" + message["info"]["file_name"] + ">下载失败";
            if(message["info"].hasOwnProperty("retry") && message["info"]["retry"] > 0){
                txt += ",正在进行第" + message["info"]["retry"] + "次重试…"
            }else{
                txt += "o(╥﹏╥)o";
            }
            break;
        case wsMsg.BATCH_DOWNLOAD_FAIL:
            if(message["info"].hasOwnProperty("retry")&& message["info"]["retry"] > 0){
                txt = "将进行第" + message["info"]["retry"] + "轮重新下载";
            }else{
                txt = "下载结束";
            }
            txt += "，下载失败的文件有<" + message["info"]["file_names"] + ">";
            break;
        case wsMsg.BATCH_DOWNLOAD_SUCCESS:
            txt = "下载结束，全部文件下载完成！"
            break;
        case wsMsg.MERGING:
            txt = "正在合并视频片段，生成视频文件<" + message["info"]["file_name"] + ">";
            break;
        case wsMsg.MERGE_CANCEL:
            txt = "视频合并取消执行";
            break;
        case wsMsg.MERGE_DONE:
            txt = "视频合并完成，保存路径为<" + message["info"]["file_path"] + ">";
            break;
    }
    return txt;
}


wsMsg = {
    "PARSE_SUCCESS": "parse_success",

    "START_TASK": "start_task",
    "STOP_TASK": "stop_task",
    "TASK_DONE": "task_done",

    "FILE_EXIST": "file_exist",
    "DOWNLOADING": "downloading",
    "DOWNLOAD_SUCCESS": "download_success",
    "DOWNLOAD_FAIL": "download_fail",
    "BATCH_DOWNLOAD_SUCCESS": "batch_download_success",
    "BATCH_DOWNLOAD_FAIL": "batch_download_fail",

    "MERGING": "merging",
    "MERGE_CANCEL": "merge_cancel",
    "MERGE_DONE": "merge_done",
}