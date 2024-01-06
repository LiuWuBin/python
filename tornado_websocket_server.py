import tornado.websocket
import tornado.httpserver
import tornado.ioloop
import tornado.web
import json
import redis
import time
import traceback
import subprocess
from huawei_phone_sid import huawei_phone_sid_object

# 广告链接
from domains import common_task

TaskObject = {}


class WebSocketHandler(tornado.websocket.WebSocketHandler):

    async def on_message(self, message):
        await my_print("on_message:", message)
        message_object = json.loads(message)
        # heart|task|timeOut
        task_type = message_object["type"]
        sid = message_object["sid"]
        session_id = message_object["sessionId"]
        if task_type == "task":
            await my_print("sid:", sid, " -session_id:", session_id, " -任务信息")
            await adb_connect(sid)
            tornado.ioloop.IOLoop.current().add_callback(self.my_task, message_object)
        else:
            await my_print("sid:", sid, " -session_id:", session_id, " -类型:", task_type)
            try:
                if sid in TaskObject:
                    ad_task = TaskObject[sid]
                    if ad_task is not None:
                        task_data = await ad_task.task_data()
                        task_result_object = {"type": task_type, "sessionId": session_id, "data": task_data}
                        await my_print(task_type, "结果:", task_result_object)
                        if self.ws_connection is not None:
                            await my_print("连接状态ok，发送", task_type, "结果")
                            await self.write_message(json.dumps(task_result_object))
                            if task_type == "timeOut":
                                await my_print("连接状态ok，已经发送timeOut结果，关闭连接")
                                # 已经超时，关闭websocket连接
                                self.close()
                                # 已经超时，finish_task
                                try:
                                    await ad_task.finish_task()
                                except Exception as e:
                                    await my_print("finishTask异常:", str(traceback.format_exc()))
                                # 已经超时，删除TaskObject in sid
                                try:
                                    if sid in TaskObject:
                                        await my_print("TaskObject in sid,删除")
                                        del TaskObject[sid]
                                    else:
                                        await my_print("TaskObject not in sid")
                                except Exception as e:
                                    await my_print("删除TaskObject-sid异常:", str(traceback.format_exc()))
                                # 已经超时，删除ad_task
                                try:
                                    if ad_task is not None:
                                        await my_print("ad_task not None,del")
                                        del ad_task
                                    else:
                                        await my_print("ad_task is None")
                                except Exception as e:
                                    await my_print("del-ad_task异常:", str(traceback.format_exc()))
                                # 已经超时，断开连接
                                await adb_disconnect(sid)
                        else:
                            await my_print("连接已关闭，无法发送", task_type, "结果，断开手机连接")
                            # 连接已经断开，finish_task
                            try:
                                await ad_task.finish_task()
                            except Exception as e:
                                await my_print("finishTask异常:", str(traceback.format_exc()))
                            # 连接已经断开，TaskObject in sid,删除
                            try:
                                if sid in TaskObject:
                                    await my_print("TaskObject in sid,删除")
                                    del TaskObject[sid]
                                else:
                                    await my_print("TaskObject not in sid")
                            except Exception as e:
                                await my_print("删除TaskObject-sid异常:", str(traceback.format_exc()))
                            # 连接已经断开，删除ad_task
                            try:
                                if ad_task is not None:
                                    await my_print("ad_task not None,del")
                                    del ad_task
                                else:
                                    await my_print("ad_task is None")
                            except Exception as e:
                                await my_print("del-ad_task异常:", str(traceback.format_exc()))
                            # 连接已经断开，断开连接
                            await adb_disconnect(sid)
                    else:
                        await my_print("sid:", sid, " -session_id:", session_id, " -", task_type, " - ad_task为None")
                        # ad_task为None，TaskObject in sid,删除
                        try:
                            if sid in TaskObject:
                                await my_print("TaskObject in sid,删除")
                                del TaskObject[sid]
                            else:
                                await my_print("TaskObject not in sid")
                        except Exception as e:
                            await my_print("删除TaskObject-sid异常:", str(traceback.format_exc()))
                        # ad_task为None，删除ad_task
                        try:
                            if ad_task is not None:
                                await my_print("ad_task not None,del")
                                del ad_task
                            else:
                                await my_print("ad_task is None")
                        except Exception as e:
                            await my_print("del-ad_task异常:", str(traceback.format_exc()))
                        # ad_task为None，断开连接
                        await adb_disconnect(sid)
                else:
                    await my_print("sid:", sid, " -session_id:", session_id, " -", task_type, " - TaskObject不包含key:",
                                   sid)
                    # TaskObject不包含key，TaskObject in sid,删除
                    try:
                        if sid in TaskObject:
                            await my_print("TaskObject in sid,删除")
                            del TaskObject[sid]
                        else:
                            await my_print("TaskObject not in sid")
                    except Exception as e:
                        await my_print("删除TaskObject-sid异常:", str(traceback.format_exc()))
                    # TaskObject不包含key，断开连接
                    await adb_disconnect(sid)
            except Exception as e:
                await my_print("心跳-超时异常:", str(traceback.format_exc()))
                # 心跳-超时异常，断开连接
                await adb_disconnect(sid)

    def on_close(self):
        print("WebSocket closed")

    def check_origin(self, origin):
        return True

    async def my_task(self, message_object):
        sid = message_object["sid"]
        session_id = message_object["sessionId"]
        ad_base_url = message_object["adBaseUrl"]
        device_port = await check_device_port(sid)
        if device_port != "":
            RealMetrics_Width = message_object["RealMetrics_Width"]
            RealMetrics_Height = message_object["RealMetrics_Height"]
            Metrics_Width = message_object["Metrics_Width"]
            Metrics_Height = message_object["Metrics_Height"]
            task_page_duration = message_object["task_page_duration"]
            task_click_rate = message_object["task_click_rate"]
            task_page_view = message_object["task_page_view"]
            taskTime_max = message_object["taskTime_max"]
            task_json_info = ""
            if "task_json_info" in message_object:
                task_json_info = message_object["task_json_info"]
            # 广告位控制新加参数
            ggw_json_info = ""
            gmail = ""
            search_key = ""
            task_url_id = ""
            if "ggw_json_info" in message_object:
                ggw_json_info = message_object["ggw_json_info"]
            if "gmail" in message_object:
                gmail = message_object["gmail"]
            if "search_key" in message_object:
                search_key = message_object["search_key"]
            if "task_url_id" in message_object:
                task_url_id = message_object["task_url_id"]
            base_url = ""
            if "base_url" in message_object:
                base_url = message_object["base_url"]
            extra = ""
            if "extra" in message_object:
                extra = message_object["extra"]
            ad_task: common_task = None
            if task_json_info != "":
                ad_task = common_task.AdTask(self, session_id, sid, device_port, ad_base_url,
                                             RealMetrics_Width, RealMetrics_Height, Metrics_Width,
                                             Metrics_Height, task_page_duration, task_click_rate,
                                             task_page_view, taskTime_max, task_json_info, ggw_json_info, gmail, search_key, task_url_id,base_url,extra)

            if ad_task is not None:
                await my_print("当前建立的连接:", TaskObject)
                TaskObject[sid] = ad_task
                task_error = ""
                try:
                    # 一直等待任务执行，直到结束
                    await ad_task.start_task()
                except Exception as e:
                    await my_print("任务异常:", str(traceback.format_exc()))
                    task_error = str(traceback.format_exc())
                task_data = await ad_task.task_data()
                task_data["sid"] = sid
                task_data["device_port"] = device_port
                if task_error != "":
                    task_data["taskError"] = task_error
                task_result_object = {"type": "finish", "sessionId": session_id, "data": task_data}
                await my_print("任务结果:", task_result_object)
                if self.ws_connection is not None:
                    await my_print("连接状态ok，发送任务结果")
                    await self.write_message(json.dumps(task_result_object))
                    # 任务正常结束，关闭websocket连接
                    self.close()
                else:
                    await my_print("连接已关闭，无法发送任务结果")
                # 任务正常结束，finish_task
                try:
                    await ad_task.finish_task()
                except Exception as e:
                    await my_print("finishTask异常:", str(traceback.format_exc()))
                # 任务正常结束，TaskObject in sid,删除
                try:
                    if sid in TaskObject:
                        await my_print("TaskObject in sid,删除")
                        del TaskObject[sid]
                    else:
                        await my_print("TaskObject not in sid")
                except Exception as e:
                    await my_print("删除TaskObject-sid异常:", str(traceback.format_exc()))
                # 任务结束，删除ad_task
                try:
                    if ad_task is not None:
                        await my_print("ad_task not None,del")
                        del ad_task
                    else:
                        await my_print("ad_task is None")
                except Exception as e:
                    await my_print("del-ad_task异常:", str(traceback.format_exc()))
                # 任务正常结束，断开连接
                await adb_disconnect(sid)
            else:
                await my_print("任务实例化失败")
                if self.ws_connection is not None:
                    await my_print("连接状态ok，关闭连接")
                    self.close()
                else:
                    await my_print("连接已关闭，断开手机连接")
                    await adb_disconnect(sid)
        else:
            await my_print("获取手机端口失败")
            if self.ws_connection is not None:
                await my_print("连接状态ok，关闭连接")
                self.close()
            else:
                await my_print("连接已关闭，断开手机连接")
                await adb_disconnect(sid)


async def adb_connect(sid):
    try:
        local_sid_port = str(sid) + ":5555"
        if local_sid_port in huawei_phone_sid_object:
            huawei_sid_port = huawei_phone_sid_object[local_sid_port]
            command = "adb connect " + huawei_sid_port
        else:
            command = "adb connect " + local_sid_port
        await my_print("连接手机:", command)
        subprocess.call(command, shell=True)
    except Exception as e:
        await my_print("连接手机异常:", str(traceback.format_exc()))


async def adb_disconnect(sid):
    try:
        if sid is not None:
            local_sid_port = str(sid) + ":5555"
            if local_sid_port in huawei_phone_sid_object:
                huawei_sid_port = huawei_phone_sid_object[local_sid_port]
                command = "adb disconnect " + huawei_sid_port
            else:
                command = "adb disconnect " + local_sid_port
            await my_print("断开手机:", command)
            subprocess.call(command, shell=True)
        else:
            await my_print("断开手机，sid is None")
    except Exception as e:
        await my_print("断开手机异常:", str(traceback.format_exc()))


async def my_print(*args):
    nowTime = time.strftime("%H:%M:%S", time.localtime())
    print(nowTime, *args)


async def check_device_port(sid):
    try:
        firstPort = 2000
        my_redis = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)
        # my_redis = redis.Redis(host="localhost", port=7379, db=0, decode_responses=True)

        device_port = my_redis.get(sid)
        if (device_port is None) or (device_port == ""):
            with my_redis.pipeline() as pipe:
                while True:
                    try:
                        pipe.watch('port_counter')
                        current_port_counter = pipe.get('port_counter')
                        if current_port_counter is None:
                            current_port_counter = firstPort
                        else:
                            current_port_counter = int(current_port_counter)
                        next_port = current_port_counter + 1
                        pipe.multi()
                        pipe.set('port_counter', next_port)
                        pipe.set(sid, next_port)
                        results = pipe.execute()
                        results = results[1]
                        break
                    except redis.WatchError:
                        continue
        device_port = my_redis.get(sid)
        await my_print("sid:", sid, " - 对应端口:", device_port)
        my_redis.close()
    except Exception as e:
        await my_print("check_device_port异常:", str(traceback.format_exc()))
        device_port = ""
    return device_port


app = tornado.web.Application([(r"/", WebSocketHandler), ])

if __name__ == "__main__":
    # playwright服务器 - 测试
    # app.listen(8891, "0.0.0.0")
    # print("Server started at 0.0.0.0:8891")

    # playwright服务器 - 正式
    app.listen(9891, "0.0.0.0")
    print("Server started at 0.0.0.0:9891")
    tornado.ioloop.IOLoop.current().start()
