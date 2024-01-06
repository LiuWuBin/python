import asyncio
import base64
import json
import random
import subprocess
import time
import traceback
import typing

import aiohttp
from urllib.parse import urlparse

import requests
from playwright.async_api import (Playwright, Browser, BrowserContext, Page, Request, Route, ElementHandle, Frame,
                                  Error)

import ad_real_url
from ads.ads_util import AdsUtil
from logger_factory import LoggerFactory

from base_set_new import BaseSetNew
from huawei_phone_sid import huawei_phone_sid_object


# 将*args拼成一个字符串
def join_args(*args):
    result = ''.join(map(str, args))
    return result


# 获取日期
def date(format_: str, timestamp: int = None):
    new_format = ''
    for c in format_:
        if c == 'Y':
            new_format += '%Y'
        elif c == 'm':
            new_format += '%m'
        elif c == 'd':
            new_format += '%d'
        elif c == 'H':
            new_format += '%H'
        elif c == 'i':
            new_format += '%M'
        elif c == 's':
            new_format += '%S'
        else:
            new_format += c
    return time.strftime(new_format, time.localtime(timestamp))

class PublicUtils_new:
    # 初始化参数
    # pageUrlArray-列表-浏览页面地址
    pageUrlArray = []
    # adShowArray-列表-展示的广告
    adShowArray = []
    # adShowUrlObject-字典-展示的广告和其url
    adShowUrlObject = {}
    # adPageUrlOriginArray-列表-跳转广告页面的地址 (出现前后广告页面地址参数有变化，这个只记录origin)
    adPageUrlOriginArray = []
    # pageTimeObject-字典（无序，可变和有索引，没有重复）-网页主页浏览时间
    pageTimeObject = {}
    # adPageTimeObject-字典（无序，可变和有索引，没有重复）-广告网页浏览时间
    adPageTimeObject = {}
    # clickAdIdArray-列表-点击的广告id
    clickAdIdArray = []
    # 根据url记录页面要点击的广告
    clickAdIdObject = {}
    # indexPageCompleteTime-首页加载完成时间
    indexPageCompleteTime: float = 0
    # jsTime,js代码更新时间
    jsTime = ""
    # 记录一些信息
    someLog = {}
    # 记录被屏蔽的url地址的host
    blockUrlArray = []
    # nowSpendTime-任务已经花费时间
    nowSpendTime: float = 0
    # taskFinish - 任务完成
    taskFinish = False
    # taskPageOver - 任务网页浏览个数状态
    taskPageViewOver = False
    # 随机浏览广告，url - 广告在当前页面的索引
    scrollToAdIndexObject = {}
    # 打开页面的时间
    startPageTime: float = 0
    # js获取手机userAgent
    js_userAgent = ""
    # js获取手机language
    js_language = ""
    # js获取手机screenWidth
    js_screenWidth: float = 0
    # js获取手机screenHeight
    js_screenHeight: float = 0
    # js获取手机devicePixelRatio
    js_devicePixelRatio: float = 0
    # ip归属地
    IPCountry = ""
    # 一次任务只会点一个广告，点击的广告的初始跳转地址（主域名）
    click_url = ""
    # 一次任务只会点一个广告，点击的广告的初始跳转地址（完整链接）
    click_url_full = ""
    # 一次任务只会点一个广告，广告页面的地址（最终跳转地址）
    click_success_url = ""
    # 广告位展示-点击计数
    adInfoObject = {}
    # 最终点击的广告位
    click_ad_id = ""
    # 最终点击的广告位的广告信息（类型和二次确认）
    click_ad_id_info = ""
    # 任务的结果状态码
    code = "100"
    # 记录页面错误信息
    page_error_text_object = {}
    # 定义广告落地页的浏览时间
    other_page_time = 0
    # 定义广告落地页的浏览页面个数
    other_page_visit = 0
    # 告诉服务器需要增加的时间(只有点击成功才赋值)
    add_task_time = 0

    # 全局赋值
    page: Page
    context: BrowserContext
    browser: Browser
    playwright: Playwright
    # websocket连接
    websocket_client = {}
    # 任务session_id，点击滑动命令需要
    session_id = ""

    # 服务器下发-页面浏览时
    task_page_duration = [30, 20]
    # 服务器下发-广告点击率
    task_click_rate = 500
    # 服务器下发-页面浏览个数
    task_page_view = 2
    # 服务器下发-任务总时间
    task_time_max = 130
    # 服务器下发-手机sid
    sid = ""
    # 手机端口 - redis里取
    device_port = 0
    # 服务器下发-广告页面
    ad_base_url = ""
    # 服务器下发 - 手机屏幕宽高
    real_metrics_width = 1080
    real_metrics_height = 1920
    metrics_width = 1080
    metrics_height = 1920

    # 页面一些判断信息
    task_json_info = {}
    # 首页的主域名
    index_page_host = ""
    # 子页的主域名（如果和主页相同，填一样的）
    child_page_host = ""
    # 拦截的图片域名
    img_url_host_arr = []
    # 屏蔽图片，有可能导致页面结构异常，这时候不去屏蔽，直接替换(1-拦截，2-替换)
    block_url_type = 1
    # 广告的选择器
    ads_element_selector = "iframe[id*=google_ads_iframe]"
    # 广告的属性
    ads_element_attr = "id"
    # 子页面的a标签
    child_page_link_selector = ""
    # 子页面的a标签(可能有的页面有，有的没有)
    child_page_link_selector2 = ""
    # 如果有 Category 页面，需要去点击，不能直接点子页面，要判断：在首页，并且需要点击子页面，有概率直接点子页面或者Category
    category = False
    # 是否点击，随机0,10000
    category_click = 0
    # Category一般是底部tab，每个页面都能检测到，这里判断是首页才有概率去点击它
    # 在这个页面才会有概率进入category
    category_index_page_url = ""
    # category按钮
    category_btn_selector = ''
    # category的页面地址
    category_category_page_url = ""
    # category的a元素
    category_child_page_link_selector = ""

    # 广告位点击信息
    ggw_json_info = {}
    # 每个广告位控制
    ggw = {}
    # 需要点击的广告信息
    ggw_click = ""
    gmail = ""
    search_key = ""
    task_url_id = ""
    base_url = ""

    # 游戏广告，需要进入游戏详情
    play_game = False
    play_game_click = 0
    play_game_page_url = ""
    play_game_btn_selector = ""
    play_game_game_page_url = ""

    # 有的全屏广告，没有明显能区别的id，一些属性区别
    # ele.style.width = "100vw"  ele.style.height = "100vh"
    full_screen_ads_by_id = True
    # 如果id里包含以下字符串，是全屏广告
    full_screen_ads_arr = ["Inter", "inter", "outofpage", "x480"]

    # 一些其他信息，object
    # "country": "US"
    extra = {}

    # 屏幕宽
    screen_width = 540
    # 屏幕高
    screen_height = 960
    # 屏幕可用宽度
    visualViewport_width = 540
    # 屏幕可用高度
    visualViewport_height = 960
    # 日志对象
    logger: LoggerFactory = None
    # 手机操作
    baseSetNew: BaseSetNew
    # 是否启用日志
    enable_log = False
    # 广告操作
    adsUtil: AdsUtil = None
    # 是否启用ads工具
    enable_ads = True

    def __init__(self, websocket_client, session_id, sid, device_port, ad_base_url, real_metrics_width,
                 real_metrics_height, metrics_width, metrics_height, task_page_duration, task_click_rate,
                 task_page_view, task_time_max, task_json_info, ggw_json_info, gmail, search_key, task_url_id, base_url, extra):
        self.websocket_client = websocket_client
        self.session_id = session_id
        self.sid = sid
        self.device_port = device_port
        self.ad_base_url = ad_base_url
        self.real_metrics_height = real_metrics_height
        self.real_metrics_width = real_metrics_width
        self.metrics_width = metrics_width
        self.metrics_height = metrics_height
        self.task_page_duration = task_page_duration
        self.task_click_rate = task_click_rate
        self.task_page_view = task_page_view
        self.task_time_max = task_time_max
        if task_json_info != "":
            self.task_json_info = json.loads(task_json_info)
            self.index_page_host = self.task_json_info["index_page_host"]
            self.child_page_host = self.task_json_info["child_page_host"]
            self.img_url_host_arr = self.task_json_info["img_url_host_arr"]
            self.block_url_type = int(self.task_json_info["block_url_type"])
            self.ads_element_selector = self.task_json_info["ads_element_selector"]
            self.ads_element_attr = self.task_json_info["ads_element_attr"]
            self.child_page_link_selector = self.task_json_info["child_page_link_selector"]
            self.child_page_link_selector2 = self.task_json_info["child_page_link_selector2"]
            if self.task_json_info["category"] == "True":
                self.category = True
            else:
                self.category = False
            self.category_click = self.task_json_info["category_click"]
            self.category_index_page_url = self.task_json_info["category_index_page_url"]
            self.category_child_page_link_selector = self.task_json_info["category_child_page_link_selector"]
            self.category_btn_selector = self.task_json_info["category_btn_selector"]
            self.category_category_page_url = self.task_json_info["category_category_page_url"]
            if self.task_json_info["play_game"] == "True":
                self.play_game = True
            else:
                self.play_game = False
            self.play_game_click = self.task_json_info["play_game_click"]
            self.play_game_page_url = self.task_json_info["play_game_page_url"]
            self.play_game_btn_selector = self.task_json_info["play_game_btn_selector"]
            self.play_game_game_page_url = self.task_json_info["play_game_game_page_url"]
            if self.task_json_info["full_screen_ads_by_id"] == "True":
                self.full_screen_ads_by_id = True
            else:
                self.full_screen_ads_by_id = False
            self.full_screen_ads_arr = self.task_json_info["full_screen_ads_arr"]
        if ggw_json_info != "":
            self.ggw_json_info = json.loads(ggw_json_info)
            # ggw，配置的各个广告位
            self.ggw = self.ggw_json_info["ggw"]
            # click - ggw，需要点击的广告位
            ggw_json_info_click = self.ggw_json_info["click"]
            if "ggw" in ggw_json_info_click:
                self.ggw_click = ggw_json_info_click["ggw"]
        self.gmail = gmail
        self.search_key = search_key
        self.task_url_id = task_url_id
        self.base_url = base_url
        # 一些额外参数，服务会存在在extra
        if extra != "":
            self.extra = json.loads(extra)
        # 一些任务记录初始化
        self.pageUrlArray = []
        self.adShowArray = []
        self.adShowUrlObject = {}
        self.adPageUrlOriginArray = []
        self.pageTimeObject = {}
        self.adPageTimeObject = {}
        self.clickAdIdArray = []
        self.clickAdIdObject = {}
        self.indexPageCompleteTime = 0
        self.jsTime = ""
        self.someLog = {}
        self.blockUrlArray = []
        self.nowSpendTime = 0
        self.taskFinish = False
        self.taskPageViewOver = False
        self.scrollToAdIndexObject = {}
        self.startPageTime = 0
        self.js_userAgent = ""
        self.js_language = ""
        self.js_screenWidth = 0
        self.js_screenHeight = 0
        self.js_devicePixelRatio = 0
        self.IPCountry = ""
        self.click_url = ""
        self.click_url_full = ""
        self.click_success_url = ""
        self.adInfoObject = {}
        self.click_ad_id = ""
        self.click_ad_id_info = ""
        self.code = "100"
        self.page_error_text_object = {}
        self.other_page_time = 0
        self.other_page_visit = 0
        self.add_task_time = 0
        # 工具类
        self.logger = None
        self.baseSetNew = None

    # 返回值
    async def task_data(self):
        #  adPageUrlOriginArray 提交用 adPageUrlArray
        taskResult = {"pageUrlArray": self.pageUrlArray, "adShowArray": self.adShowArray,
                      "adPageUrlArray": self.adPageUrlOriginArray,
                      "clickAdIdArray": self.clickAdIdArray,
                      "pageTimeObject": self.pageTimeObject, "adPageTimeObject": self.adPageTimeObject,
                      "clickAdIdObject": self.clickAdIdObject,
                      "indexPageCompleteTime": self.indexPageCompleteTime,
                      "task_page_view": self.task_page_view, "task_page_duration": self.task_page_duration,
                      "task_click_rate": self.task_click_rate,
                      "userAgent": self.js_userAgent, "language": self.js_language,
                      "screenWidth": self.js_screenWidth, "screenHeight": self.js_screenHeight,
                      "devicePixelRatio": self.js_devicePixelRatio, "adShowUrlObject": self.adShowUrlObject,
                      "IPCountry": self.IPCountry, "adBaseUrl": self.ad_base_url, "jsTime": self.jsTime, "click_url": self.click_url,
                      "click_url_full": self.click_url_full,
                      "code": self.code, "page_error": self.page_error_text_object,"add_task_time": self.add_task_time}
        if self.startPageTime == 0:
            session_duration = 0
        else:
            session_duration = int(time.time() - self.startPageTime)
        taskResult["session_duration"] = session_duration
        if len(self.someLog) != 0:
            taskResult["someLog"] = self.someLog
        # 设置广告位展示点击相关信息
        # 统计展示
        # 1@google_ads_iframe_/22965457460/happyearly.com/happyearly-336x280-01_0
        adInfoObject_temp = {}
        for ad_show_id in self.adShowArray:
            if "@" in ad_show_id:
                ad_show_id = ad_show_id.split("@")[1]
            if ad_show_id in adInfoObject_temp:
                adShow_id_object = adInfoObject_temp[ad_show_id]
                adShow_id_object["show"] += 1
            else:
                adShow_id_object = {"show": 1, "click": 0}
                adInfoObject_temp[ad_show_id] = adShow_id_object
        self.adInfoObject = adInfoObject_temp
        # click_success_url不为空，跳转到广告页面，点击成功
        if self.click_success_url != "":
            for adInfo_ad_id in self.adInfoObject:
                if adInfo_ad_id == self.click_ad_id:
                    adInfo_ad_id_object = self.adInfoObject[adInfo_ad_id]
                    adInfo_ad_id_object["click"] = 1
        if self.click_success_url != "":
            if "##" not in self.click_success_url:
                self.click_success_url = self.click_success_url + self.click_ad_id_info
        taskResult["click_success_url"] = self.click_success_url
        taskResult["adInfoObject"] = self.adInfoObject
        return taskResult

    # 日志打印格式化
    async def my_print(self, *args):
        nowTime = date('Y-m-d H:i:s')
        print(nowTime, self.sid, *args)
        if self.enable_log:
            msg = join_args(*args)
            await self.logger.log_info(f"{self.sid} - {msg}")

    # 同步方法打印
    def sync_print(self, *args):
        nowTime = date('Y-m-d H:i:s')
        print(nowTime, self.sid, *args)

    # 不打印日志
    async def my_print_not_log(self, *args):
        nowTime = date('Y-m-d H:i:s')
        print(nowTime, self.sid, *args)

    # 开启日志
    async def setup_logger_factory(self):
        # 开启日志
        # domain = await url2_domain(self.ad_base_url)
        # new_domain = domain.replace(".", "_")
        today = date("Ymd")
        phone_sid = self.sid
        self.logger = LoggerFactory('./logs', f'{today}_{phone_sid}')

    # 赋予 playwright 对象

    async def assign_playwright(self, playwright: Playwright):
        self.playwright = playwright

    # 浏览器已断开连接
    def browser_disconnected(self, browser: Browser):
        try:
            self.sync_print("browser_disconnected")
        except Exception as e:
            self.sync_print("browser_disconnected异常:", str(traceback.format_exc()))

    # 浏览器上下文关闭
    def browser_context_close(self, any_: typing.Any):
        try:
            self.sync_print("browser_context_close")
        except Exception as e:
            self.sync_print("browser_context_close异常:", str(traceback.format_exc()))

    # 页面关闭
    def page_close(self, any_: typing.Any):
        try:
            self.sync_print("page_close")
        except Exception as e:
            self.sync_print("page_close异常:", str(traceback.format_exc()))

    # 任务完成 关闭浏览器

    async def finish_task(self):
        self.taskFinish = True
        try:
            await self.my_print("page.close")
            if self.page is not None:
                await self.my_print("page - not none")
                await self.page.close()
        except Exception as e:
            await self.my_print("page.close异常:", e)
        try:
            await self.my_print("browser_context.close")
            if self.context is not None:
                await self.my_print("browser_context - not none")
                await self.context.close()
        except Exception as e:
            await self.my_print("browser_context.close异常:", e)
        try:
            await self.my_print("browser.close")
            if self.browser is not None:
                await self.my_print("browser - not none")
                await self.browser.close()
        except Exception as e:
            await self.my_print("browser.close异常:", e)
        try:
            await self.my_print("playwright.stop")
            if self.playwright is not None:
                await self.my_print("playwright - not none")
                await self.playwright.stop()
        except Exception as e:
            await self.my_print("playwright.stop异常:", e)

    # 屏蔽图片加载

    async def route_image(self, route: Route, request: Request):
        request_url_lower = request.url.lower()
        if len(self.img_url_host_arr) == 0:
            await route.continue_()
        else:
            is_block_img_url = False
            for imgUrlHost in self.img_url_host_arr:
                if request_url_lower.startswith(imgUrlHost):
                    is_block_img_url = True
            if is_block_img_url:
                if (".png" in request_url_lower or ".jpg" in request_url_lower or ".webp" in request_url_lower or
                        ".gif" in request_url_lower or ".jpeg" in request_url_lower or
                        request.resource_type in ["audio", "video"]):
                    parsed_url = urlparse(request.url)
                    request_url_origin = parsed_url.scheme + "://" + parsed_url.netloc
                    if request_url_origin not in self.blockUrlArray:
                        await self.my_print("屏蔽:", request_url_origin)
                        self.blockUrlArray.append(request_url_origin)
                    if self.block_url_type == 1:
                        await route.abort()
                    else:
                        await route.fulfill(path="local.jpeg")
                else:
                    await route.continue_()
            else:
                await route.continue_()

    # 转发手机地址

    async def forward(self):
        for i in range(10):
            await self.my_print("forward - i:", i)
            local_sid_port = str(self.sid) + ":5555"
            if local_sid_port in huawei_phone_sid_object:
                huawei_sid_port = huawei_phone_sid_object[local_sid_port]
                forwardCommand = "adb -s " + huawei_sid_port + " forward tcp:" + str(
                    self.device_port) + " localabstract:chrome_devtools_remote"
            else:
                forwardCommand = "adb -s " + local_sid_port + " forward tcp:" + str(
                    self.device_port) + " localabstract:chrome_devtools_remote"
            await self.my_print("绑定端口:", forwardCommand)
            # 如果命令成功执行，返回值是0，如果命令执行失败，返回值是非0。
            result = subprocess.call(forwardCommand, shell=True)
            await self.my_print("result:", result)
            if result == 0:
                break
            await asyncio.sleep(3)

    # ip归属地
    async def checkIPCountry(self):
        await self.my_print("checkIPCountry")
        try:
            async with self.page.expect_navigation(timeout=20000, wait_until="domcontentloaded"):
                await self.page.goto("https://myip.duoduodev.com/check/myip")
                body_element = await self.page.query_selector("body")
                if body_element is not None:
                    self.IPCountry = await body_element.inner_text()
                    await self.my_print("ip_country:", self.IPCountry)
        except Exception as e:
            await self.my_print("checkIPCountry异常:", str(traceback.format_exc()))

    # 验证转发是否成功
    async def http_get(self):
        for i in range(10):
            await self.my_print("http_get - i:", i)
            url = "http://localhost:" + str(self.device_port) + "/json/version"
            cmd = ["curl", url]
            result = subprocess.run(cmd, capture_output=True, text=True)
            result_str = str(result)
            await self.my_print("result_str:", result_str)
            if "Android-Package" in result_str:
                break
            await asyncio.sleep(3)

    # 解析url，获取其中的广告地址
    async def query_adurl(self, origin_url):
        await self.my_print("query_adurl")
        read_url = ""
        try:
            if (origin_url is not None) and (origin_url != ""):
                read_url = ad_real_url.check_ad_real_url(origin_url)
                if read_url.startswith("https://ad.doubleclick.net"):
                    read_url = ad_real_url.check_doubleclick_url(read_url)
        except Exception as e:
            await self.my_print(f'query_adurl错误：{e}')
        if (read_url is None) and (read_url == ""):
            read_url = origin_url
        return read_url

    # 遍历iframe内部的a元素，找到符合条件的href
    async def find_frame_a_href(self, frame_element: ElementHandle):
        # await self.my_print("find_frame_a_href - start")
        frame_a_href_result = ""
        try:
            content_frame = await frame_element.content_frame()
            if content_frame is not None:
                frame_a_list = await content_frame.query_selector_all("a")
                frame_a_list_len = len(frame_a_list)
                await self.my_print("frame_a_list_len:", frame_a_list_len)
                if frame_a_list_len > 0:
                    await self.my_print("frame内有a标签")
                    for frame_a in frame_a_list:
                        try:
                            if frame_a is not None:
                                frame_a_box = await frame_a.bounding_box()
                                if frame_a_box is not None:
                                    left = int(frame_a_box["x"])
                                    top = int(frame_a_box["y"])
                                    rect = await content_frame.evaluate("ele => ele.getBoundingClientRect()", frame_a)
                                    width = int(rect["width"])
                                    height = int(rect["height"])
                                    if (width > 0) and (height > 0):
                                        await self.my_print("frame内a元素 -left:", left, " -top:", top, " -width:",
                                                            width, " -height:", height)
                                        frame_a_href = await frame_a.get_attribute("href")
                                        if frame_a_href is not None:
                                            frame_a_href_start = frame_a_href[0:100]
                                            await self.my_print("frame内a元素 -href:", frame_a_href_start)
                                            is_redirectUrl = False
                                            for redirectUrlHost in self.baseSetNew.redirectUrlHost_array:
                                                if frame_a_href is not None:
                                                    if frame_a_href.startswith(redirectUrlHost):
                                                        is_redirectUrl = True
                                            if is_redirectUrl:
                                                await self.my_print("frame内a元素 -href:", frame_a_href_start, " - 是跳转链接")
                                                frame_a_href_result = frame_a_href
                                                return frame_a_href_result
                                        # else:
                                        # await self.my_print("frame内a元素 -href:", frame_a_href)
                        except Exception as e:
                            await self.my_print("iframe内a元素异常:", str(traceback.format_exc()))
        except Exception as e:
            await self.my_print("find_frame_a_href异常:", str(traceback.format_exc()))
        # await self.my_print("find_frame_a_href - end")
        return frame_a_href_result

    # 查找元素内部frame，调用方法去查找frame内部的a元素
    async def find_element_inner_a_href(self, frame_element: ElementHandle):
        # await self.my_print("find_element_inner_a_href - start")
        await self.my_print("find_element_inner_a_href:", frame_element)
        href_value = ""
        href_value = await self.find_frame_a_href(frame_element)
        if href_value != "":
            return href_value
        try:
            content_frame = await frame_element.content_frame()
            if content_frame is not None:
                frame_iframe_list = await content_frame.query_selector_all("iframe")
                frame_iframe_list_len = len(frame_iframe_list)
                await self.my_print("frame_iframe_list_len:", frame_iframe_list_len)
                if frame_iframe_list_len > 0:
                    await self.my_print("元素内有iframe")
                    for frame_iframe in frame_iframe_list:
                        try:
                            if frame_iframe is not None:
                                rect = await content_frame.evaluate("ele => ele.getBoundingClientRect()", frame_iframe)
                                width = int(rect["width"])
                                height = int(rect["height"])
                                if (width > 0) and (height > 0):
                                    await self.my_print("元素内iframe -width:", width, " -height:", height)
                                    href_value = await self.find_element_inner_a_href(frame_iframe)
                                    if href_value != "":
                                        return href_value
                        except Exception as e:
                            await self.my_print("遍历元素内有iframe异常:", str(traceback.format_exc()))
        except Exception as e:
            await self.my_print("find_element_inner_a_href异常:", str(traceback.format_exc()))
        # await self.my_print("find_element_inner_a_href - end")
        return href_value

    # 遍历iframe内部的a元素data-asoch-targets属性值，用来判断广告类型
    async def find_frame_a_type(self, frame_element: ElementHandle):
        # await self.my_print("find_frame_a_type - start")
        frame_a_type_result = []
        try:
            content_frame = await frame_element.content_frame()
            if content_frame is not None:
                frame_a_list = await content_frame.query_selector_all("a")
                frame_a_list_len = len(frame_a_list)
                await self.my_print("frame_a_list_len:", frame_a_list_len)
                if frame_a_list_len > 0:
                    await self.my_print("frame内有a标签")
                    for frame_a in frame_a_list:
                        try:
                            if frame_a is not None:
                                frame_a_box = await frame_a.bounding_box()
                                if frame_a_box is not None:
                                    left = int(frame_a_box["x"])
                                    top = int(frame_a_box["y"])
                                    rect = await content_frame.evaluate("ele => ele.getBoundingClientRect()", frame_a)
                                    width = int(rect["width"])
                                    height = int(rect["height"])
                                    if (width > 0) and (height > 0):
                                        # await self.my_print("frame内a元素 -left:", left, " -top:", top, " -width:",
                                        #                     width, " -height:", height)
                                        frame_a_attr = await frame_a.get_attribute("data-asoch-targets")
                                        if frame_a_attr is not None:
                                            # await self.my_print("frame内a元素 -data-asoch-targets:", frame_a_attr)
                                            if frame_a_attr not in frame_a_type_result:
                                                frame_a_type_result.append(frame_a_attr)
                                        # else:
                                        # await self.my_print("frame内a元素 -data-asoch-targets:", frame_a_attr)
                        except Exception as e:
                            await self.my_print("iframe内a元素异常:", str(traceback.format_exc()))
        except Exception as e:
            await self.my_print("find_frame_a_type异常:", str(traceback.format_exc()))
        await self.my_print("frame_a_type_result:", frame_a_type_result)
        # await self.my_print("find_frame_a_type - end")
        return frame_a_type_result

    # 查找元素内部frame，遍历iframe内部的a元素data-asoch-targets属性值，用来判断广告类型
    async def find_element_a_type(self, frame_element: ElementHandle):
        # await self.my_print("find_element_a_type - start")
        await self.my_print("find_element_a_type:", frame_element)
        element_a_type_result = []
        frame_a_type_result = await self.find_frame_a_type(frame_element)
        if frame_a_type_result is not None:
            element_a_type_result = list(set(element_a_type_result + frame_a_type_result))
        try:
            content_frame = await frame_element.content_frame()
            if content_frame is not None:
                frame_iframe_list = await content_frame.query_selector_all("iframe")
                frame_iframe_list_len = len(frame_iframe_list)
                await self.my_print("frame_iframe_list_len:", frame_iframe_list_len)
                if frame_iframe_list_len > 0:
                    await self.my_print("元素内有iframe")
                    for frame_iframe in frame_iframe_list:
                        try:
                            if frame_iframe is not None:
                                rect = await content_frame.evaluate("ele => ele.getBoundingClientRect()", frame_iframe)
                                width = int(rect["width"])
                                height = int(rect["height"])
                                if (width > 0) and (height > 0):
                                    await self.my_print("元素内iframe -width:", width, " -height:", height)
                                    element_a_type_result_2 = await self.find_element_a_type(frame_iframe)
                                    if element_a_type_result_2 is not None:
                                        element_a_type_result = list(set(element_a_type_result + element_a_type_result_2))
                        except Exception as e:
                            await self.my_print("遍历元素内有iframe异常:", str(traceback.format_exc()))
        except Exception as e:
            await self.my_print("find_element_a_type异常:", str(traceback.format_exc()))
        # await self.my_print("find_element_a_type - end")
        return element_a_type_result

    # 遍历iframe内部元素class为video-container，用来判断是不是视频广告
    async def find_frame_video_type(self, frame_element: ElementHandle):
        # await self.my_print("find_frame_video_type - start")
        frame_video_type_result = []
        try:
            content_frame = await frame_element.content_frame()
            if content_frame is not None:
                frame_video_list = await content_frame.query_selector_all(".video-container")
                frame_video_list_len = len(frame_video_list)
                await self.my_print("frame_video_list_len:", frame_video_list_len)
                if frame_video_list_len > 0:
                    await self.my_print("frame内有a标签")
                    for frame_video in frame_video_list:
                        try:
                            if frame_video is not None:
                                frame_video_box = await frame_video.bounding_box()
                                if frame_video_box is not None:
                                    left = int(frame_video_box["x"])
                                    top = int(frame_video_box["y"])
                                    rect = await content_frame.evaluate("ele => ele.getBoundingClientRect()", frame_video)
                                    width = int(rect["width"])
                                    height = int(rect["height"])
                                    if (width > 0) and (height > 0):
                                        await self.my_print("frame内video元素 -left:", left, " -top:", top, " -width:",
                                                            width, " -height:", height)
                                        frame_video_class = await frame_video.get_attribute("class")
                                        if frame_video_class is not None:
                                            await self.my_print("frame内video元素 -class:", frame_video_class)
                                            if frame_video_class not in frame_video_type_result:
                                                frame_video_type_result.append(frame_video_class)
                                        else:
                                            await self.my_print("frame内video元素 -class:", frame_video_class)
                        except Exception as e:
                            await self.my_print("iframe内video元素异常:", str(traceback.format_exc()))
        except Exception as e:
            await self.my_print("find_frame_video_type异常:", str(traceback.format_exc()))
        await self.my_print("frame_video_type_result:", frame_video_type_result)
        # await self.my_print("find_frame_video_type - end")
        return frame_video_type_result

    # 查找元素内部frame，遍历iframe内部元素class为video-container，用来判断是不是视频广告
    async def find_element_video_type(self, frame_element: ElementHandle):
        # await self.my_print("find_element_video_type - start")
        await self.my_print("find_element_video_type:", frame_element)
        element_video_type_result = []
        frame_video_type_result = await self.find_frame_video_type(frame_element)
        if frame_video_type_result is not None:
            element_video_type_result = list(set(element_video_type_result + frame_video_type_result))
        try:
            content_frame = await frame_element.content_frame()
            if content_frame is not None:
                frame_iframe_list = await content_frame.query_selector_all("iframe")
                frame_iframe_list_len = len(frame_iframe_list)
                await self.my_print("frame_iframe_list_len:", frame_iframe_list_len)
                if frame_iframe_list_len > 0:
                    await self.my_print("元素内有iframe")
                    for frame_iframe in frame_iframe_list:
                        try:
                            if frame_iframe is not None:
                                rect = await content_frame.evaluate("ele => ele.getBoundingClientRect()", frame_iframe)
                                width = int(rect["width"])
                                height = int(rect["height"])
                                if (width > 0) and (height > 0):
                                    await self.my_print("元素内iframe -width:", width, " -height:", height)
                                    element_video_type_result_2 = await self.find_element_video_type(frame_iframe)
                                    if element_video_type_result_2 is not None:
                                        element_video_type_result = list(set(element_video_type_result + element_video_type_result_2))
                        except Exception as e:
                            await self.my_print("遍历元素内有iframe异常:", str(traceback.format_exc()))
        except Exception as e:
            await self.my_print("find_element_video_type异常:", str(traceback.format_exc()))
        # await self.my_print("find_element_video_type - end")
        return element_video_type_result

    # 查找元素内部frame，遍历iframe内部元素的text，用来判断是不是搜索广告
    async def find_frame_text_type(self, frame_element: ElementHandle):
        # await self.my_print("find_frame_text_type - start")
        frame_text_type_result = ""
        try:
            content_frame = await frame_element.content_frame()
            if content_frame is not None:
                frame_body = await content_frame.query_selector("body")
                if frame_body is not None:
                    frame_body_box = await frame_body.bounding_box()
                    if frame_body_box is not None:
                        left = int(frame_body_box["x"])
                        top = int(frame_body_box["y"])
                        rect = await content_frame.evaluate("ele => ele.getBoundingClientRect()", frame_body)
                        width = int(rect["width"])
                        height = int(rect["height"])
                        if (width > 0) and (height > 0):
                            await self.my_print("frame内body元素 -left:", left, " -top:", top, " -width:",
                                                width, " -height:", height)
                            frame_text_type_result = await frame_body.inner_text()
        except Exception as e:
            await self.my_print("find_frame_text_type异常:", str(traceback.format_exc()))
        await self.my_print("frame_text_type_result:", frame_text_type_result)
        # await self.my_print("find_frame_text_type - end")
        return frame_text_type_result

    # 查找元素内部frame，遍历iframe内部元素的text，用来判断是不是搜索广告
    async def find_element_text_type(self, frame_element: ElementHandle):
        # await self.my_print("find_element_text_type - start")
        await self.my_print("find_element_text_type:", frame_element)
        element_text_type_result = ""
        frame_text_type_result = await self.find_frame_text_type(frame_element)
        if frame_text_type_result is not None:
            element_text_type_result = element_text_type_result + str(frame_text_type_result)
        try:
            content_frame = await frame_element.content_frame()
            if content_frame is not None:
                frame_iframe_list = await content_frame.query_selector_all("iframe")
                frame_iframe_list_len = len(frame_iframe_list)
                await self.my_print("frame_iframe_list_len:", frame_iframe_list_len)
                if frame_iframe_list_len > 0:
                    await self.my_print("元素内有iframe")
                    for frame_iframe in frame_iframe_list:
                        try:
                            if frame_iframe is not None:
                                rect = await content_frame.evaluate("ele => ele.getBoundingClientRect()", frame_iframe)
                                width = int(rect["width"])
                                height = int(rect["height"])
                                if (width > 0) and (height > 0):
                                    await self.my_print("元素内iframe -width:", width, " -height:", height)
                                    element_text_type_result_2 = await self.find_element_text_type(frame_iframe)
                                    if element_text_type_result_2 is not None:
                                        element_text_type_result = element_text_type_result + str(element_text_type_result_2)
                        except Exception as e:
                            await self.my_print("遍历元素内有iframe异常:", str(traceback.format_exc()))
        except Exception as e:
            await self.my_print("find_element_text_type异常:", str(traceback.format_exc()))
        # await self.my_print("find_element_text_type - end")
        return element_text_type_result

    async def check_ad_element_adtype(self, pageUrlArray_len_id: str, ad_element: ElementHandle):
        ad_element_adtype = ""
        try:
            # 查找广告类型 （video，image，imageText,text,search）
            # 先查找是不是视频广告，再查找搜索类广告（search）,最后查找data-asoch-targets属性
            # data-asoch-targets属性（小写），其中包含image，logo视为imageText，其他视为文字
            # 以上什么都没有的，视为image
            element_video_type = await self.find_element_video_type(ad_element)
            # 对应video: ['video-container']
            await self.my_print("广告id:", pageUrlArray_len_id, " -对应video:", element_video_type)

            element_text_type = await self.find_element_text_type(ad_element)
            # 对应text: Pittsburgh's Source for
            await self.my_print("广告id:", pageUrlArray_len_id, " -对应text:", element_text_type)

            element_a_type = await self.find_element_a_type(ad_element)
            # 对应type: ['ad0,ochTitle', 'ad0,ochUrl', 'ad0,ochButton', 'ad0,ochBody']
            await self.my_print("广告id:", pageUrlArray_len_id, " -对应type:", element_a_type)

            if len(element_video_type) != 0:
                ad_element_adtype = "video"
            if (ad_element_adtype == "") and ("Search for" in element_text_type):
                ad_element_adtype = "search"
            if ad_element_adtype == "":
                if len(element_a_type) == 0:
                    # 跳转链接类型为空，如果文字也为空，就默认是image广告，否则为text广告
                    if len(element_text_type) == 0:
                        ad_element_adtype = "image"
                    else:
                        ad_element_adtype = "text"
                else:
                    for a_type in element_a_type:
                        a_type = a_type.lower()
                        if "image" in a_type or "img" in a_type or "logo" in a_type:
                            ad_element_adtype = "imageText"
                    # 链接类型，没有image类型，有其他类型（['ad0,bodyClk', 'ad0,btnClk', 'ad0,urlClk', 'ad0,titleClk']），认为是text
                    if ad_element_adtype == "":
                        ad_element_adtype = "text"
            if ad_element_adtype == "":
                ad_element_adtype = "image"
        except Exception as e:
            await self.my_print("check_ad_element_adtype异常:", str(traceback.format_exc()))
        return ad_element_adtype

    # 查找元素内部的二次点击元素，返回位置
    # 先判断元素内有没有二次点击元素，有的话，先点击内部a元素，让二次点击按钮出现，然后再次查找二次点击元素位置
    # 注意，二次点击元素未显示状态时，元素位置可能不在广告iframe内部
    async def find_frame_confirm_btn(self, frame_element: ElementHandle):
        # await self.my_print("find_frame_confirm_btn - start")
        frame_confirm_btn_result = []
        try:
            content_frame = await frame_element.content_frame()
            if content_frame is not None:
                common_15click_anchor = await content_frame.query_selector("#common_15click_anchor")
                if common_15click_anchor is not None:
                    common_15click_anchor_box = await common_15click_anchor.bounding_box()
                    if common_15click_anchor_box is not None:
                        left = int(common_15click_anchor_box["x"])
                        top = int(common_15click_anchor_box["y"])
                        rect = await content_frame.evaluate("ele => ele.getBoundingClientRect()", common_15click_anchor)
                        width = int(rect["width"])
                        height = int(rect["height"])
                        if (width > 0) and (height > 0):
                            await self.my_print("frame内Yes -left:", left, " -top:", top, " -width:",
                                                width, " -height:", height)
                            common_15click_anchor_text = await common_15click_anchor.inner_text()
                            await self.my_print("common_15click_anchor_text:", common_15click_anchor_text)
                            x = int(left + width * 0.5)
                            y = int(top + height * 0.5)
                            await self.my_print("common_15click_anchor -x:", x, " -y:", y)
                            clickXY = str(x) + "-" + str(y)
                            frame_confirm_btn_result.append(clickXY)
        except Exception as e:
            await self.my_print("find_frame_confirm_btn异常:", str(traceback.format_exc()))
        await self.my_print("frame_a_type_result:", frame_confirm_btn_result)
        # await self.my_print("find_frame_confirm_btn - end")
        return frame_confirm_btn_result

    # 查找元素内部的二次点击元素，返回位置
    # 先判断元素内有没有二次点击元素，有的话，先点击内部a元素，让二次点击按钮出现，然后再次查找二次点击元素位置
    # 注意，二次点击元素未显示状态时，元素位置可能不在广告iframe内部
    async def find_element_confirm_btn(self, frame_element: ElementHandle):
        # await self.my_print("find_element_confirm_btn - start")
        await self.my_print("find_element_confirm_btn:", frame_element)
        element_confirm_btn_result = []
        frame_confirm_btn_result = await self.find_frame_confirm_btn(frame_element)
        if frame_confirm_btn_result is not None:
            element_confirm_btn_result = list(set(element_confirm_btn_result + frame_confirm_btn_result))
        try:
            content_frame = await frame_element.content_frame()
            if content_frame is not None:
                frame_iframe_list = await content_frame.query_selector_all("iframe")
                frame_iframe_list_len = len(frame_iframe_list)
                await self.my_print("frame_iframe_list_len:", frame_iframe_list_len)
                if frame_iframe_list_len > 0:
                    await self.my_print("元素内有iframe")
                    for frame_iframe in frame_iframe_list:
                        try:
                            if frame_iframe is not None:
                                rect = await content_frame.evaluate("ele => ele.getBoundingClientRect()", frame_iframe)
                                width = int(rect["width"])
                                height = int(rect["height"])
                                if (width > 0) and (height > 0):
                                    await self.my_print("元素内iframe -width:", width, " -height:", height)
                                    element_confirm_btn_result_2 = await self.find_element_confirm_btn(frame_iframe)
                                    if element_confirm_btn_result_2 is not None:
                                        element_confirm_btn_result = list(set(element_confirm_btn_result + element_confirm_btn_result_2))
                        except Exception as e:
                            await self.my_print("遍历元素内有iframe异常:", str(traceback.format_exc()))
        except Exception as e:
            await self.my_print("find_element_confirm_btn异常:", str(traceback.format_exc()))
        # await self.my_print("find_element_confirm_btn - end")
        return element_confirm_btn_result

    # 计算广告元素（非iframe）点击的坐标
    async def find_ad_element_link_xy(self, clickAdIframeLocator):
        await self.my_print("find_ad_element_link_xy - 广告属性:", clickAdIframeLocator)
        resultXYObject = {}
        anchor_a = []
        normal_a = []
        ad_element = await self.page.query_selector(clickAdIframeLocator)
        if ad_element is not None:
            await self.my_print("find_ad_element_link_xy - 广告属性:", clickAdIframeLocator, " - 元素不为None")
            await self.page.evaluate("ele => ele.scrollIntoView({block:'center'})", ad_element)
            await self.page.wait_for_timeout(3000)
            rect = await self.page.evaluate("ele => ele.getBoundingClientRect()", ad_element)
            left = int(rect["left"])
            top = int(rect["top"])
            right = int(rect["right"])
            bottom = int(rect["bottom"])
            width = int(rect["width"])
            height = int(rect["height"])
            await self.my_print("广告元素 -width:", width, " -height:", height, "-left:",
                                left, " -top:", top, " -right:", right, " -bottom:", bottom)
            if (width > 0) and (height > 0):
                random_x = width * 0.25 + random.randint(1, int(width * 0.5))
                await self.my_print("random_x:", random_x)
                x = int(left + random_x)
                y = int(top + height * 0.5)
                await self.my_print("普通广告，点击广告元素0.5位置 -x:", x, " -y:", y)
                clickXY = str(x) + "-" + str(y)
                normal_a.append(clickXY)
                await self.my_print("anchor_a:", anchor_a)
                await self.my_print("normal_a:", normal_a)
                if (len(anchor_a) != 0) or (len(normal_a) != 0):
                    resultXYObject["anchor_a"] = anchor_a
                    resultXYObject["normal_a"] = normal_a
                    return resultXYObject
        else:
            await self.my_print("find_ad_element_link_xy - 广告属性:", clickAdIframeLocator, " - 元素为None")
        return resultXYObject

    # 计算广告元素点击的坐标
    async def find_ad_iframe_link_xy(self, clickAdIframeLocator):
        await self.my_print("find_ad_iframe_link_xy - 广告id:", clickAdIframeLocator)
        # 如果有二次确认按钮，返回2个点击坐标
        resultXYObject = {}
        anchor_a = []
        normal_a = []
        ad_iframe_element = await self.page.query_selector(clickAdIframeLocator)
        if ad_iframe_element is not None:
            await self.my_print("find_ad_iframe_link_xy - 广告id:", clickAdIframeLocator, " - 元素不为None")
            await self.page.evaluate("ele => ele.scrollIntoView({block:'center'})", ad_iframe_element)
            # await self.swipe_position(ad_iframe_element, [])
            await self.page.wait_for_timeout(3000)
            adIframe_rect = await self.page.evaluate("ele => ele.getBoundingClientRect()", ad_iframe_element)
            adIframe_left = int(adIframe_rect["left"])
            adIframe_top = int(adIframe_rect["top"])
            adIframe_right = int(adIframe_rect["right"])
            adIframe_bottom = int(adIframe_rect["bottom"])
            adIframe_width = int(adIframe_rect["width"])
            adIframe_height = int(adIframe_rect["height"])
            await self.my_print("广告iframe -width:", adIframe_width, " -height:", adIframe_height, "-left:",
                                adIframe_left, " -top:", adIframe_top, " -right:", adIframe_right, " -bottom:",
                                adIframe_bottom)
            # 获取 iframe 元素
            # 将 iframe 元素转为 frame 对象
            # 在 iframe 中获取所有的 a 元素
            adIframe = await ad_iframe_element.content_frame()
            try:
                await adIframe.wait_for_load_state("domcontentloaded")
                # 二次确认按钮
                common_15click_anchor = await adIframe.query_selector("#common_15click_anchor")
                if common_15click_anchor is not None:
                    await self.my_print("common_15click_anchor:", common_15click_anchor)
                    common_15click_anchor_box = await common_15click_anchor.bounding_box()
                    if common_15click_anchor_box is not None:
                        left = int(common_15click_anchor_box["x"])
                        top = int(common_15click_anchor_box["y"])
                        rect = await adIframe.evaluate("ele => ele.getBoundingClientRect()", common_15click_anchor)
                        width = int(rect["width"])
                        height = int(rect["height"])
                        await self.my_print("common_15click_anchor -left:", left, " -top:", top, " -width:", width, " -height:", height)
                        if (width > 0) and (height > 0):
                            common_15click_anchor_text = await common_15click_anchor.inner_text()
                            await self.my_print("common_15click_anchor_text:", common_15click_anchor_text)
                            x = int(left + width * 0.5)
                            y = int(top + height * 0.5)
                            await self.my_print("common_15click_anchor -x:", x, " -y:", y)
                            clickXY = str(x) + "-" + str(y)
                            anchor_a.append(clickXY)

                adIframe_aList = await adIframe.query_selector_all("a")
                adIframe_aList_len = len(adIframe_aList)
                await self.my_print("adIframe_aList_len:", adIframe_aList_len)
                if adIframe_aList_len > 0:
                    await self.my_print("iframe内有a标签")
                    for adIframe_a in adIframe_aList:
                        if adIframe_a is not None:
                            box = await adIframe_a.bounding_box()
                            if box is not None:
                                left = int(box["x"])
                                top = int(box["y"])
                                rect = await adIframe.evaluate("ele => ele.getBoundingClientRect()", adIframe_a)
                                width = int(rect["width"])
                                height = int(rect["height"])
                                if (width > 15) and (height > 15):
                                    if (width < (adIframe_width + 5)) and (height < (adIframe_height + 5)) and (
                                            (adIframe_left - 5) < (left + width) < (adIframe_right + 5)) and (
                                            (adIframe_top - 5) < (top + height) < (adIframe_bottom + 5)):
                                        await self.my_print("iframe内a元素 -left:", left, " -top:", top, " -width:",
                                                            width, " -height:", height, " - 在广告范围内")
                                        adIframe_a_href = await adIframe_a.get_attribute("href")
                                        adIframe_a_href_start = adIframe_a_href[0:100]
                                        await self.my_print("iframe内a元素 -href:", adIframe_a_href_start)
                                        is_redirectUrl = False
                                        for redirectUrlHost in self.baseSetNew.redirectUrlHost_array:
                                            if adIframe_a_href is not None:
                                                if adIframe_a_href.startswith(redirectUrlHost):
                                                    is_redirectUrl = True
                                        if is_redirectUrl:
                                            await self.my_print("iframe内a元素 -href:", adIframe_a_href_start,
                                                                " - 是跳转链接")
                                            random_x = width * 0.25 + random.randint(1, int(width * 0.5))
                                            await self.my_print("random_x:", random_x)
                                            x = int(left + random_x)
                                            y = int(top + height * 0.5)
                                            await self.my_print("点击iframe内a元素0.5位置 - left:", left, " -top:", top,
                                                                " -width:", width, " -height:", height, " -x:", x,
                                                                " -y:", y)
                                            clickXY = str(x) + "-" + str(y)
                                            normal_a.append(clickXY)
                                    else:
                                        await self.my_print("iframe内a元素 -left:", left, " -top:", top, " -width:",
                                                            width, " -height:", height, " - 在广告范围外")
                    # 遍历完所有a元素
                    await self.my_print("广告内部a元素 - anchor_a:", anchor_a)
                    await self.my_print("广告内部a元素 - normal_a:", normal_a)
                    if (len(anchor_a) != 0) or (len(normal_a) != 0):
                        resultXYObject["anchor_a"] = anchor_a
                        resultXYObject["normal_a"] = normal_a
                        return resultXYObject
            except Exception as e:
                await self.my_print("iframe内a元素异常:", str(traceback.format_exc()))
            if len(resultXYObject) == 0:
                await self.my_print("iframe内没有a标签，去遍历内部的iframe内部的a标签")
                try:
                    child_iframe_list = await adIframe.query_selector_all("iframe")
                    child_iframe_list_len = len(child_iframe_list)
                    await self.my_print("child_iframe_list_len:", child_iframe_list_len)
                    if child_iframe_list_len > 0:
                        await self.my_print("内部有iframe标签")
                        for child_iframe_element in child_iframe_list:
                            await self.my_print("child_iframe_element:", child_iframe_element)
                            if child_iframe_element is not None:
                                rect = await adIframe.evaluate("ele => ele.getBoundingClientRect()",
                                                               child_iframe_element)
                                width = int(rect["width"])
                                height = int(rect["height"])
                                if (width > 0) and (height > 0):
                                    await self.my_print("内部iframe元素 -width:", width, " -height:", height)
                                    child_iframe = await child_iframe_element.content_frame()
                                    await child_iframe.wait_for_load_state("domcontentloaded")

                                    # 二次确认按钮
                                    common_15click_anchor = await adIframe.query_selector("#common_15click_anchor")
                                    if common_15click_anchor is not None:
                                        await self.my_print("common_15click_anchor:", common_15click_anchor)
                                        common_15click_anchor_box = await common_15click_anchor.bounding_box()
                                        if common_15click_anchor_box is not None:
                                            left = int(common_15click_anchor_box["x"])
                                            top = int(common_15click_anchor_box["y"])
                                            rect = await adIframe.evaluate("ele => ele.getBoundingClientRect()", common_15click_anchor)
                                            width = int(rect["width"])
                                            height = int(rect["height"])
                                            await self.my_print("common_15click_anchor -left:", left, " -top:", top, " -width:", width, " -height:", height)
                                            if (width > 0) and (height > 0):
                                                common_15click_anchor_text = await common_15click_anchor.inner_text()
                                                await self.my_print("common_15click_anchor_text:", common_15click_anchor_text)
                                                x = int(left + width * 0.5)
                                                y = int(top + height * 0.5)
                                                await self.my_print("common_15click_anchor -x:", x, " -y:", y)
                                                clickXY = str(x) + "-" + str(y)
                                                anchor_a.append(clickXY)

                                    child_iframe_aList = await child_iframe.query_selector_all("a")
                                    child_iframe_aList_len = len(child_iframe_aList)
                                    await self.my_print("child_frame_aList_len:", child_iframe_aList_len)
                                    if child_iframe_aList_len > 0:
                                        await self.my_print("内部iframe有a标签")
                                        for child_iframe_a in child_iframe_aList:
                                            if child_iframe_a is not None:
                                                box = await child_iframe_a.bounding_box()
                                                if box is not None:
                                                    left = box["x"]
                                                    top = box["y"]
                                                    rect = await child_iframe.evaluate(
                                                        "ele => ele.getBoundingClientRect()", child_iframe_a)
                                                    width = int(rect["width"])
                                                    height = int(rect["height"])
                                                    if (width > 15) and (height > 15):
                                                        if (width < (adIframe_width + 5)) and (
                                                                height < (adIframe_height + 5)) and (
                                                                (adIframe_left - 5) < (left + width) < (
                                                                adIframe_right + 5)) and (
                                                                (adIframe_top - 5) < (top + height) < (
                                                                adIframe_bottom + 5)):
                                                            await self.my_print("内部iframe的a元素 -left:", left,
                                                                                " -top:", top, " -width:", width,
                                                                                " -height:", height, " - 在广告范围内")
                                                            child_iframe_a_href = await child_iframe_a.get_attribute(
                                                                "href")
                                                            await self.my_print("内部iframe的a元素 -href:",
                                                                                child_iframe_a_href)
                                                            is_redirectUrl = False
                                                            for redirectUrlHost in self.baseSetNew.redirectUrlHost_array:
                                                                if child_iframe_a_href is not None:
                                                                    if child_iframe_a_href.startswith(redirectUrlHost):
                                                                        is_redirectUrl = True
                                                            if is_redirectUrl:
                                                                await self.my_print("内部iframe的a元素 -href:",
                                                                                    child_iframe_a_href,
                                                                                    " - 是跳转链接")
                                                                random_x = (width * 0.25 +
                                                                            random.randint(1, int(width * 0.5)))
                                                                await self.my_print("random_x:", random_x)
                                                                x = int(left + random_x)
                                                                y = int(top + height * 0.5)
                                                                await self.my_print(
                                                                    "点击内部iframe的a元素0.5位置 - left:", left,
                                                                    " -top:", top, " -width:", width, " -height:",
                                                                    height, " -x:", x, " -y:", y)
                                                                clickXY = str(x) + "-" + str(y)
                                                                normal_a.append(clickXY)
                                                        else:
                                                            await self.my_print("内部iframe的a元素 -left:", left,
                                                                                " -top:", top, " -width:", width,
                                                                                " -height:", height, " - 在广告范围外")
                                        # 遍历完所有a元素
                                        await self.my_print("内部iframe的a元素 - anchor_a:", anchor_a)
                                        await self.my_print("内部iframe的a元素 - normal_a:", normal_a)
                                        if (len(anchor_a) != 0) or (len(normal_a) != 0):
                                            resultXYObject["anchor_a"] = anchor_a
                                            resultXYObject["normal_a"] = normal_a
                                            return resultXYObject
                        if len(resultXYObject) == 0:
                            await self.my_print("广告内部iframe元素的a元素，未找到点击坐标，遍历内部iframe本身")
                            for child_iframe_element in child_iframe_list:
                                await self.my_print("child_iframe_element:", child_iframe_element)
                                if child_iframe_element is not None:
                                    box = await child_iframe_element.bounding_box()
                                    if box is not None:
                                        left = box["x"]
                                        top = box["y"]
                                        rect = await adIframe.evaluate("ele => ele.getBoundingClientRect()",
                                                                       child_iframe_element)
                                        width = int(rect["width"])
                                        height = int(rect["height"])
                                        if (width > 0) and (height > 0):
                                            await self.my_print("广告内部iframe -left:", left, " -top:", top,
                                                                " -width:",
                                                                width, " -height:", height)
                                            if (width < (adIframe_width + 5)) and (height < (adIframe_height + 5)) and (
                                                    (adIframe_left - 5) < (left + width) < (adIframe_right + 5)) and (
                                                    (adIframe_top - 5) < (top + height) < (adIframe_bottom + 5)):
                                                await self.my_print("广告内部iframe -left:", left, " -top:", top,
                                                                    " -width:", width, " -height:", height,
                                                                    " - 在广告范围内")
                                                random_x = (width * 0.25 + random.randint(1, int(width * 0.5)))
                                                await self.my_print("random_x:", random_x)
                                                x = int(left + random_x)
                                                y = int(top + height * 0.5)
                                                await self.my_print("点击广告内部iframe的0.5位置 - left:", left,
                                                                    " -top:", top, " -width:", width, " -height:",
                                                                    height, " -x:", x, " -y:", y)
                                                clickXY = str(x) + "-" + str(y)
                                                normal_a.append(clickXY)
                            # 遍历完所有a元素，没有找到坐标点，遍历内部iframe本身
                            await self.my_print("广告内部iframe - anchor_a:", anchor_a)
                            await self.my_print("广告内部iframe - normal_a:", normal_a)
                            if (len(anchor_a) != 0) or (len(normal_a) != 0):
                                resultXYObject["anchor_a"] = anchor_a
                                resultXYObject["normal_a"] = normal_a
                                return resultXYObject
                except Exception as e:
                    await self.my_print("广告内部iframe元素:", str(traceback.format_exc()))
            if len(resultXYObject) == 0:
                await self.my_print("广告iframe内部未找到点击坐标，点击ad_iframe本身")
                box = await ad_iframe_element.bounding_box()
                if box is not None:
                    left = box["x"]
                    top = box["y"]
                    rect = await self.page.evaluate("ele => ele.getBoundingClientRect()", ad_iframe_element)
                    width = int(rect["width"])
                    height = int(rect["height"])
                    await self.my_print("广告元素 -left:", left, " -top:", top, " -width:", width, " -height:", height)
                    if (width > 0) and (height > 0):
                        random_x = width * 0.25 + random.randint(1, int(width * 0.5))
                        await self.my_print("random_x:", random_x)
                        is_fullScreenAd = False
                        if self.full_screen_ads_by_id:
                            await self.my_print("全屏广告-通过id判断")
                            for fullScreenAd in self.full_screen_ads_arr:
                                if fullScreenAd in clickAdIframeLocator:
                                    is_fullScreenAd = True
                        else:
                            await self.my_print("全屏广告-通过style判断")
                            style_width = await self.page.evaluate("ele => ele.style.width", ad_iframe_element)
                            style_height = await self.page.evaluate("ele => ele.style.height", ad_iframe_element)
                            await self.my_print("style_width:", style_width, " - style_height：", style_height)
                            if ("100vw" in style_width) or ("100vh" in style_height):
                                is_fullScreenAd = True
                        if is_fullScreenAd:
                            x = int(left + width * 0.5)
                            y = int(top + height * 0.5)
                            await self.my_print("全屏广告，点击广告元素0.5位置 -x:", x, " -y:", y)
                        else:
                            x = int(left + random_x)
                            y = int(top + height * 0.85)
                            await self.my_print("普通广告，点击广告元素0.85位置 -x:", x, " -y:", y)
                        clickXY = str(x) + "-" + str(y)
                        normal_a.append(clickXY)
                        await self.my_print("ad_iframe本身 - anchor_a:", anchor_a)
                        await self.my_print("ad_iframe本身 - normal_a:", normal_a)
                        if (len(anchor_a) != 0) or (len(normal_a) != 0):
                            resultXYObject["anchor_a"] = anchor_a
                            resultXYObject["normal_a"] = normal_a
                            return resultXYObject
        else:
            await self.my_print("find_ad_iframe_link_xy - 广告id:", clickAdIframeLocator, " - 元素为None")
        return resultXYObject

    # 检查页面操作

    async def check_page_operate(self):
        current_pageUrl = self.page.url
        await self.my_print("check_page_operate - pageUrl:", current_pageUrl)
        if (current_pageUrl.startswith(self.index_page_host)) or (current_pageUrl.startswith(self.child_page_host)):
            await self.index_page()
        elif current_pageUrl.startswith("chrome-error"):
            await self.my_print("错误页面:", current_pageUrl)
        else:
            await self.other_page()

    # 判断页面浏览个数有没有完成

    async def index_page(self):
        current_pageUrl = self.page.url
        await self.my_print("index_page - pageUrl:", current_pageUrl)
        if current_pageUrl not in self.pageUrlArray:
            self.pageUrlArray.append(current_pageUrl)
        pageUrlArray_len = len(self.pageUrlArray)
        await self.my_print("index_page - pageUrlArray:", self.pageUrlArray)
        await self.my_print("index_page - 需要浏览页面个数:", self.task_page_view, "- 已经浏览页面个数:",
                            pageUrlArray_len)
        if pageUrlArray_len < self.task_page_view:
            await self.my_print("页面浏览个数没有达到，继续浏览")
            self.taskPageViewOver = False
            await self.index_page_operate()
        else:
            await self.my_print("页面浏览个数达到，停止浏览")
            self.taskPageViewOver = True
            await self.index_page_operate()

    # 跳转到广告页面操作

    async def other_page(self):
        try:
            # 点击广告成功，设置点击的广告位相关上报信息
            current_pageUrl = self.page.url
            if self.click_success_url == "":
                self.click_success_url = current_pageUrl
                self.add_task_time = self.other_page_time
                await self.my_print("原始task_time_max:", self.task_time_max)
                self.task_time_max = self.task_time_max + self.add_task_time
                await self.my_print("新task_time_max:", self.task_time_max)
                await self.adsUtil.load(
                    {
                        "page": self.page,
                        "logger": self.logger,
                        "context": self.context,
                        "browser": self.browser,
                        "baseSetNew": self.baseSetNew,
                        "screen_width": self.screen_width,
                        "screen_height": self.screen_height,
                        "ads_max_visits": self.other_page_time,
                        "visit_pace": self.other_page_visit
                    }
                )
            # 广告页面地址，只记录origin
            parsed_url = urlparse(current_pageUrl)
            current_pageUrl_origin = parsed_url.scheme + "://" + parsed_url.netloc
            await self.my_print("other_page - pageUrl_origin:", current_pageUrl_origin)

            current_pageUrl_path = parsed_url.scheme + "://" + parsed_url.netloc + parsed_url.path
            await self.my_print("other_page - pageUrl_path:", current_pageUrl_path)

            current_pageUrl_time = 0
            if current_pageUrl_origin in self.adPageTimeObject:
                current_pageUrl_time = self.adPageTimeObject[current_pageUrl_origin]
            await self.my_print("other_page - 广告页面已经浏览时长", current_pageUrl_time)
            if current_pageUrl_time <= self.other_page_time:
                await self.my_print("other_page - 广告页面已经浏览时长不超过" + str(self.other_page_time) + "s，继续浏览")

                current_pageUrl_isRedirectUrl = False
                for redirectUrlHost in self.baseSetNew.redirectUrlHost_array:
                    if current_pageUrl_origin.startswith(redirectUrlHost):
                        current_pageUrl_isRedirectUrl = True
                if not current_pageUrl_isRedirectUrl:
                    await self.my_print("other_page - 当前页面不是302跳转页面")

                    if current_pageUrl_origin not in self.adPageUrlOriginArray:
                        self.adPageUrlOriginArray.append(current_pageUrl_origin)

                    await self.adsUtil.ads_run()
                    # await self.baseSetNew.page_randomSwipe()
            else:
                await self.my_print("other_page - 广告页面已经浏览时长超过" + str(self.other_page_time) + "s")
                ads_task_data = await self.adsUtil.result()
                await self.my_print("ads_task_data:",ads_task_data)
                await self.adsUtil.stop()
                if self.taskPageViewOver:
                    await self.my_print("other_page - 任务完成，结束任务")
                    self.taskFinish = True
                else:
                    await self.my_print("other_page - 任务未完成，返回上一页")
                    need_back = True
                    while need_back:
                        current_pageUrl = self.page.url
                        if current_pageUrl.startswith(self.index_page_host) or current_pageUrl.startswith(self.child_page_host):
                            need_back = False
                        else:
                            await self.my_print("other_page - 当前页面不是主页，继续返回 - url:",current_pageUrl)
                            await self.baseSetNew.page_back()
                            await asyncio.sleep(3)
        except Exception:
            await self.my_print("广告页面异常:", str(traceback.format_exc()))

    # 广告位显示不完整，修改top和bottom
    async def ad_fixed_repair(self):
        try:
            await self.my_print("ad_fixed_repair")
            current_pageUrl = self.page.url
            if "google_vignette" in current_pageUrl:
                await self.my_print("ad_fixed_repair - google_vignette页面，不做修改")
            else:
                visualViewport_height = self.visualViewport_height
                await self.my_print("visualViewport_height:", visualViewport_height)
                gpt_unit_list = await self.page.query_selector_all("[id*='gpt_unit']")
                await self.my_print("页面gpt_unit个数:", len(gpt_unit_list))
                for gpt_unit in gpt_unit_list:
                    gpt_unit_id = await gpt_unit.get_attribute("id")
                    position = await self.page.evaluate("ele => window.getComputedStyle(ele).getPropertyValue('position')", gpt_unit)
                    await self.my_print("position:", position)
                    await self.my_print("gpt_unit-id:", gpt_unit_id, " -position:", position)
                    if position == "fixed":
                        google_ad_iframes = await gpt_unit.query_selector_all(self.ads_element_selector)
                        await self.my_print("元素内部ad_iframe个数:", len(google_ad_iframes))
                        for ad_element in google_ad_iframes:
                            ad_element_id = await ad_element.get_attribute(self.ads_element_attr)
                            rect = await self.page.evaluate("ele => ele.getBoundingClientRect()", ad_element)
                            width = int(rect["width"])
                            height = int(rect["height"])
                            top = int(rect["top"])
                            bottom = int(rect["bottom"])
                            data_load_complete = await ad_element.get_attribute("data-load-complete")
                            if data_load_complete is None:
                                data_load_complete = "true"
                            await self.my_print("元素内部广告id:", ad_element_id, " -width:", width, " -height:", height, " -top:", top, " -bottom:", bottom,
                                                " -data_load_complete:", data_load_complete)
                            if (width > 20) and (height > 20) and (data_load_complete == "true"):
                                await self.my_print("元素内部有广告，去修改位置")
                                if top > (visualViewport_height * 0.5):
                                    await self.my_print("底部fixed广告")
                                    # 设置6px的允许范围
                                    if (bottom - 6) > visualViewport_height:
                                        await self.my_print("底部fixed广告 - 需要修改位置")
                                        repair_top = visualViewport_height - height
                                        repair_bottom = visualViewport_height
                                        await self.my_print("repair_top:", repair_top)
                                        await self.my_print("repair_bottom:", repair_bottom)
                                        await self.page.evaluate("ele => ele.style.top='" + str(repair_top) + "px'", gpt_unit)
                                        await self.page.evaluate("ele => ele.style.bottom='" + str(repair_bottom) + "px'", gpt_unit)
        except Exception as e:
            await self.my_print("ad_fixed_repair异常:", str(traceback.format_exc()))

    # 请求判断广告位是不是可以点击
    def checkggw(self, ad_url_origin, ad_type):
        # "status": 0, // 0不点击 1点击
        status = 0
        try:
            # 百度云取HK任务：193.5.47.66
            # 百度云自己：http://10.4.50.220:38085/
            # 华为云：http://192.168.0.20:38085/
            op_time = self.task_time_max + 2 * 60
            url = (str(self.base_url) + "hwtask/checkggw?sid=" + str(self.sid) + "&gmail=" + str(self.gmail) + "&search_key=" + str(self.search_key) +
                   "&ggw=" + str(self.click_ad_id) + "&click_url=" + str(ad_url_origin) + "&ad_type=" + str(ad_type) + "&task_url_id=" + str(self.task_url_id)) + "&op_time=" + str(op_time)
            self.sync_print("checkggw - url:", url)
            headers = {"Connection": "close"}
            response = requests.get(url, headers=headers, timeout=10)
            response_object = response.json()
            self.sync_print("checkggw-response:", response_object)
            status = response_object["status"]
        except Exception as e:
            self.sync_print("checkggw异常:", str(traceback.format_exc()))
            status = 0
        self.sync_print("checkggw-status:", status)
        return status

    # H5页面操作,结束后，如何进行下一步
    async def index_page_operate_over(self, step_info):
        current_pageUrl = self.page.url
        await self.my_print("index_page_operate_over - current_pageUrl:", current_pageUrl)
        await self.my_print("index_page_operate_over - step_info:", step_info)
        if self.taskPageViewOver:
            await self.my_print(str(step_info) + " - 任务完成，结束任务")
            self.taskFinish = True
        else:
            # 有的页面可能需要返回上一页，才能点击其他子页面
            if "google_vignette" in current_pageUrl:
                await self.my_print(str(step_info) + " - 任务未完成,google_vignette,返回上一页，点击子页面")
                await self.baseSetNew.page_back()
            elif self.play_game and current_pageUrl.startswith(self.play_game_game_page_url):
                await self.my_print(str(step_info) + " - 任务未完成,playGame,返回上一页，点击子页面")
                await self.baseSetNew.page_back()
            else:
                if (self.index_page_host != self.child_page_host) and (
                        current_pageUrl.startswith(self.child_page_host)):
                    await self.my_print(str(step_info) + " - 任务未完成，返回上一页，点击子页面")
                    await self.baseSetNew.page_back()
                else:
                    await self.my_print(str(step_info) + " - 任务未完成，点击子页面")
                    await self.click_child_page()

    # H5页面操作

    async def index_page_operate(self):
        await self.my_print("index_page_operate - taskPageViewOver:", self.taskPageViewOver)
        current_pageUrl = self.page.url
        await self.my_print("index_page_operate - pageUrl:", current_pageUrl)

        current_pageUrl_taskTime = self.task_page_duration[0]
        if current_pageUrl in self.pageUrlArray:
            index = self.pageUrlArray.index(current_pageUrl)
            # 需要浏览2个页面，意外跳转到了第3个页面，index = 2
            if index in range(len(self.task_page_duration)):
                current_pageUrl_taskTime = self.task_page_duration[index]

        current_pageUrl_time = 0
        if current_pageUrl in self.pageTimeObject:
            current_pageUrl_time = self.pageTimeObject[current_pageUrl]

        await self.my_print("index_page_operate - task_page_duration:", self.task_page_duration)
        await self.my_print("index_page_operate - pageUrlArray:", self.pageUrlArray)
        await self.my_print("页面地址:", current_pageUrl, " - 要求浏览时长:", current_pageUrl_taskTime,
                            " - 已经浏览时长:", current_pageUrl_time)
        await self.ad_fixed_repair()
        if current_pageUrl_time < current_pageUrl_taskTime:
            await self.my_print("页面浏览时长没有达到，继续浏览")
            # 判断页面有没有广告，有广告去浏览广告
            currentPage_adShowArray = []
            google_ad_iframes = await self.page.query_selector_all(self.ads_element_selector)
            await self.my_print("页面ad_iframe个数:", len(google_ad_iframes))
            for ad_element in google_ad_iframes:
                ad_element_id = await ad_element.get_attribute(self.ads_element_attr)
                rect = await self.page.evaluate("ele => ele.getBoundingClientRect()", ad_element)
                width = int(rect["width"])
                height = int(rect["height"])
                data_load_complete = await ad_element.get_attribute("data-load-complete")
                if data_load_complete is None:
                    # 某些链接的广告不是iframe，也没有data_load_complete属性
                    data_load_complete = "true"
                await self.my_print("广告id:", ad_element_id, " -width:", width, " -height:", height,
                                    " -data_load_complete:", data_load_complete)
                if (width > 20) and (height > 20) and (data_load_complete == "true"):
                    if "google_vignette" in current_pageUrl:
                        is_fullScreenAd = False
                        if self.full_screen_ads_by_id:
                            await self.my_print("google_vignette页面，通过id判断")
                            for fullScreenAd in self.full_screen_ads_arr:
                                if fullScreenAd in ad_element_id:
                                    is_fullScreenAd = True
                        else:
                            await self.my_print("google_vignette页面，通过style判断")
                            style_width = await self.page.evaluate("ele => ele.style.width", ad_element)
                            style_height = await self.page.evaluate("ele => ele.style.height", ad_element)
                            await self.my_print("style_width:", style_width, " - style_height：", style_height)
                            if ("100vw" in style_width) or ("100vh" in style_height):
                                is_fullScreenAd = True
                        if is_fullScreenAd:
                            pageUrlArray_len = len(self.pageUrlArray)
                            pageUrlArray_len_id = str(pageUrlArray_len) + "@" + ad_element_id
                            await self.my_print("广告id:", pageUrlArray_len_id)
                            if pageUrlArray_len_id not in self.adShowArray:
                                self.adShowArray.append(pageUrlArray_len_id)
                            currentPage_adShowArray.append(ad_element_id)
                    else:
                        pageUrlArray_len = len(self.pageUrlArray)
                        pageUrlArray_len_id = str(pageUrlArray_len) + "@" + ad_element_id
                        await self.my_print("广告id:", pageUrlArray_len_id)
                        if pageUrlArray_len_id not in self.adShowArray:
                            self.adShowArray.append(pageUrlArray_len_id)
                        currentPage_adShowArray.append(ad_element_id)

            currentPage_adShowArray_len = len(currentPage_adShowArray)
            if currentPage_adShowArray_len > 0:
                await self.my_print("页面浏览时长没有达到 - 页面有广告，广告个数:", currentPage_adShowArray_len,
                                    " - 去浏览广告")
                scrollToAdIndex = 0
                if current_pageUrl in self.scrollToAdIndexObject:
                    scrollToAdIndex = self.scrollToAdIndexObject[current_pageUrl]
                else:
                    self.scrollToAdIndexObject[current_pageUrl] = scrollToAdIndex
                await self.my_print("广告个数:", currentPage_adShowArray_len, " - scrollToAdIndex:", scrollToAdIndex)
                if scrollToAdIndex <= (currentPage_adShowArray_len - 1):
                    await self.my_print("每个广告没有浏览完成 - 浏览广告:", scrollToAdIndex)
                    scrollToAdId = currentPage_adShowArray[scrollToAdIndex]
                    scrollAdLocator = "[" + str(self.ads_element_attr) + "='" + str(scrollToAdId) + "']"
                    await self.my_print("浏览广告-index:", scrollToAdIndex, " - id:", scrollAdLocator)
                    scrollToAd_element = await self.page.query_selector(scrollAdLocator)
                    if scrollToAd_element is not None:
                        scrollToAdIndex = scrollToAdIndex + 1
                        self.scrollToAdIndexObject[current_pageUrl] = scrollToAdIndex
                        # 顶部有广告遮挡，不要用block:'start'
                        await self.page.evaluate("ele => ele.scrollIntoView({block:'center'})", scrollToAd_element)
                else:
                    await self.my_print("每个广告浏览完成 - 随机滑动")
                    await self.baseSetNew.page_randomSwipe()
            else:
                await self.my_print("页面浏览时长没有达到 - 页面无广告 - 随机滑动")
                await self.baseSetNew.page_randomSwipe()
        else:
            await self.my_print("页面浏览时长完成")
            # 判断当前页面是否已经点击了广告
            if not (current_pageUrl in self.clickAdIdObject):
                await self.my_print("页面浏览时长完成 - 当前页面还未点击过广告")
                # 页面浏览时长完成，去记录当前页面的广告，并且判断是否需要点击广告
                currentPage_adShowArray = []
                currentPage_adInfoObject = {}
                currentPage_adTypeObject = {}
                google_ad_iframes = await self.page.query_selector_all(self.ads_element_selector)
                await self.my_print("页面ad_iframe个数:", len(google_ad_iframes))
                for ad_element in google_ad_iframes:
                    ad_element_id = await ad_element.get_attribute(self.ads_element_attr)
                    rect = await self.page.evaluate("ele => ele.getBoundingClientRect()", ad_element)
                    width = int(rect["width"])
                    height = int(rect["height"])
                    data_load_complete = await ad_element.get_attribute("data-load-complete")
                    if data_load_complete is None:
                        # 某些链接的广告不是iframe，也没有data_load_complete属性
                        data_load_complete = "true"
                    await self.my_print("广告id:", ad_element_id, " -width:", width, " -height:", height,
                                        " -data_load_complete:", data_load_complete)
                    if (width > 20) and (height > 20) and (data_load_complete == "true"):
                        if "google_vignette" in current_pageUrl:
                            is_fullScreenAd = False
                            if self.full_screen_ads_by_id:
                                await self.my_print("google_vignette页面，通过id判断")
                                for fullScreenAd in self.full_screen_ads_arr:
                                    if fullScreenAd in ad_element_id:
                                        is_fullScreenAd = True
                            else:
                                await self.my_print("google_vignette页面，通过style判断")
                                style_width = await self.page.evaluate("ele => ele.style.width", ad_element)
                                style_height = await self.page.evaluate("ele => ele.style.height", ad_element)
                                await self.my_print("style_width:", style_width, " - style_height：", style_height)
                                if ("100vw" in style_width) or ("100vh" in style_height):
                                    is_fullScreenAd = True
                            if is_fullScreenAd:
                                pageUrlArray_len = len(self.pageUrlArray)
                                pageUrlArray_len_id = str(pageUrlArray_len) + "@" + ad_element_id
                                await self.my_print("广告id:", pageUrlArray_len_id)
                                if pageUrlArray_len_id not in self.adShowArray:
                                    self.adShowArray.append(pageUrlArray_len_id)
                                currentPage_adShowArray.append(ad_element_id)

                                # ad元素对应的跳转地址
                                ad_element_aHref = await self.find_element_inner_a_href(ad_element)
                                await self.my_print("广告id:", pageUrlArray_len_id, " -对应href:", ad_element_aHref)

                                ad_element_adurl = await self.query_adurl(ad_element_aHref)
                                await self.my_print("广告id:", pageUrlArray_len_id, " -对应adurl:", ad_element_adurl)

                                # 对应二次确认: ['179-79']
                                element_confirm_btn = await self.find_element_confirm_btn(ad_element)
                                await self.my_print("广告id:", pageUrlArray_len_id, " -对应二次确认:", element_confirm_btn)
                                ad_confirm = 0
                                if len(element_confirm_btn) != 0:
                                    ad_confirm = 1
                                # 广告类型
                                if "intent://" in ad_element_aHref:
                                    ad_element_adtype = "openApp"
                                    await self.my_print("广告id:", pageUrlArray_len_id, " -广告类型:", ad_element_adtype)
                                else:
                                    ad_element_adtype = await self.check_ad_element_adtype(pageUrlArray_len_id, ad_element)
                                    await self.my_print("广告id:", pageUrlArray_len_id, " -广告类型:", ad_element_adtype)

                                ad_element_adurl_type_confirm = str(ad_element_adurl) + "##" + str(ad_element_adtype) + "##" + str(ad_confirm)
                                if ad_element_id in self.adShowUrlObject:
                                    adShowUrlObject_item_array: list = self.adShowUrlObject[ad_element_id]
                                    if ad_element_adurl_type_confirm not in adShowUrlObject_item_array:
                                        adShowUrlObject_item_array.append(ad_element_adurl_type_confirm)
                                else:
                                    adShowUrlObject_item_array = [ad_element_adurl_type_confirm]
                                    self.adShowUrlObject[ad_element_id] = adShowUrlObject_item_array

                                # 记录当前页面的广告元素，对应的广告信息（类型和二次确认）
                                # 如果当前页面有需要点击的id，click_ad_id_info获取对应的广告信息，在点击成功的url后添加
                                currentPage_adInfoObject[ad_element_id] = ("##" + str(ad_element_adtype) + "##" + str(ad_confirm))
                                currentPage_adTypeObject[ad_element_id] = str(ad_element_adtype)

                                # 记录本次任务点击的广告位对应的ad_url，如果点击成功，上报
                                if self.click_success_url == "":
                                    if ad_element_id == self.ggw_click:
                                        if ad_element_adurl != "":
                                            parsed_url = urlparse(ad_element_adurl)
                                            self.click_url = parsed_url.netloc
                                            self.click_url_full = ad_element_aHref
                                        else:
                                            self.click_url = "www.lwb.com"
                                            self.click_url_full = "https://www.lwb.com"
                        else:
                            pageUrlArray_len = len(self.pageUrlArray)
                            pageUrlArray_len_id = str(pageUrlArray_len) + "@" + ad_element_id
                            await self.my_print("广告id:", pageUrlArray_len_id)
                            if pageUrlArray_len_id not in self.adShowArray:
                                self.adShowArray.append(pageUrlArray_len_id)
                            currentPage_adShowArray.append(ad_element_id)

                            ad_element_aHref = await self.find_element_inner_a_href(ad_element)
                            await self.my_print("广告id:", pageUrlArray_len_id, " -对应href:", ad_element_aHref)

                            ad_element_adurl = await self.query_adurl(ad_element_aHref)
                            await self.my_print("广告id:", pageUrlArray_len_id, " -对应adurl:", ad_element_adurl)

                            element_confirm_btn = await self.find_element_confirm_btn(ad_element)
                            # 对应二次确认: ['179-79']
                            await self.my_print("广告id:", pageUrlArray_len_id, " -对应二次确认:", element_confirm_btn)
                            ad_confirm = 0
                            if len(element_confirm_btn) != 0:
                                ad_confirm = 1

                            # 广告类型
                            if "intent://" in ad_element_aHref:
                                ad_element_adtype = "openApp"
                                await self.my_print("广告id:", pageUrlArray_len_id, " -广告类型:", ad_element_adtype)
                            else:
                                ad_element_adtype = await self.check_ad_element_adtype(pageUrlArray_len_id, ad_element)
                                await self.my_print("广告id:", pageUrlArray_len_id, " -广告类型:", ad_element_adtype)

                            ad_element_adurl_type_confirm = str(ad_element_adurl) + "##" + str(ad_element_adtype) + "##" + str(ad_confirm)
                            if ad_element_id in self.adShowUrlObject:
                                adShowUrlObject_item_array: list = self.adShowUrlObject[ad_element_id]
                                if ad_element_adurl_type_confirm not in adShowUrlObject_item_array:
                                    adShowUrlObject_item_array.append(ad_element_adurl_type_confirm)
                            else:
                                adShowUrlObject_item_array = [ad_element_adurl_type_confirm]
                                self.adShowUrlObject[ad_element_id] = adShowUrlObject_item_array

                            # 记录当前页面的广告元素，对应的广告信息（类型和二次确认）
                            # 如果当前页面有需要点击的id，click_ad_id_info获取对应的广告信息，在点击成功的url后添加
                            currentPage_adInfoObject[ad_element_id] = ("##" + str(ad_element_adtype) + "##" + str(ad_confirm))
                            currentPage_adTypeObject[ad_element_id] = str(ad_element_adtype)

                            # 记录本次任务点击的广告位对应的ad_url，如果点击成功，上报
                            if self.click_success_url == "":
                                if ad_element_id == self.ggw_click:
                                    if ad_element_adurl != "":
                                        parsed_url = urlparse(ad_element_adurl)
                                        self.click_url = parsed_url.netloc
                                        self.click_url_full = ad_element_aHref
                                    else:
                                        self.click_url = "www.lwb.com"
                                        self.click_url_full = "https://www.lwb.com"

                currentPage_adShowArray_len = len(currentPage_adShowArray)
                if currentPage_adShowArray_len > 0:
                    await self.my_print("页面有广告，广告个数:", currentPage_adShowArray_len)

                    await self.my_print("需要点击的广告位:", self.ggw_click)
                    # 如果广告位在多个页面出现，只要没有点击成功，就继续判断是否要点击
                    # 指定点击广告位，视频广告点击概率70%，0-70（判断是广告位是视频才点），71-100（不管是不是都点）
                    # 如果广告位是other，在没有配置的广告位中，选择一个点击
                    if self.click_success_url == "":
                        await self.my_print("需要点击的广告位:", self.ggw_click, " -还未点击成功，去点击")
                        self.click_ad_id = ""
                        if self.ggw_click == "other":
                            await self.my_print("需要点击的广告位是other，在未配置的广告位中，随机一个")
                            set_ggw_list = []
                            for ggw_ggw in self.ggw:
                                if ggw_ggw != "other":
                                    set_ggw_list.append(ggw_ggw)
                            await self.my_print("已经配置的广告位:", set_ggw_list)
                            await self.my_print("页面的广告位:", currentPage_adShowArray)
                            currentPage_ad_no_set = []
                            for currentPage_ad in currentPage_adShowArray:
                                if currentPage_ad not in set_ggw_list:
                                    currentPage_ad_no_set.append(currentPage_ad)
                            await self.my_print("未配置的广告位数组:", currentPage_ad_no_set)
                            if len(currentPage_ad_no_set) > 0:
                                self.click_ad_id = random.choice(currentPage_ad_no_set)
                                await self.my_print("随机一个未配置的广告位:", self.click_ad_id)
                        else:
                            self.click_ad_id = self.ggw_click
                        await self.my_print("页面点击的广告位:", self.click_ad_id)
                        if self.click_ad_id in currentPage_adShowArray:
                            await self.my_print("click_ad_id", self.click_ad_id)
                            # 记录点击的广告id，防止同一个页面每次点击的不一样
                            if current_pageUrl in self.clickAdIdObject:
                                self.click_ad_id = self.clickAdIdObject[current_pageUrl]
                            else:
                                self.clickAdIdObject[current_pageUrl] = self.click_ad_id
                            clickAdLocator = "[" + str(self.ads_element_attr) + "='" + str(self.click_ad_id) + "']"
                            await self.my_print("点击广告:", clickAdLocator)

                            await self.my_print("点击广告的ad_url:", self.click_url)
                            # 请求服务，判断是不是要点击
                            click_ad_id_type = currentPage_adTypeObject[self.click_ad_id]
                            await self.my_print("广告位:", self.click_ad_id, " - 广告类型:", click_ad_id_type)

                            checkggw_status = self.checkggw(self.click_url, click_ad_id_type)
                            checkggw_status = 1
                            await self.my_print("广告位:", self.click_ad_id, " - status:", checkggw_status)
                            if checkggw_status == 1:
                                self.click_ad_id_info = currentPage_adInfoObject[self.click_ad_id]
                                await self.my_print("广告位:", self.click_ad_id, " - 可以点击，广告信息:", self.click_ad_id_info)
                                # 记录每个页面点击的广告id
                                pageUrlArray_len = len(self.pageUrlArray)
                                pageUrlArray_len_clickAdId = str(pageUrlArray_len) + "@" + self.click_ad_id
                                if pageUrlArray_len_clickAdId not in self.clickAdIdArray:
                                    self.clickAdIdArray.append(pageUrlArray_len_clickAdId)

                                adIframeLinkXYObject = await self.find_ad_iframe_link_xy(clickAdLocator)
                                await self.my_print("广告id:", clickAdLocator, " - 点击坐标:", adIframeLinkXYObject)
                                if len(adIframeLinkXYObject) == 0:
                                    await self.my_print("广告id:", clickAdLocator, " - 没有找到点击坐标")
                                    # 万一没有找到点击坐标，当作已经点击过了，继续任务
                                    self.someLog[current_pageUrl] = "没有找到点击坐标"
                                else:
                                    anchor_a = adIframeLinkXYObject["anchor_a"]
                                    normal_a = adIframeLinkXYObject["normal_a"]
                                    if len(anchor_a) != 0:
                                        # 广告内部有二次确认按钮，先去点击普通a标签，等二次确认按钮出现，再次点击二次确认按钮
                                        if len(normal_a) != 0:
                                            await self.my_print("二次确认按钮，有普通a标签，先去点击普通a标签")
                                            clickXY = random.choice(normal_a)
                                            clickXYList = clickXY.split("-")
                                            clickX = clickXYList[0]
                                            clickY = clickXYList[1]
                                            await self.my_print("普通a元素 - clickX:", clickX, " - clickY:", clickY)
                                            await self.baseSetNew.page_click(clickX, clickY)
                                            await self.my_print("普通a元素 - 点击后等待5s")
                                            await asyncio.sleep(5)
                                            adIframeLinkXYObject2 = await self.find_ad_iframe_link_xy(clickAdLocator)
                                            await self.my_print("广告id:", clickAdLocator, " - 点击坐标2:",
                                                                adIframeLinkXYObject2)
                                            anchor_a = adIframeLinkXYObject2["anchor_a"]
                                            normal_a = adIframeLinkXYObject2["normal_a"]
                                            if len(anchor_a) != 0:
                                                await self.my_print("二次确认按钮，点击普通a标签后，二次按钮出现")
                                                clickXY = random.choice(anchor_a)
                                                clickXYList = clickXY.split("-")
                                                clickX = clickXYList[0]
                                                clickY = clickXYList[1]
                                                await self.my_print("二次按钮 - clickX:", clickX, " - clickY:", clickY)
                                                try:
                                                    async with self.page.expect_navigation(timeout=60000, wait_until="domcontentloaded"):
                                                        await self.baseSetNew.page_click(clickX, clickY)
                                                except Exception as e:
                                                    await self.my_print("点击广告异常:", str(traceback.format_exc()))
                                            else:
                                                await self.my_print("二次确认按钮，点击普通a标签后，二次按钮没有出现")
                                                if len(normal_a) != 0:
                                                    clickXY = random.choice(normal_a)
                                                    clickXYList = clickXY.split("-")
                                                    clickX = clickXYList[0]
                                                    clickY = clickXYList[1]
                                                    await self.my_print("普通a元素 - clickX:", clickX, " - clickY:", clickY)
                                                    try:
                                                        async with self.page.expect_navigation(timeout=60000, wait_until="domcontentloaded"):
                                                            await self.baseSetNew.page_click(clickX, clickY)
                                                    except Exception as e:
                                                        await self.my_print("点击广告异常:", str(traceback.format_exc()))
                                        else:
                                            await self.my_print("二次确认按钮，没有普通a标签，点击二次确认按钮")
                                            clickXY = random.choice(anchor_a)
                                            clickXYList = clickXY.split("-")
                                            clickX = clickXYList[0]
                                            clickY = clickXYList[1]
                                            await self.my_print("二次确认按钮 - clickX:", clickX, " - clickY:", clickY)
                                            try:
                                                async with self.page.expect_navigation(timeout=60000, wait_until="domcontentloaded"):
                                                    await self.baseSetNew.page_click(clickX, clickY)
                                            except Exception as e:
                                                await self.my_print("点击广告异常:", str(traceback.format_exc()))
                                    else:
                                        await self.my_print("没有二次确认按钮，点击普通a标签")
                                        if len(normal_a) != 0:
                                            # 普通a标签，随机取一个
                                            await self.my_print("点击普通a元素")
                                            clickXY = random.choice(normal_a)
                                            clickXYList = clickXY.split("-")
                                            clickX = clickXYList[0]
                                            clickY = clickXYList[1]
                                            await self.my_print("普通a元素 - clickX:", clickX, " - clickY:", clickY)
                                            try:
                                                async with self.page.expect_navigation(timeout=60000, wait_until="domcontentloaded"):
                                                    await self.baseSetNew.page_click(clickX, clickY)
                                            except Exception as e:
                                                await self.my_print("点击广告异常:", str(traceback.format_exc()))
                            else:
                                await self.my_print("广告位不可以点击")
                                await self.index_page_operate_over("广告位不可以点击")
                        else:
                            await self.my_print("需要点击的广告位，不在此页面")
                            await self.index_page_operate_over("需要点击的广告位，不在此页面")
                    else:
                        await self.my_print("需要点击的广告位，已经点击过")
                        await self.index_page_operate_over("需要点击的广告位，已经点击过")
                else:
                    await self.my_print("页面无广告")
                    await self.index_page_operate_over("页面无广告")
            else:
                await self.my_print("页面浏览时长完成 - 当前页面已经点击过广告")
                await self.index_page_operate_over("已经点击过广告")

    # 跳转子页面

    async def click_child_page(self):
        await self.my_print("click_child_page")
        current_pageUrl = self.page.url
        await self.my_print("click_child_page - pageUrl:", current_pageUrl)

        childPageElementArray = []

        is_click_random = random.randint(1, 10000)
        await self.my_print("is_click_random:", is_click_random)

        if self.category and (current_pageUrl == self.category_index_page_url) and (
                is_click_random <= self.category_click):
            await self.my_print("去点击category:", self.category_btn_selector)
            childPageNodeList = await self.page.query_selector_all(self.category_btn_selector)
        elif self.play_game and current_pageUrl.startswith(self.play_game_page_url) and (
                is_click_random <= self.play_game_click):
            await self.my_print("去点击playGame:", self.play_game_btn_selector)
            childPageNodeList = await self.page.query_selector_all(self.play_game_btn_selector)
        elif self.category and current_pageUrl.startswith(self.category_category_page_url):
            await self.my_print("在category页面，去选择category页面a元素:", self.category_child_page_link_selector)
            childPageNodeList = await self.page.query_selector_all(self.category_child_page_link_selector)
        else:
            await self.my_print("选择子页面a元素:", self.child_page_link_selector)
            childPageNodeList = await self.page.query_selector_all(self.child_page_link_selector)

        if len(childPageNodeList) == 0:
            await self.my_print("childPageNodeList - 没有元素，重新选择")
            childPageNodeList = await self.page.query_selector_all(self.child_page_link_selector2)

        await self.my_print("childPageNodeList:", len(childPageNodeList))
        for childPageNode in childPageNodeList:
            if childPageNode is not None:
                rect = await self.page.evaluate("ele => ele.getBoundingClientRect()", childPageNode)
                width = int(rect["width"])
                height = int(rect["height"])
                left = int(rect["left"])
                right = int(rect["right"])
                if (width > 0) and (height > 0) and (0 <= left < self.screen_width) and (
                        0 <= right < self.screen_width):
                    childPageElementArray.append(childPageNode)
        childPageElementArray_len = len(childPageElementArray)
        await self.my_print("childPageElementArray_len:", childPageElementArray_len)
        if childPageElementArray_len > 0:
            childPageElement = random.choice(childPageElementArray)
            await self.my_print("点击子页面元素:", childPageElement)
            if childPageElement is not None:
                await self.my_print("滑动")
                await self.page.evaluate("ele => ele.scrollIntoView({block:'center'})", childPageElement)
                # await self.swipe_position(childPageElement, [])
                await self.page.wait_for_timeout(2000)
                await self.page.evaluate('ele =>  ele.style.border = "1px solid red"', childPageElement)
                box = await childPageElement.bounding_box()
                if box is not None:
                    left = box["x"]
                    top = box["y"]
                    rect = await self.page.evaluate("ele => ele.getBoundingClientRect()", childPageElement)
                    width = int(rect["width"])
                    height = int(rect["height"])
                    await self.my_print("点击子页面 -left:", left, " -top:", top, " -width:", width, " -height:",
                                        height)
                    x = int(left + width * 0.5)
                    y = int(top + height * 0.5)
                    await self.my_print("点击子页面 -x:", x, " -y:", y)
                    try:
                        async with self.page.expect_navigation(timeout=60000, wait_until="domcontentloaded"):
                            await self.baseSetNew.page_click(x, y)
                    except Exception as e:
                        await self.my_print("点击子页面异常:", str(traceback.format_exc()))

    # 查找页面异常情况
    async def page_error_text(self):
        await self.my_print("page_error_text")
        current_pageUrl = self.page.url
        error_text_list = ["403 forbidden", "no internet", "not be reached", "provide a secure connection", "sent an invalid response", "err_ssl_protocol_error"]
        try:
            page_body = await self.page.query_selector("body")
            if page_body is not None:
                page_body_text = await page_body.inner_text()
                page_body_text = page_body_text.lower()
                page_body_text = page_body_text.replace("\n", "")
                for error_text in error_text_list:
                    if error_text in page_body_text:
                        self.page_error_text_object[current_pageUrl] = page_body_text
                        break
        except Exception as e:
            await self.my_print("page_error_text异常:", str(traceback.format_exc()))

    # 清除通知栏通知
    async def clear_notification(self):
        await self.my_print("clear_notification")
        try:
            local_sid_port = str(self.sid) + ":5555"
            if local_sid_port in huawei_phone_sid_object:
                huawei_sid_port = huawei_phone_sid_object[local_sid_port]
                clearCommand = "adb -s " + huawei_sid_port + " shell am broadcast -a android.intent.action.CLOSE_SYSTEM_DIALOGS"
            else:
                clearCommand = "adb -s " + local_sid_port + " shell am broadcast -a android.intent.action.CLOSE_SYSTEM_DIALOGS"
            await self.my_print("clear_notification命令:", clearCommand)
            subprocess.call(clearCommand, shell=True)
        except Exception as e:
            await self.my_print("clear_notification异常:", str(traceback.format_exc()))

    # 获取屏幕宽高

    async def get_screen(self):
        screenWidth = 360
        screenHeight = 640
        # 点击的时候，注意区别手机真实的分辨率
        visualViewport_width = await self.page.evaluate("window.visualViewport.width")
        visualViewport_height = await self.page.evaluate("window.visualViewport.height")
        await self.my_print("visualViewport_width:", visualViewport_width, " - visualViewport_height:", visualViewport_height)
        self.visualViewport_width = visualViewport_width
        self.visualViewport_height = visualViewport_height
        if visualViewport_width == 360:
            screenWidth = 360
            screenHeight = 640
        if visualViewport_width == 540:
            screenWidth = 540
            screenHeight = 960
        self.screen_width = screenWidth
        self.screen_height = screenHeight
        await self.my_print(f'获取屏幕宽高, 宽:{self.screen_width} - 高:{self.screen_height}')

    # 请求图片点击热点
    async def ad_img_request(self, img_bytes):
        await self.my_print("ad_img_request")
        await self.get_screen()
        self.baseSetNew = BaseSetNew(self.page, self.sid, self.websocket_client, self.session_id, self.real_metrics_width,
                                     self.real_metrics_height, self.metrics_width, self.metrics_height, self.screen_width, self.screen_height,
                                     self.visualViewport_width, self.visualViewport_height)
        self.js_userAgent = await self.page.evaluate("navigator.userAgent")
        url = "http://38.181.57.75/api/v1/image/textDetect"
        headers = {"Content-Type": "application/json",
                   "Connection": "close",
                   "User-Agent": self.js_userAgent}
        await self.my_print("headers:", headers)

        encoded_string = base64.b64encode(img_bytes).decode()

        encoded_string = "data:image/png;base64," + encoded_string
        data = {
            "file": encoded_string,
            "only_one": 1
        }
        # data = {
        #     "file": encoded_string
        # }
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data, headers=headers) as resp:
                result = await resp.text()
                await self.my_print(result)
                result_object = json.loads(result)

        if "data" in result_object:
            data = result_object["data"]
            data_list = data["list"]
            for item in data_list:
                await self.my_print("item:", item)
                clickX = item["x"]
                clickY = item["y"]
                await self.my_print("clickX:", clickX, " - clickY:", clickY)
                local_sid_port = str(self.sid) + ":5555"
                if local_sid_port in huawei_phone_sid_object:
                    huawei_sid_port = huawei_phone_sid_object[local_sid_port]
                    clickCommand = "adb -s " + huawei_sid_port + " shell input tap " + str(clickX) + " " + str(clickY)
                else:
                    clickCommand = "adb -s " + str(self.sid) + ":5555 shell input tap " + str(clickX) + " " + str(clickY)
                await self.my_print("adb点击:", clickCommand)
                subprocess.call(clickCommand, shell=True)
                await asyncio.sleep(5)
                await self.my_print("点击方法点击")
                await self.baseSetNew.adImage_click(clickX, clickY)
                await asyncio.sleep(5)
        await self.delete_ad_img()

    def test(self):
        self.sync_print("test")
        url = "http://38.181.57.75/api/v1/image/textDetect"
        headers = {"Content-Type": "application/json",
                   "Connection": "close",
                   "User-Agent": self.js_userAgent}
        self.sync_print("headers:", headers)

        with open("example.png", "rb") as image_file:
            encoded_string = base64.encodebytes(image_file.read()).decode('utf-8')

        encoded_string = "data:image/png;base64," + encoded_string
        data = {"file": encoded_string}
        res = requests.post(url, headers=headers, json=data)
        res_dict = res.json()
        self.sync_print("res_dict:", res_dict)

    # 加载ads工具
    def ads_init(self):
        if self.enable_ads:
            adsParams = {
                "sid": self.sid,
                "enable_log": self.enable_log,
                "index_page_host": self.index_page_host,
                "child_page_host": self.child_page_host,
            }
            self.adsUtil = AdsUtil(adsParams)
            self.sync_print("ads初始化完成")

    # 程序运行

    async def task_run(self, p: Playwright, enable_log=False):
        await self.my_print('任务开始运行-PublicUtils_new')
        # 是否启用日志功能
        if enable_log:
            await self.my_print_not_log('开启日志功能')
            await self.setup_logger_factory()
            await self.my_print_not_log('日志功能已启用')
            self.enable_log = True
        else:
            await self.my_print_not_log('日志功能已禁用')
            self.enable_log = False
        await self.assign_playwright(p)
        self.jsTime = "20240106-1659_new"
        await self.my_print("jsTime:", self.jsTime)
        await self.my_print("sid:", self.sid)
        await self.my_print("device_port:", self.device_port)
        await self.my_print("ad_base_url:", self.ad_base_url)
        await self.my_print("RealMetrics_Width:", self.real_metrics_width)
        await self.my_print("RealMetrics_Height:", self.real_metrics_height)
        await self.my_print("Metrics_Width:", self.metrics_width)
        await self.my_print("Metrics_Height:", self.metrics_height)
        await self.my_print("task_page_duration:", self.task_page_duration)
        await self.my_print("task_click_rate:", self.task_click_rate)
        await self.my_print("task_page_view:", self.task_page_view)
        await self.my_print("taskTime_max:", self.task_time_max)
        # 页面控制参数
        await self.my_print("index_page_host:", self.index_page_host)
        await self.my_print("child_page_host:", self.child_page_host)
        await self.my_print("img_url_host_arr:", self.img_url_host_arr)
        await self.my_print("block_url_type:", self.block_url_type)
        await self.my_print("ads_element_selector:", self.ads_element_selector)
        await self.my_print("ads_element_attr:", self.ads_element_attr)
        await self.my_print("child_page_link_selector:", self.child_page_link_selector)
        await self.my_print("child_page_link_selector2:", self.child_page_link_selector2)
        await self.my_print("category:", self.category)
        await self.my_print("category_click:", self.category_click)
        await self.my_print("category_index_page_url:", self.category_index_page_url)
        await self.my_print("category_child_page_link_selector:", self.category_child_page_link_selector)
        await self.my_print("category_btn_selector:", self.category_btn_selector)
        await self.my_print("category_category_page_url:", self.category_category_page_url)
        await self.my_print("play_game:", self.play_game)
        await self.my_print("play_game_click:", self.play_game_click)
        await self.my_print("play_game_page_url:", self.play_game_page_url)
        await self.my_print("play_game_btn_selector:", self.play_game_btn_selector)
        await self.my_print("play_game_game_page_url:", self.play_game_game_page_url)
        await self.my_print("full_screen_ads_by_id:", self.full_screen_ads_by_id)
        await self.my_print("full_screen_ads_arr:", self.full_screen_ads_arr)
        await self.my_print("gmail:", self.gmail)
        await self.my_print("search_key:", self.search_key)
        await self.my_print("task_url_id:", self.task_url_id)
        await self.my_print("base_url:", self.base_url)
        # 广告位
        self.ggw_click = "google_ads_iframe_/21623892435,22666680030/meagame.com_0105_rs_320x50_1_0"
        await self.my_print("ggw_click:", self.ggw_click)
        # 绑定手机和端口
        await self.forward()
        await self.http_get()

        cpd_url = "http://localhost:" + str(self.device_port)
        self.browser = await self.playwright.chromium.connect_over_cdp(cpd_url)
        num_contexts = len(self.browser.contexts)
        await self.my_print("num_contexts:", num_contexts)
        if num_contexts == 0:
            self.context = await self.browser.new_context()
        else:
            self.context = self.browser.contexts[0]

        await self.context.route("**", self.route_image)
        num_pages = len(self.context.pages)
        await self.my_print("num_pages:", num_pages)
        if num_pages == 0:
            self.page = await self.context.new_page()
        else:
            self.page = self.context.pages[0]

        self.context.set_default_timeout(90000)
        self.page.set_default_timeout(90000)
        self.page.set_default_navigation_timeout(90000)

        # await self.my_print("开始测试")
        # await self.page.goto("https://user.gardensdog.com/ad_img_test.html")
        # await self.page.wait_for_timeout(10000)
        # adImg = await self.page.query_selector("[id='adImg']")
        # if adImg is not None:
        #     await self.my_print("adImg")
        #     rect = await self.page.evaluate("ele => ele.getBoundingClientRect()", adImg)
        #     await self.my_print("adImg rect:", rect)
        #     screenshot_bytes = await adImg.screenshot()
        #     await self.ad_img_request(screenshot_bytes)
        # else:
        #     await self.my_print("adImg None")
        # await self.page.wait_for_timeout(60000)

        # 打开链接前，检测ip归属地
        await self.checkIPCountry()
        await asyncio.sleep(3)
        if "country" in self.extra:
            extra_country = self.extra["country"]
            await self.my_print("extra_country:", extra_country)
            if extra_country in self.IPCountry:
                await self.my_print("检测ip符合目标国家")
            else:
                await self.my_print("检测ip不符合目标国家，结束任务")
                self.code = "-1"
                await self.finish_task()

        self.startPageTime = time.time()
        await self.page.goto(self.ad_base_url, wait_until="domcontentloaded")

        self.browser.on("disconnected", self.browser_disconnected)
        self.context.on("close", self.browser_context_close)
        self.page.on("close", self.page_close)

        while (self.nowSpendTime < self.task_time_max) and (not self.taskFinish):
            task_start_time = time.time()
            try:
                browser_is_connected = self.browser.is_connected()
                await self.my_print("browser_is_connected:", browser_is_connected)

                num_contexts = len(self.browser.contexts)
                await self.my_print("num_contexts:", num_contexts)

                if num_contexts == 0:
                    self.context = await self.browser.new_context()
                else:
                    self.context = self.browser.contexts[0]
                await self.context.route("**", self.route_image)

                self.context.set_default_timeout(90000)
                self.page.set_default_timeout(90000)
                self.page.set_default_navigation_timeout(90000)

                num_pages = len(self.context.pages)
                await self.my_print("num_pages:", num_pages)

                if (num_contexts > 0) and (num_pages > 0):
                    # 从广告页面回来，最后一个页面的page已经关闭
                    self.page = self.context.pages[num_pages - 1]
                    for page_index, context_page in enumerate(reversed(self.context.pages)):
                        page_status = context_page.is_closed()
                        await self.my_print("num_pages:", num_pages, " - 遍历:", page_index, " - 是否已经关闭:",
                                            page_status)
                        if not page_status:
                            context_page_url = context_page.url
                            await self.my_print("num_pages:", num_pages, " - 遍历:", page_index, " - 开启:",
                                                context_page_url)

                    for page_index, context_page in enumerate(reversed(self.context.pages)):
                        page_status = context_page.is_closed()
                        await self.my_print("num_pages:", num_pages, " - 遍历:", page_index, " - 是否已经关闭:",
                                            page_status)
                        if not page_status:
                            self.page = context_page
                            break

                    self.baseSetNew = BaseSetNew(self.page, self.sid, self.websocket_client, self.session_id, self.real_metrics_width,
                                                 self.real_metrics_height, self.metrics_width, self.metrics_height, self.screen_width, self.screen_height,
                                                 self.visualViewport_width, self.visualViewport_height)
                    # 清除通知栏通知
                    await self.clear_notification()

                    # try:
                    #     await self.page.wait_for_load_state("domcontentloaded")
                    # except Exception as e:
                    #     await self.my_print("等待页面加载-异常:", str(traceback.format_exc()))

                    current_pageUrl = self.page.url
                    visibilityState = "visible"
                    try:
                        visibilityState = await asyncio.wait_for(self.page.evaluate("document.visibilityState"),
                                                                 timeout=5)
                    except asyncio.TimeoutError:
                        await self.my_print("visibilityState 获取异常")
                    await self.my_print("页面加载 - pageUrl:", current_pageUrl, " -visibilityState:", visibilityState)

                    documentReadyState = "complete"
                    try:
                        documentReadyState = await asyncio.wait_for(self.page.evaluate("document.readyState"),
                                                                    timeout=5)
                    except asyncio.TimeoutError:
                        await self.my_print("documentReadyState 获取异常")
                    await self.my_print("页面加载 - pageUrl:", current_pageUrl, " -documentReadyState:",
                                        documentReadyState)

                    # 页面的一些按钮，先用js点击
                    await self.baseSetNew.some_setting()

                    current_page_status = False
                    if current_pageUrl.startswith(self.index_page_host) or (current_pageUrl.startswith(self.child_page_host)):
                        if documentReadyState == "complete":
                            current_page_status = True
                    else:
                        if documentReadyState == "interactive" or documentReadyState == "complete":
                            current_page_status = True

                    if (visibilityState == "visible") and current_page_status:
                        complete_start_time = time.time()
                        if self.indexPageCompleteTime == 0:
                            await self.my_print("页面首次加载成功，随机滑动")
                            await self.get_screen()
                            await self.baseSetNew.page_randomSwipe()
                            random_sleep = random.randint(1000, 3000)
                            await self.page.wait_for_timeout(random_sleep)
                            self.indexPageCompleteTime = time.time() - self.startPageTime
                            await self.my_print("indexPageCompleteTime:", self.indexPageCompleteTime)
                            self.js_userAgent = await self.page.evaluate("navigator.userAgent")
                            await self.my_print("js_userAgent:", self.js_userAgent)
                            self.js_language = await self.page.evaluate("navigator.language")
                            await self.my_print("js_language:", self.js_language)
                            self.js_screenWidth = await self.page.evaluate("screen.width")
                            await self.my_print("js_screenWidth:", self.js_screenWidth)
                            self.js_screenHeight = await self.page.evaluate("screen.height")
                            await self.my_print("js_screenHeight:", self.js_screenHeight)
                            self.js_devicePixelRatio = await self.page.evaluate("window.devicePixelRatio")
                            await self.my_print("js_devicePixelRatio:", self.js_devicePixelRatio)
                            self.other_page_time = random.randint(60, 300)
                            self.other_page_time = 100
                            await self.my_print("other_page_time:", self.other_page_time)
                            self.other_page_visit = random.randint(2, 5)
                            self.other_page_visit = 2
                            await self.my_print("other_page_visit:", self.other_page_visit)
                            self.ads_init()
                        await self.page_error_text()
                        await self.check_page_operate()

                        # 浏览广告后，返回前一个页面，page会已经close
                        await asyncio.sleep(10)
                        complete_end_time = time.time()
                        complete_loop_time = int(complete_end_time - complete_start_time)
                        await self.my_print("complete_start_time:", complete_start_time)
                        await self.my_print("complete_end_time:", complete_end_time)
                        await self.my_print("complete_loop_time:", complete_loop_time)
                        if current_pageUrl.startswith(self.index_page_host) or (
                                current_pageUrl.startswith(self.child_page_host)):
                            if current_pageUrl in self.pageTimeObject:
                                self.pageTimeObject[current_pageUrl] += complete_loop_time
                            else:
                                self.pageTimeObject[current_pageUrl] = complete_loop_time
                            await self.my_print("pageTimeObject:", self.pageTimeObject)
                        else:
                            if current_pageUrl.startswith("https://"):
                                # 广告页面地址，只记录主地址
                                parsed_url = urlparse(current_pageUrl)
                                current_pageUrl_origin = parsed_url.scheme + "://" + parsed_url.netloc
                                if current_pageUrl_origin in self.adPageTimeObject:
                                    self.adPageTimeObject[current_pageUrl_origin] += complete_loop_time
                                else:
                                    self.adPageTimeObject[current_pageUrl_origin] = complete_loop_time
                                await self.my_print("adPageTimeObject:", self.adPageTimeObject)
                    else:
                        if (visibilityState == "visible") and (documentReadyState == "interactive"):
                            await self.my_print("页面未完全加载，可以随机滑动")
                            await self.baseSetNew.page_randomSwipe()
                        # 浏览广告后，返回前一个页面，page会已经close
                        await asyncio.sleep(10)
                else:
                    await asyncio.sleep(10)
            except Error as error:
                await self.my_print("startPage - playwright异常:", str(traceback.format_exc()))
                await asyncio.sleep(10)
            task_end_time = time.time()
            task_loop_time = int(task_end_time - task_start_time)
            await self.my_print("task_start_time:", task_start_time)
            await self.my_print("task_end_time:", task_end_time)
            await self.my_print("task_loop_time:", task_loop_time)
            self.nowSpendTime += task_loop_time
            await self.my_print("任务进行中 - nowSpendTime:", self.nowSpendTime, " - taskTime_max:", self.task_time_max)

        await self.my_print("任务结束")
        await self.my_print("nowSpendTime:", self.nowSpendTime)
        await self.my_print("adShowArray:", self.adShowArray)
        await self.my_print("pageUrlArray:", self.pageUrlArray)
        await self.my_print("pageTimeObject:", self.pageTimeObject)
        await self.my_print("blockUrlArray:", self.blockUrlArray)
        await self.finish_task()
