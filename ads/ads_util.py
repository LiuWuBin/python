import asyncio
import copy
import hashlib
import json
import math
import random
import time
import traceback
from typing import Optional, Union
from urllib.parse import urlsplit, urlparse

from playwright.async_api import Page, ElementHandle, BrowserContext, Browser

from base_set_new import BaseSetNew
from ads.ads_config import *
from logger_factory import LoggerFactory

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


# 获取元素边界值
async def get_bounding(bounding_rect: dict):
    tag_height = round(bounding_rect['height'], 2)
    tag_width = round(bounding_rect['width'], 2)
    tag_top = round(bounding_rect['top'], 2)
    tag_left = round(bounding_rect['left'], 2)
    tag_bottom = round(bounding_rect['bottom'], 2)
    tag_right = round(bounding_rect['right'], 2)
    return tag_width, tag_height, tag_top, tag_right, tag_bottom, tag_left


class AdsUtil:
    # 浏览器对象
    browser: Optional[Browser] = None
    # 上下问对象
    context: Optional[BrowserContext] = None
    # 页对象
    page: Optional[Page] = None
    # 可点击element集合
    clickable_elements: list[ElementHandle] = []
    # 是否启用日志
    enable_log: bool = False
    # 广告页可点击选择器
    clickable_selectors: list[str] = []
    # 广告页不可点击选择器
    non_clickable_selectors: list[str] = []
    # 广告页中存在点击展示隐藏的列表
    show_selectors: list[str] = []
    # 进入页面浏览完成后退出
    back_selectors: list[str] = []
    # video
    video_selectors: list[str] = []
    # 日志对象
    logger: Optional[LoggerFactory] = None
    # sid
    sid: str = ''
    # 手机操作
    baseSetNew: Optional[BaseSetNew] = None
    # 屏幕宽
    screen_width = 0
    # 屏幕高
    screen_height = 0
    # 首页的主域名
    index_page_host = ""
    # 子页的主域名（如果和主页相同，填一样的）
    child_page_host = ""
    # 广告时长
    # ads_durations: list = []
    # 广告页面数
    # ads_visit_count: int = 1
    # 广告最大浏览时间
    ads_max_visits: int = 1
    # 加载完成后记录浏览总时长
    current_visit_seconds: int = 0
    # 当前浏览页面数
    current_visit_count: int = 0
    # 广告浏览参数
    js_handles_md5: list[str] = []
    browse_page_url: list[str] = []
    browse_a_href: list[str] = []
    index_page_url: str = ''
    # 广告的地址栏高度
    browser_ads_bar: int = 0
    # 广告界面中的cookie
    ads_cookie_selectors: list = []
    # 任务提前终止
    manual_finished: bool = False
    # 设置文档加载状态
    default_ready_state = ['interactive', 'complete']
    # 排除的jsHandle
    non_clickable_handles: list[ElementHandle] = []
    # 当前广告的域名
    ads_domain = ''
    # 当前用户步调 1 - 9 慢 -> 快
    visit_pace = 1
    ads_start_time = 0

    def __init__(self, require_params: dict) -> None:
        self.clickable_elements = []
        self.sid = require_params['sid']
        self.enable_log = require_params['enable_log']
        self.index_page_host = require_params['index_page_host']
        self.child_page_host = require_params['child_page_host']
        self.sync_print_not_log("广告工具 - 初始化完成")

    # 加载本次广告任务数据
    async def load(self, require_params: dict) -> None:
        await self.variable_blank()
        self.browser = require_params['browser']
        self.context = require_params['context']
        self.page = require_params['page']
        self.logger = require_params['logger']
        self.baseSetNew = require_params['baseSetNew']
        self.screen_width = require_params['screen_width'] \
            if 'screen_width' in require_params else self.screen_width
        await self.my_print(f"广告工具 - 屏宽: {self.screen_width}")
        self.screen_height = require_params['screen_height'] \
            if 'screen_height' in require_params else self.screen_height
        await self.my_print(f"广告工具 - 屏高: {self.screen_height}")
        self.clickable_selectors = require_params['clickable_selectors'] \
            if ('clickable_selectors' in require_params.keys()) else c_click
        await self.my_print(f"广告工具 - 点击的selectors: {json.dumps(self.clickable_selectors)}")
        self.non_clickable_selectors = require_params['non_clickable_selectors'] \
            if ('non_clickable_selectors' in require_params.keys()) else (c_cookie + c_video)
        await self.my_print(f"广告工具 - 不点击的selectors: {json.dumps(self.non_clickable_selectors)}")
        self.show_selectors = require_params['show_selectors'] \
            if ('show_selectors' in require_params.keys()) else c_menu
        await self.my_print(f"广告工具 - 点击展示的selectors: {json.dumps(self.show_selectors)}")
        self.back_selectors = require_params['back_selectors'] \
            if ('back_selectors' in require_params.keys()) else c_back
        await self.my_print(f"广告工具 - 进入页面后退出的selectors: {json.dumps(self.back_selectors)}")
        self.video_selectors = require_params['video_selectors'] \
            if ('video_selectors' in require_params.keys()) else c_video
        await self.my_print(f"广告工具 - 进入页面后退出的selectors: {json.dumps(self.back_selectors)}")
        # self.ads_durations = require_params['ads_durations']
        # await self.my_print(f"广告工具 - 浏览时长: {json.dumps(self.ads_durations)}")
        # self.ads_visit_count = require_params['ads_visit_count']
        # await self.my_print(f"广告工具 - 浏览页面: {self.ads_visit_count}")
        self.ads_max_visits = require_params['ads_max_visits']
        await self.my_print(f"广告工具 - 最大浏览时间: {self.ads_max_visits}")
        self.visit_pace = require_params['visit_pace'] \
            if ('visit_pace' in require_params.keys()) else random.randint(6, 10)
        # self.visit_pace = 10
        await self.my_print(f"广告工具 - 模拟用户浏览速度: {self.visit_pace}")
        self.ads_cookie_selectors = require_params['ads_cookie_selectors'] \
            if ("ads_cookie_selectors" in require_params.keys()) else c_cookie
        await self.my_print(f"广告工具 - 点击cookie的selectors: {json.dumps(self.ads_cookie_selectors)}")
        self.current_visit_seconds = 0
        self.current_visit_count = 0
        self.browse_page_url = []
        self.index_page_url = ''

        await self.reload_page()
        self.index_page_url = copy.deepcopy(self.page.url)
        self.browse_page_url.append(self.index_page_url)
        self.ads_domain = urlparse(self.page.url).netloc
        self.sync_print_not_log("广告工具 - 当前广告数据加载完成")

    # 人工终止
    async def stop(self):
        self.manual_finished = True

    async def result(self):
        return {
            "log_state": self.enable_log, "clickable_selectors": self.clickable_selectors,
            "non_clickable_selectors": self.non_clickable_selectors, "sid": self.sid,
            "screen_width": self.screen_width, "screen_height": self.screen_height,
            "index_page_host": self.index_page_host, "child_page_host": self.child_page_host,
            # "ads_durations": self.ads_durations, "ads_visit_count": self.ads_visit_count,
            "ads_max_visits": self.ads_max_visits, "current_visit_seconds": self.current_visit_seconds,
            "current_visit_count": self.current_visit_count, "js_handles_md5": self.js_handles_md5,
            "browse_page_url": self.browse_page_url, "index_page_url": self.index_page_url,
            "ads_cookie_selectors": self.ads_cookie_selectors, "manual_finished": self.manual_finished
        }

    async def variable_blank(self):
        self.clickable_elements = []
        self.browser = None
        self.context = None
        self.page = None
        self.logger = None
        self.baseSet = None
        self.screen_width = 0
        self.screen_height = 0
        self.clickable_selectors = []
        self.non_clickable_selectors = []
        self.show_selectors = []
        self.back_selectors = []
        self.video_selectors = []
        # self.ads_durations = []
        # self.ads_visit_count = 0
        self.ads_max_visits = 0
        self.ads_cookie_selectors = []
        self.current_visit_seconds = 0
        self.current_visit_count = 0
        self.browse_page_url = []
        self.index_page_url = ''
        self.ads_domain = ''

    # 日志打印格式化
    async def my_print(self, *args):
        nowTime = date('Y-m-d H:i:s')
        print(nowTime, self.sid, *args)
        if self.enable_log:
            msg = join_args(*args)
            await self.logger.log_info(f"{self.sid} - {msg}")

    # 不打印日志
    def sync_print_not_log(self, *args):
        nowTime = date('Y-m-d H:i:s')
        print(nowTime, self.sid, *args)

    # 同步方法打印
    def sync_print(self, *args):
        nowTime = date('Y-m-d H:i:s')
        print(nowTime, self.sid, *args)
        if self.enable_log:
            msg = join_args(*args)
            self.logger.log_info_sync(f"{self.sid} - {msg}")

    # 获取指定的selectors节点列表  已废弃
    async def get_specify_elements(self, selectors=None):
        temp_elements: list[ElementHandle] = []
        if selectors is None:
            selectors = self.clickable_selectors
        await self.my_print(f"广告工具 - 指定selectors: {selectors}")
        if len(selectors) == 0:
            raise Exception('广告工具 - Ads does not specify a selector tag.')
        for selector in selectors:
            elements = await self.page.query_selector_all(selector)
            for element in elements:
                if element is not None:
                    rect = await self.page.evaluate("ele => ele.getBoundingClientRect()", element)
                    width = int(rect["width"])
                    height = int(rect["height"])
                    if (width > 0) and (height > 0):
                        temp_elements.append(element)
        await self.my_print(f"广告工具 - 获取指定 {selectors} 的可点击元素长度: {len(temp_elements)}")
        return temp_elements

    # 获取可点击的js element列表
    async def get_click_elements(self):
        ce_len = 0
        nce_len = 0
        self.clickable_elements = []
        if len(self.clickable_selectors) > 0 and len(self.non_clickable_selectors) == 0:
            clickable_elements = await self.page.query_selector_all(','.join(self.clickable_selectors))
            ce_len = copy.deepcopy(len(clickable_elements))
            for element in clickable_elements:
                temp_rect = await self.page.evaluate("ele => ele.getBoundingClientRect()", element)
                if int(temp_rect['width']) > 0 and int(temp_rect['height']) > 0:
                    self.clickable_elements.append(element)
        elif len(self.non_clickable_selectors) > 0 and len(self.clickable_selectors) > 0:
            clickable_elements = await self.page.query_selector_all(','.join(self.clickable_selectors))
            ce_len = copy.deepcopy(len(clickable_elements))
            non_clickable_elements = await self.page.query_selector_all(','.join(self.non_clickable_selectors))
            nce_len = copy.deepcopy(len(non_clickable_elements))
            for element in clickable_elements:
                temp_rect = await self.page.evaluate("ele => ele.getBoundingClientRect()", element)
                if int(temp_rect['width']) > 0 and int(temp_rect['height']) > 0:

                    element_inner_html = ((await element.inner_html()).replace(" ", "")
                                          .replace("\n", "").replace("\t", ""))
                    element_md5 = hashlib.md5(element_inner_html.encode()).hexdigest()
                    flag = True
                    for non_element in non_clickable_elements:
                        non_element_inner_html = ((await non_element.inner_html()).replace(" ", "")
                                                  .replace("\n", "").replace("\t", ""))
                        non_element_md5 = hashlib.md5(non_element_inner_html.encode()).hexdigest()
                        if element_md5 == non_element_md5:
                            flag = False
                    if flag:
                        self.clickable_elements.append(element)

        if len(self.clickable_elements) > 0:
            for handle in self.non_clickable_handles:
                while handle in self.clickable_elements:
                    self.clickable_elements.remove(handle)

        if len(self.clickable_elements) > 0:
            for ce in self.clickable_elements:
                temp_href = await self.page.evaluate("""
                    (ce) => ce.href;
                """, ce)
                await self.my_print(f"可点击element移除href筛选: {temp_href}")
                if temp_href in self.browse_a_href:
                    self.clickable_elements.remove(ce)
                    await self.my_print(f"成功从element移除href: {temp_href}")

        await self.my_print(
            f"广告工具 - 当前页: {self.page.url}, 可点击的element数: {len(self.clickable_elements)}, 其中点击标签数: {ce_len}, "
            f"不点击标签数: {nce_len}")

    # 检查某个selector下元素列表是否包含当前元素, 包含返回 True
    async def check_element_contains(self, specify_selector: str, element: ElementHandle):
        specify_elements = await self.page.query_selector_all(specify_selector)
        for specify_element in specify_elements:
            specify_element_inner_html = ((await specify_element.inner_html()).replace(" ", "")
                                          .replace("\n", "").replace("\t", ""))
            element_inner_html = ((await element.inner_html()).replace(" ", "")
                                  .replace("\n", "").replace("\t", ""))

            if specify_selector == self.video_selectors[0]:
                await self.my_print(
                    f"specify_element_inner_html: {specify_element_inner_html},  element_inner_html: {element_inner_html}")
                await self.page.wait_for_timeout(60000)

            if (hashlib.md5(specify_element_inner_html.encode()).hexdigest() ==
                    hashlib.md5(element_inner_html.encode()).hexdigest()):
                return True
        return False

    # 随机获取一个有值的selector，每次都重新获取可点击的标签
    async def rand_element(self, specify_selector=None, match=True):
        current_element = None
        await self.get_click_elements()
        if len(self.clickable_elements) == 0:
            return current_element, match
        while len(self.clickable_elements) > 0:
            random.shuffle(self.clickable_elements)
            temp_element = self.clickable_elements.pop()
            ce_len = len(self.clickable_elements)
            box = await temp_element.bounding_box()
            if box is None:
                continue
            rect = await self.page.evaluate("ele => ele.getBoundingClientRect()", temp_element)
            width = int(rect["width"])
            height = int(rect["height"])
            if width <= 0 or height <= 0:
                await self.my_print(f"广告工具 - 随机到的子页面element为: {temp_element}, 边界值为: {rect}")
                continue
            # 同一页面不再点击
            si_html = ((await temp_element.inner_html()).replace(" ", "")
                       .replace("\n", "").replace("\t", ""))
            if hashlib.md5(si_html.encode()).hexdigest() in self.js_handles_md5:
                continue
            if specify_selector is None:
                current_element = temp_element
            else:
                flag = await self.check_element_contains(specify_selector, temp_element)
                if flag:
                    current_element = temp_element
                else:
                    if ce_len <= 0:
                        await self.my_print(f"当前页面元素中无法获取到指定selector的元素: {specify_selector}")
                        return await self.rand_element(None, False)
                    continue
            break
        return current_element, match

    # 当前页面存在点击标签时，再当前页面点击，否则返回上一个页面。返回的float只做日志打印，原因是已加入记录中
    async def current_page_click(self):
        # 获取最新页面对象
        last_page_len = await self.reload_page()
        last_page_url = copy.deepcopy(self.page.url)
        (clickable_ele, flag) = await self.rand_element()
        await self.my_print(f"current_page_click 1 {clickable_ele} {flag}")
        # 当前页面没有点击标签时
        if clickable_ele is None:
            # 若是在广告首页，则首页浏览
            if self.page.url == self.index_page_url:
                return await self.page_visit()
            else:
                await self.page_back()
                return await self.current_page_click()
        else:
            # 当前页面有点击事件
            curr_page_len = await self.reload_page()
            await self.wait_ready_state()
            rect = await self.page.evaluate("ele => ele.getBoundingClientRect()", clickable_ele)
            if int(rect["width"]) > 0 and int(rect["height"]) > 0:
                ss_ret = await self.specify_element(clickable_ele)
                if isinstance(ss_ret, float):
                    curr_page_url = copy.deepcopy(self.page.url)
                    # 当打开新标签页时，同时 specify_element 并没有执行后退操作时，关闭当前标签页，使用主标签页
                    if last_page_len < curr_page_len and last_page_url != curr_page_url:
                        await self.page_back()
                    return ss_ret

    # 页面浏览
    async def page_visit(self, stay=False):
        await self.wait_ready_state()
        await self.cookie_find_click2()
        load_start_time = time.time()
        predict_step, predict_time, current_swipe_direction = await self.predict_count_duration_coordinate()
        await self.my_print(f"预测滑动步骤: {predict_step}")
        await self.my_print(f"预测等待时间: {predict_time}")
        if len(predict_step) == 0:
            await self.page.wait_for_timeout(random.randint(7000, 14000))
            await self.my_print("已知无滑动步骤, 原地等待7-14s")
        else:
            swipe_count = 1
            for ps in predict_step:
                swipe_step = [int(ps_item) for ps_item in ps.split(",")]
                temp_cd = await self.current_direction()
                if isinstance(temp_cd, str):
                    if current_swipe_direction != temp_cd:
                        current_swipe_direction = temp_cd

                if current_swipe_direction == "down":
                    if swipe_step[1] > swipe_step[3]:
                        swipe_step[1], swipe_step[3] = swipe_step[3], swipe_step[1]
                    await self.my_print(f"滑动次数: {swipe_count}, 本次滑动为下滑: {swipe_step}")
                    swipe_count += 1
                elif current_swipe_direction == "up":
                    if swipe_step[1] < swipe_step[3]:
                        swipe_step[1], swipe_step[3] = swipe_step[3], swipe_step[1]
                    await self.my_print(f"滑动次数: {swipe_count}, 本次滑动为上滑: {swipe_step}")
                    swipe_count += 1

                await self.baseSetNew.page_step_swipe(*swipe_step)
                if swipe_count % 3 == 0:
                    if (time.time() - self.ads_start_time) > self.ads_max_visits:
                        await self.my_print(f"滑动次数: {swipe_count}, 浏览时间超时，结束任务")
                        await self.stop()
                        break
        load_suc_time = time.time() - load_start_time
        self.current_visit_count += 1
        self.current_visit_seconds += load_suc_time
        return load_suc_time

    # 当前滑动方向 step速度无法预测，随时参数反转
    async def current_direction(self):
        # js获取页面高度
        body_height = await self.page.evaluate("""
                            () => document.body.scrollHeight || document.body.clientHeight;
                        """)
        body_height = float(body_height)
        # js获取可视高度
        # screen_height = await self.page.evaluate("""
        #                     () => window.innerHeight || document.documentElement.clientHeight;
        #                 """)
        # screen_height = float(screen_height)
        visit_height = await self.page.evaluate("""
                   () => window.visualViewport.height;
               """)
        # js获取滚动高度
        scroll_height = await self.page.evaluate("""
                        () => document.documentElement.scrollTop || document.body.scrollTop;
                    """)
        scroll_height = float(scroll_height)
        # await self.my_print(f"current_direction: {body_height} {scroll_height} {self.screen_height} {visit_height}")
        if body_height < scroll_height + self.screen_height + self.screen_height / 8:
            return 'down'
        elif scroll_height < self.screen_height / 8:
            return 'up'
        else:
            return True

    # 预测浏览的持续时长和滑动次数和坐标始末
    async def predict_count_duration_coordinate(self):
        (body_height, visit_height, scroll_height, bookmark_height, predict_slide_height,
         predict_visit_time, swipe_direction, slide_step, slide_count) = \
            await self.get_page_browsing_data()

        # 调整滑动次数
        if slide_count > 8:
            slide_count = 8

        # #该版本不做单页面的最大浏览时长处理
        predict_result = []
        # 第一次移动方向
        temp_swipe_direction = swipe_direction
        current_slide_count = 0
        while current_slide_count <= slide_count:
            # if scroll_height + self.screen_height >= body_height - 10:
            #     break
            scrollTop = await self.page.evaluate("document.documentElement.scrollTop || document.body.scrollTop")
            scrollHeight = await self.page.evaluate("document.body.scrollHeight")

            current_slide_count += 1
            this_slide_height = random.randint(*predict_slide_height)
            await self.my_print(f"本次滑动高度[this_slide_height]为: {this_slide_height} - {predict_slide_height}")
            # 上滑
            if swipe_direction == 'up':
                # 上滑到接近底部时处理
                # if body_height - scroll_height - self.screen_height < this_slide_height:
                if scrollTop >= scrollHeight - visit_height * 1.33:
                    # temp_height = int(body_height - scroll_height - self.screen_height)
                    # if temp_height < 0:
                    #     current_slide_count -= 1
                    #     swipe_direction = 'down'
                    #     continue
                    # tsh = random.randint(temp_height - 10, temp_height)
                    tsh = this_slide_height
                    start_y = random.randint(tsh, self.screen_height)
                    start_x = random.randint(int(self.screen_width / 4), int(self.screen_width / 4 * 3))
                    # end_x = random.randint(start_x - 15, start_x + 15)
                    if random.randint(1, 100) < 50:
                        end_x = start_x - random.randint(10, 30)
                    else:
                        end_x = start_x + random.randint(10, 30)
                    end_y = start_y - tsh
                    step = random.randint(*slide_step)
                    visit_time = math.ceil(random.randint(*predict_visit_time) / this_slide_height * tsh)
                    predict_result.append(f"{start_x},{start_y},{end_x},{end_y},{step},{visit_time}")
                    scroll_height += tsh
                    swipe_direction = 'down'
                else:
                    start_y = random.randint(this_slide_height, self.screen_height)
                    start_x = random.randint(int(self.screen_width / 4), int(self.screen_width / 4 * 3))
                    # end_x = random.randint(start_x - 15, start_x + 15)
                    if random.randint(1, 100) < 50:
                        end_x = start_x - random.randint(10, 30)
                    else:
                        end_x = start_x + random.randint(10, 30)
                    end_y = start_y - this_slide_height
                    step = random.randint(*slide_step)
                    visit_time = math.ceil(random.randint(*predict_visit_time))
                    predict_result.append(f"{start_x},{start_y},{end_x},{end_y},{step},{visit_time}")
                    scroll_height += this_slide_height
            else:  # 下滑
                # 下滑到接近顶部时处理
                # if scroll_height < this_slide_height:
                if scrollTop <= visit_height * 0.33:
                    # if scroll_height - 10 < 0:
                    #     if scroll_height < 0:
                    #         current_slide_count -= 1
                    #         swipe_direction = 'up'
                    #         continue
                    #     tsh = scroll_height
                    # else:
                    #     tsh = random.randint(int(scroll_height - 10), int(scroll_height))
                    tsh = this_slide_height
                    start_y = random.randint(bookmark_height, self.screen_height - int(scroll_height))
                    start_x = random.randint(int(self.screen_width / 4), int(self.screen_width / 4 * 3))
                    # end_x = random.randint(start_x - 15, start_x + 15)
                    if random.randint(1, 100) < 50:
                        end_x = start_x - random.randint(10, 30)
                    else:
                        end_x = start_x + random.randint(10, 30)
                    end_y = start_y + tsh
                    step = random.randint(*slide_step)
                    visit_time = math.ceil(random.randint(*predict_visit_time) / this_slide_height * tsh)
                    predict_result.append(f"{start_x},{start_y},{end_x},{end_y},{step},{visit_time}")
                    scroll_height -= tsh
                    swipe_direction = 'up'
                else:
                    start_y = random.randint(bookmark_height, self.screen_height - this_slide_height)
                    start_x = random.randint(int(self.screen_width / 4), int(self.screen_width / 4 * 3))
                    # end_x = random.randint(start_x - 15, start_x + 15)
                    if random.randint(1, 100) < 50:
                        end_x = start_x - random.randint(10, 30)
                    else:
                        end_x = start_x + random.randint(10, 30)
                    end_y = start_y + this_slide_height
                    step = random.randint(*slide_step)
                    visit_time = math.ceil(random.randint(*predict_visit_time))
                    predict_result.append(f"{start_x},{start_y},{end_x},{end_y},{step},{visit_time}")
                    scroll_height -= this_slide_height

        return predict_result, predict_visit_time, temp_swipe_direction

    # 预测本次浏览滑动的各项参数
    async def predict_visit_coordinate(self, coordinate: Union[tuple[int, int, int, int], str]):
        (body_height, visit_height, scroll_height, bookmark_height, predict_slide_height,
         predict_visit_time, swipe_direction, slide_step, slide_count) = \
            await self.get_page_browsing_data()

        # slide_float = 40
        if isinstance(coordinate, str):
            this_slide_height = random.randint(*predict_slide_height)
            if coordinate == 'down':
                if self.screen_height - this_slide_height < bookmark_height:
                    start_y = bookmark_height
                else:
                    start_y = random.randint(bookmark_height, self.screen_height - this_slide_height)
                start_x = random.randint(int(self.screen_width / 4), int(self.screen_width / 4 * 3))
                # end_x = random.randint(start_x - 15, start_x + 15)
                if random.randint(1, 100) < 50:
                    end_x = start_x - random.randint(10, 30)
                else:
                    end_x = start_x + random.randint(10, 30)
                end_y = start_y + this_slide_height
                step = random.randint(*slide_step)
                visit_time = math.ceil(random.randint(*predict_visit_time))
            elif coordinate == 'up':
                start_y = random.randint(this_slide_height, self.screen_height)
                start_x = random.randint(int(self.screen_width / 4), int(self.screen_width / 4 * 3))
                # end_x = random.randint(start_x - 15, start_x + 15)
                if random.randint(1, 100) < 50:
                    end_x = start_x - random.randint(10, 30)
                else:
                    end_x = start_x + random.randint(10, 30)
                end_y = start_y - this_slide_height
                step = random.randint(*slide_step)
                visit_time = math.ceil(random.randint(*predict_visit_time))
            else:
                raise Exception("未知错误")

        else:
            start_x, start_y, end_x, end_y = coordinate
            this_slide_height = random.randint(*predict_slide_height)
            tsh = start_y - end_y
            if tsh == 0:
                tsh = start_x - end_x
            if tsh < 0:
                tsh = -tsh
            step = random.randint(*slide_step)
            visit_time = math.ceil(random.randint(*predict_visit_time) / this_slide_height * tsh)
        return f"{start_x},{start_y},{end_x},{end_y},{step},{visit_time}"

    # 获取本页面浏览数据
    async def get_page_browsing_data(self):
        await self.wait_ready_state()
        # js获取页面高度
        body_height = await self.page.evaluate("""
                    () => document.body.scrollHeight || document.body.clientHeight;
                """)
        visualViewport_height = await self.page.evaluate("window.visualViewport.height")
        await self.my_print(f"js获取页面高度: {body_height}")
        await self.my_print(f"js获取页面可用高度: {visualViewport_height}")
        # if body_height <= visualViewport_height:
        #     body_height = float(body_height)
        # else:
        #     if body_height >= 5000:
        #         body_height = 5000
        #     elif body_height >= 4000:
        #         body_height = 3500
        #     elif body_height >= 3000:
        #         body_height = 2500
        #     elif body_height >= 2000:
        #         body_height = 1500
        #     elif body_height >= 1000:
        #         body_height = 1000
        #     else:
        #         body_height = float(body_height)
        await self.my_print(f"计算页面高度: {body_height}")
        # js获取可视高度
        visit_height = await self.page.evaluate("""
            () => window.visualViewport.height;
        """)
        visit_height = float(visit_height)
        # 浏览器页签区、地址栏区、菜单栏区、调试窗口区外的区域
        bookmark_height = int(self.screen_height / 4)
        if self.screen_height > visit_height:
            bookmark_height = int(self.screen_height - visit_height + 10)
        await self.my_print(f"js获取可视高度: {visit_height}")
        # js获取滚动高度
        scroll_height = await self.page.evaluate("""
                    () => document.documentElement.scrollTop || document.body.scrollTop;
                """)
        scroll_height = float(scroll_height)
        await self.my_print(f"js获取滚动高度: {scroll_height}")
        # 开始方向 向上 上滑
        if scroll_height <= 0:
            swipe_direction = "up"
        else:
            temp_rand = random.randint(1, 100)
            if temp_rand <= 50:
                swipe_direction = "down"
            else:
                swipe_direction = "up"
        origin_direction = copy.deepcopy(swipe_direction)
        # 滑动次数
        def_swipe_count = 5
        if float(visit_height) > 0:
            def_swipe_count = math.ceil(body_height / visit_height)
        await self.my_print(f"预测滑动次数为: {def_swipe_count}")
        # 当前文章中所有文字
        html_text = await self.page.evaluate("""
                    () => document.documentElement.innerText;
                """)
        ht_len = len(html_text)
        await self.my_print(f"已知当前页文本字数为: {ht_len}")
        # 时间单位为毫秒
        predict_visit_time = [3000, 5000]
        # 持续时长 表示 滑动浮动为10的时间
        if html_text is not None:
            visit_time = math.ceil(ht_len / def_swipe_count / 10 / self.visit_pace)
            min_visit_time = visit_time - 5
            max_visit_time = visit_time + 5
            if min_visit_time < 3:
                min_visit_time = 3
            predict_visit_time = [min_visit_time * 1000, max_visit_time * 1000]
        # 坐标始末 定义 1000px滑动需1s
        # 滑动浮动
        # slide_float = random.randint(15, 35)
        slide_float = random.randint(1, 10)
        slide_step = [math.ceil(0.2 * slide_float + 13), math.ceil(0.25 * slide_float + 17)]
        # await self.my_print(f"预测滑动速度: {slide_float}")
        slide_height = int((self.screen_height - bookmark_height) / 10 * slide_float)
        predict_slide_height = [slide_height, slide_height + 20]
        # 重置浏览滑动时间
        predict_visit_time: list[int] = [math.ceil(vt / 10 * slide_float) for vt in predict_visit_time]

        await self.my_print(f"get_page_browsing_data获取结果 body_height:{body_height},visit_height:{visit_height},"
                            f"scroll_height:{scroll_height},bookmark_height:{bookmark_height},"
                            f"predict_slide_height:{predict_slide_height},predict_visit_time:{predict_visit_time},"
                            f"swipe_direction:{swipe_direction},slide_step:{slide_step},"
                            f"def_swipe_count:{def_swipe_count}")
        return (int(body_height), int(visit_height), int(scroll_height), bookmark_height, predict_slide_height,
                predict_visit_time, swipe_direction, slide_step, def_swipe_count)

    # 没有标签的随机滑动
    # async def no_selector(self, duration: Optional[float] = None, stay=False):
    #     if duration is not None and duration > 0:
    #         start_time = time.time()
    #         while time.time() - start_time < duration:
    #             if not stay:
    #                 await self.rand_swipe()
    #             else:
    #                 await asyncio.sleep(1)
    #     else:
    #         await self.rand_swipe()
    #     return True

    # async def rand_swipe(self):
    #     await self.baseSetNew.page_randomSwipe()
    #     await asyncio.sleep(random.randint(2000, 3000) / 1000)

    # 点击
    async def page_click(self, x, y):
        await self.wait_ready_state()
        await self.baseSetNew.page_click(x, y)
        # await self.page.wait_for_timeout(10000)
        await self.reload_page()
        await self.my_print(f"广告工具 - 当前页面的地址为: {self.page.url}")

    # 后退
    async def page_back(self, target_url=None):
        await self.my_print(f"广告工具 - 准备返回- 当前页面的地址为: {self.page.url}")
        await self.my_print(f"广告工具 - 准备返回- 首页地址为: {self.index_page_url}")
        if self.page.url == self.index_page_url:
            return False
        else:
            await self.baseSetNew.page_back()
            return True
        # current_url = copy.deepcopy(self.page.url)
        # while True:
        #     if target_url is None:
        #         if self.page.url != current_url:
        #             break
        #     else:
        #         if self.page.url == target_url:
        #             break
        #
        #     await self.baseSetNew.page_back()
        #     await asyncio.sleep(random.randint(3000, 5000) / 1000)
        #     await self.wait_ready_state()
        #
        #     if target_url is None:
        #         if self.page.url != current_url:
        #             break
        #     else:
        #         if self.page.url == target_url:
        #             break
        # await self.reload_page()


    # 等待页面加载完成
    async def wait_ready_state(self):
        await self.reload_page()
        start_time = time.time()
        try:
            readyState = await self.page.evaluate("document.readyState")
            # 页面等待时间超过10s则重载当前页面
            while readyState not in self.default_ready_state and time.time() - start_time <= 10:
                await asyncio.sleep(1)
                await self.my_print(f"广告工具 - 当前页面: {self.page.url}, 页面状态: {readyState}")
            if readyState in self.default_ready_state:
                return True
            await self.page.reload()
            await self.my_print(f"广告工具 - 当前页面刷新重新获取")
            return await self.reload_page()
        except Exception as e:
            await self.my_print(f"广告工具 - 等待当前页面加载完成异常, 重载加载page对象")
            return await self.reload_page()

    # 页面滑动 将指定对象滑动到可视页面中
    async def swipe_position(self, selectorNode: ElementHandle, swipe_notes: list[dict], cur_count=1, max_count=3):
        # await self.page.wait_for_timeout(random.randint(2000, 4000))
        bounding_rect = await self.page.evaluate("""
            ele => ele.getBoundingClientRect()
        """, selectorNode)
        await self.my_print(f'广告工具 - 获取到element对象的边界属性: {bounding_rect}')
        if len(swipe_notes) != 0:
            last_swipe_notes = {}
            for sn in swipe_notes:
                if last_swipe_notes == sn:
                    # 若当前位置不在屏幕范围内
                    bounding_rect = await self.page.evaluate("""
                                ele => ele.getBoundingClientRect()
                            """, selectorNode)
                    if ((bounding_rect["top"] > self.screen_height or bounding_rect["bottom"] < 0 or
                         bounding_rect["left"] > self.screen_width or bounding_rect["right"] < 0)):
                        # if self.page.url != self.index_page_url:
                        #     await self.my_print(f"广告工具 - 目标点击标签不在屏幕范围内, 边界值: {bounding_rect}")
                        #     return False
                        # else:
                        #     return True
                        if cur_count > max_count:
                            await self.my_print(f"广告工具 - 目标点击标签不在屏幕范围内, 边界值: {bounding_rect}")
                            return False
                        # 本次滑动丢失，重新滑动
                        await self.my_print(f"广告工具 - 本次滑动丢失, 重新滑动, 边界值: {bounding_rect}")
                        del swipe_notes[len(swipe_notes) - 1]
                        cur_count += 1
                        return await self.swipe_position(selectorNode, swipe_notes, cur_count, max_count)
                    else:
                        await self.my_print(
                            f'广告工具 - 无法滑动, 边界值: {last_swipe_notes}')
                        return bounding_rect
                last_swipe_notes = sn

        await asyncio.sleep(random.randint(2000, 3000) / 1000)
        tag_width, tag_height, tag_top, tag_right, tag_bottom, tag_left = await get_bounding(bounding_rect)
        target_rect: dict = {}
        if tag_top > self.browser_ads_bar and tag_top >= 0 and tag_bottom <= self.screen_height:
            await self.my_print(f'广告工具 - 目标在完整屏幕范围内, 目标边界值: {bounding_rect}')
            # 尽量靠近屏幕高 1/4 - 3/4 中间位置
            dep = await self.slight_sliding(round(self.screen_height / 4, 2), round(self.screen_height / 4 * 3, 2),
                                            tag_top, tag_bottom)
            if isinstance(dep, bool) and dep:
                target_rect = bounding_rect
            elif isinstance(dep, dict):
                await self.baseSetNew.page_swipe(dep['start_x'], dep['start_y'], dep['end_x'], dep['end_y'])
            elif isinstance(dep, str):
                swipe_step = [int(item) for item in dep.split(",")]
                await self.baseSetNew.page_step_swipe(*swipe_step)

        elif tag_top < 0 and tag_bottom / tag_height >= 0.5:
            await self.my_print('广告工具 - 目标位于屏幕上方，目标可视>50%')
            dep = await self.slight_sliding(round(self.screen_height / 4, 2), round(self.screen_height / 4 * 3, 2),
                                            tag_top, tag_bottom)
            if isinstance(dep, bool) and dep:
                target_rect = bounding_rect
            elif isinstance(dep, dict):
                await self.baseSetNew.page_swipe(dep['start_x'], dep['start_y'], dep['end_x'], dep['end_y'])
            elif isinstance(dep, str):
                swipe_step = [int(item) for item in dep.split(",")]
                await self.baseSetNew.page_step_swipe(*swipe_step)

        elif tag_bottom > self.screen_height and (
                tag_height - (tag_bottom - self.screen_height)) / tag_height >= 0.5:
            await self.my_print('广告工具 - 目标位于屏幕下方，目标可视>50%')
            dep = await self.slight_sliding(round(self.screen_height / 4, 2), round(self.screen_height / 4 * 3, 2),
                                            tag_top, tag_bottom)
            if isinstance(dep, bool) and dep:
                target_rect = bounding_rect
            elif isinstance(dep, dict):
                await self.baseSetNew.page_swipe(dep['start_x'], dep['start_y'], dep['end_x'], dep['end_y'])
            elif isinstance(dep, str):
                swipe_step = [int(item) for item in dep.split(",")]
                await self.baseSetNew.page_step_swipe(*swipe_step)

        elif tag_top < 0 and tag_bottom / tag_height < 0.5:
            await self.my_print('广告工具 - 目标位于屏幕上方且目标不可视，需下滑')
            # await self.baseSetNew.page_swipeDown()
            temp_pvc = await self.predict_visit_coordinate("down")
            await self.my_print(f"广告工具 - 获取下滑结果: {temp_pvc}")
            swipe_step = [int(item) for item in temp_pvc.split(",")]
            await self.baseSetNew.page_step_swipe(*swipe_step)

        elif tag_bottom > self.screen_height and (
                tag_height - (tag_bottom - self.screen_height)) / tag_height < 0.5:
            await self.my_print('广告工具 - 目标位于屏幕下方且目标不可视，需上滑')
            # await self.baseSetNew.page_swipeUp()
            temp_pvc = await self.predict_visit_coordinate("up")
            await self.my_print(f"广告工具 - 获取上滑结果: {temp_pvc}")
            swipe_step = [int(item) for item in temp_pvc.split(",")]
            await self.baseSetNew.page_step_swipe(*swipe_step)

        else:
            await self.my_print(f'广告工具 - 目标位于屏幕位置未知，获取到数据为->边界矩形:{json.dumps(bounding_rect)}, '
                                f'屏幕大小:width:{self.screen_width}, height:{self.screen_height}, '
                                f'通过scrollTo直接滑动指定位置')
            # 通过js直接滑动并返回
            await self.page.evaluate("ele => ele.scrollIntoView({block:'start'})", selectorNode)
            await self.page.wait_for_timeout(2000)
            return await self.page.evaluate("""
                    ele => ele.getBoundingClientRect()
                    """, selectorNode)

        if len(target_rect.keys()) > 0:
            return target_rect
        else:
            swipe_notes.append(bounding_rect)
            await asyncio.sleep(random.randint(2000, 3000) / 1000)
            await self.my_print(f'广告工具 - 第 {len(swipe_notes)} 次滑动完成')
            return await self.swipe_position(selectorNode, swipe_notes)

    # 轻微滑动
    async def slight_sliding(self, start: float, end: float, top: float, bottom: float):
        # if bottom <= end and top >= start:
        if bottom < end or top > start:
            await self.my_print('广告工具 - 目标位于规定范围内, 可以点击')
            return True
        elif bottom > end:
            await self.my_print('广告工具 - 目标位于屏幕下方, 轻微上滑')
            start_x = random.randint(30, self.screen_width - 30)
            # end_x = start_x + random.randint(-15, 15)
            if random.randint(1, 100) < 50:
                end_x = start_x - random.randint(10, 30)
            else:
                end_x = start_x + random.randint(10, 30)
            start_y = random.randint(round(self.screen_height / 2) + 15, round(self.screen_height, 2) - 15)
            end_y = start_y - round(self.screen_height / 4, 2)
            # return {'start_x': start_x, 'start_y': start_y, 'end_x': end_x, 'end_y': end_y, }
            return await self.predict_visit_coordinate((start_x, start_y, end_x, end_y))
        else:
            await self.my_print('广告工具 - 目标位于屏幕上方, 轻微下滑')
            start_x = random.randint(30, self.screen_width - 30)
            # end_x = start_x + random.randint(-15, 15)
            if random.randint(1, 100) < 50:
                end_x = start_x - random.randint(10, 30)
            else:
                end_x = start_x + random.randint(10, 30)
            start_y = random.randint(round(self.screen_height / 2), round(self.screen_height / 2 + 30))
            end_y = start_y + round(self.screen_height / 4, 2)
            # return {'start_x': start_x, 'start_y': start_y, 'end_x': end_x, 'end_y': end_y, }
            return await self.predict_visit_coordinate((start_x, start_y, end_x, end_y))

    # 若left为负数或者超出屏幕宽度，则可能为横行平滑图片。平滑到指定图片
    async def smooth_pic(self, sp_selector, pic_direction='right', current_smooth_count=1, max_smooth_count=6):
        if current_smooth_count > max_smooth_count:
            await self.page_back()
            return False
        box: dict = await self.page.evaluate("ele => ele.getBoundingClientRect()", sp_selector)
        left: float = box['left']
        top: float = box['top']
        if 0 < left < self.screen_width:
            await self.my_print(f"广告工具 - 随机到的按钮已在当前图片中, 当前定位: {box}")
            return box
        await self.my_print(f"广告工具 - 随机到的按钮为滑动式图片内的a标签, 当前定位: {box}, 校正中...")
        rect = await self.page.evaluate("ele => ele.getBoundingClientRect()", sp_selector)
        height = rect["height"]
        y = int(top + height * 0.50)
        if y > self.screen_height:
            y = random.randint(int(top + 1), int(self.screen_height - 1))
        x1 = int(self.screen_width * 0.75)
        x2 = int(self.screen_width * 0.25)
        if pic_direction == 'left':
            temp_pvc = await self.predict_visit_coordinate((x2, y, x1, y))
            temp_c = [int(item) for item in temp_pvc.split(',')]
            await self.baseSetNew.page_step_swipe(temp_c[0], temp_c[1], temp_c[2], temp_c[3], temp_c[4])
            await self.my_print(f"广告工具 - {x2} -> {x1} 图片左滑中...")
        else:
            temp_pvc = await self.predict_visit_coordinate((x1, y, x2, y))
            temp_c = [int(item) for item in temp_pvc.split(',')]
            await self.baseSetNew.page_step_swipe(temp_c[0], temp_c[1], temp_c[2], temp_c[3], temp_c[4])
            await self.my_print(f"广告工具 - {x1} -> {x2} 图片右滑中...")
        await asyncio.sleep(1)
        rect2 = await self.page.evaluate("ele => ele.getBoundingClientRect()", sp_selector)
        current_smooth_count += 1
        if rect == rect2:
            return await self.smooth_pic(sp_selector, 'right' if pic_direction == 'left' else 'left',
                                         current_smooth_count, max_smooth_count)
        else:
            return await self.smooth_pic(sp_selector, pic_direction, current_smooth_count, max_smooth_count)

    # 判断当前element是否为下拉形式，是返回next的element
    async def next_element(self, current_element: ElementHandle):
        next_selector = None
        for show_selector in self.show_selectors:
            if show_selector is None:
                break
            ss_list = show_selector.split(">>")
            for idx in range(len(ss_list)):
                ss = ss_list[idx].strip()
                flag = await self.check_element_contains(ss, current_element)
                if flag and len(ss_list) > idx + 1:
                    await self.my_print(f"ss_list长度: {len(ss_list)}  idx值: {idx}")
                    next_selector = ss_list[idx + 1]
                    break
        if next_selector is None:
            return None

        (temp_element, flag) = await self.rand_element(next_selector)
        temp_element: ElementHandle = temp_element
        flag: bool = flag
        return temp_element if flag else None

    # 有指定标签的目标性滑动，并点击、浏览、退出
    async def specify_element(self, sp_element: ElementHandle, event=None):
        await self.my_print(f"sp_element点击目标为: {await sp_element.get_attribute('href')}")
        sp_rect = await self.swipe_position(sp_element, [])
        if isinstance(sp_rect, bool):
            if not sp_rect:
                await self.my_print("广告工具 - 滑动页面返回false, 后退, 重新选择进入")
                await self.page_back()
            return False
        rect = await self.page.evaluate("ele => ele.getBoundingClientRect()", sp_element)
        if rect is not None:
            width = rect["width"]
            height = rect["height"]
            left = rect['left']
            top = rect['top']
            if top > self.screen_height or 0 > top:
                await self.my_print(f"广告工具 - 目标边界值top超出或者小于屏幕高度: {top}, 后退, 重新选择进入")
                await self.page_back()
                return False
            if 0 > left or left > self.screen_width:
                # rect = await self.smooth_pic(sp_element)
                # if isinstance(rect, bool):
                #     await self.my_print(f"广告工具 - 平滑目标中, 出现滑不动情况, 后退, 重新选择进入")
                #     await self.page_back()
                #     return False
                # width = rect["width"]
                # height = rect["height"]
                # left = rect['left']
                # top = rect['top']
                return False
            await self.my_print(f"广告工具 - 点击子页面 -left:", left, " -top:", top, " -width:", width,
                                " -height:", height)

            x = int(left + width * 0.5)
            y = int(top + height * 0.5)
            await self.my_print(f"广告工具 - 点击子页面 -x:", x, " -y:", y)
            si_html = ((await sp_element.inner_html()).replace(" ", "")
                       .replace("\n", "").replace("\t", ""))
            last_page_url = copy.deepcopy(self.page.url)

            # 检查当前页面浏览完成后是否退出
            temp_visit_suc_and_back = False
            for bs in self.back_selectors:
                temp_flag = await self.check_element_contains(bs, sp_element)
                if temp_flag:
                    await self.my_print(f"广告工具 - 进入的页面为指定退出页面, 浏览结束后退出")
                    temp_visit_suc_and_back = True
                    break
            # 记录当前跳转页面href
            temp_href = await self.page.evaluate("""
                       (sp_element) => sp_element.href
                   """, sp_element)
            await self.my_print(f"广告工具 - 点击目标的href为: {temp_href}")

            try:
                # 等待页面加载完成
                await self.page_click(x, y)
                await self.wait_ready_state()
                current_page_url = self.page.url
                if current_page_url is not None and current_page_url == last_page_url:
                    # 先判断是否点击标签后展开ul样式了
                    next_element = await self.next_element(sp_element)
                    # 点击当前按钮存在下一个按钮
                    if next_element is not None:
                        return await self.specify_element(next_element)
                    # 不存在下一个按钮
                    await self.my_print("广告工具 - 点击操作后页面未进入, 再次点击")
                    await self.page_click(x, y)
                    await self.wait_ready_state()
                    if self.page.url is not None and self.page.url == last_page_url:
                        # self.non_clickable_handles.append(sp_element)
                        await self.my_print("广告工具 - 在本页面中继续浏览")

                temp_md5 = hashlib.md5(si_html.encode()).hexdigest()

                if temp_md5 not in self.js_handles_md5:
                    self.js_handles_md5.append(temp_md5)
                    await self.my_print(f"广告工具 - 点击后页面加载并进入成功, 当前Element的md5: {temp_md5}")
                # 当前页面对象记录并下次不在触发
                self.non_clickable_handles.append(sp_element)
                # 点击前标签的href地址
                if temp_href is not None:
                    self.browse_a_href.append(temp_href)
                    await self.my_print(f"已浏览的href列表: {self.browse_a_href}")

                # 若当前页的地址不包含广告域名，则浏览结束后退出
                if self.ads_domain not in self.page.url:
                    await self.my_print(f"广告工具 - 进入的页面非广告域名, 浏览结束后退出")
                    temp_visit_suc_and_back = True

                # 判断当前页面是否存在已知的video
                current_page_video_selector = None
                for vs in self.video_selectors:
                    if len(await self.page.query_selector_all(vs)) > 0:
                        current_page_video_selector = vs
                        await self.my_print(f"广告工具 - 当前页面存在video: {current_page_video_selector}")
                        break
                # 概率性 是否触发观看video操作
                if current_page_video_selector is not None and random.random() < 0 and event is None:
                    await self.my_print(f"广告工具 - 当前页面存在video, 同时满足触发条件, 开始播放video")
                    (temp_element, flag) = await self.rand_element(current_page_video_selector)
                    temp_element: ElementHandle = temp_element
                    flag: bool = flag
                    if flag:
                        return await self.specify_element(temp_element, "video click")

                if event == 'video click' and random.random() < 0:
                    await self.my_print(f"广告工具 - 播放video, 停留观看")
                    child_load_suc_time = await self.page_visit(True)
                else:
                    await self.my_print(f"广告工具 - 页面随机滑动")
                    child_load_suc_time = await self.page_visit()
                if temp_visit_suc_and_back:
                    await self.page_back()
                return child_load_suc_time
            except Exception as e:
                await self.my_print(f"广告工具 - 点击子页面异常:", str(traceback.format_exc()))
                await self.reload_page()
        return False

    # 检查当前页面是否为广告首页，不是则后退。若退到任务首页或者任务子页面则终止广告工具继续执行
    async def page_position(self):
        # await self.page.wait_for_load_state("domcontentloaded")
        await self.wait_ready_state()
        current_url = copy.deepcopy(self.page.url)
        await self.my_print(f"广告工具 - 定位当前页面: {current_url}")
        if current_url == self.index_page_url:
            return True
        elif current_url.startswith(self.index_page_host) or current_url.startswith(
                self.child_page_host):
            return False
        elif current_url in 'chrome-error://chromewebdata/':
            await self.page_back()
            return await self.page_position()
        else:
            await self.page_back()
            return await self.page_position()

    # 每次点击都重新获取当前page对象
    async def reload_page(self):
        try:
            pages_len = len(self.context.pages)
            self.page = self.context.pages[pages_len - 1]
            readyState = await self.page.evaluate("document.readyState")
            start_time = time.time()
            # 页面等待时间超过10s则重载当前页面
            while readyState not in self.default_ready_state and time.time() - start_time < 10:
                await asyncio.sleep(1)
                await self.my_print(f"广告工具 - 当前页面: {self.page.url}, 页面状态: {readyState}")
            if readyState in self.default_ready_state:
                return pages_len
            raise Exception("广告工具 - 当前上下文可能丢失了")
        except Exception as e:
            error = str(traceback.format_exc())
            if "Execution context was destroyed" in error:
                self.context = self.browser.contexts[0]
                return await self.reload_page()

    # 点击cookie
    async def cookie_find_click(self):
        await self.reload_page()
        for cookie_selectors in self.ads_cookie_selectors:
            try:
                cookie_btn = await self.page.query_selector_all(cookie_selectors)
                await self.cookie_click(cookie_btn)
            except Exception as e:
                await self.my_print(f"未发现当前selector: {cookie_selectors}")
                continue

    # cookie 点击
    async def cookie_click(self, cookie_btn: list[ElementHandle]):
        if len(cookie_btn) > 0:
            for cookie in cookie_btn:
                rect = await self.page.evaluate("ele => ele.getBoundingClientRect()", cookie)
                if rect is not None:
                    width = rect["width"]
                    height = rect["height"]
                    if width > 0 and height > 0:
                        await self.my_print("广告工具 - 存在cookie管理界面")
                        left = rect['left']
                        top = rect['top']
                        x = int(left + width * 0.5)
                        y = int(top + height * 0.5)
                        await self.page_click(x, y)
                        await asyncio.sleep(random.randint(2000, 3000) / 1000)
                        await self.wait_ready_state()
                        await self.my_print("广告工具 - cookie已确定")

    # cookie 点击 改自悟斌js
    async def cookie_find_click2(self):
        ads_cookie_selectors = await js_find_pup_selector(self.page)
        self.ads_cookie_selectors = json.loads(ads_cookie_selectors)
        await self.my_print(f"获取到的ads_cookie_selectors为: {self.ads_cookie_selectors}")
        await self.cookie_find_click()

    # 任务运行
    async def ads_run(self):
        await self.my_print(f"广告工具 - 任务开始")
        await self.page.wait_for_load_state("domcontentloaded")

        await self.wait_ready_state()

        # 任务开始时间
        self.ads_start_time = time.time()
        index_visit_sec = await self.page_visit()
        await self.my_print(
            f"广告工具 - 第{self.current_visit_count}个页面浏览结束, 地址: {self.page.url}, 用时: {index_visit_sec}")

        # 子页面浏览时长
        while (time.time() - self.ads_start_time) < self.ads_max_visits and not self.manual_finished:
            await self.wait_ready_state()

            # 不需要退回首页，直接运行
            child_suc_time = await self.current_page_click()
            if child_suc_time is None:
                continue
            await asyncio.sleep(random.randint(2000, 3000) / 1000)
            await self.my_print(
                f"广告工具 - 第{self.current_visit_count}个页面浏览结束, 地址: {self.page.url}, 用时: {child_suc_time}")

            if self.page.url.startswith(self.index_page_host) or self.page.url.startswith(self.child_page_host):
                await self.my_print(f"广告工具 - 意外退出广告页，结束任务")
                await self.stop()
        # 检查
        await self.my_print("广告工具 - 请稍等, 正在返回到广告首页")
        isAdsIndex = await self.page_position()
        await self.wait_ready_state()
        if isAdsIndex:
            await self.my_print(f"广告工具 - 已返回到[广告首页], {self.page.url}")
        else:
            await self.my_print(f"广告工具 - 已返回到[任务页面], {self.page.url}")
        if not self.manual_finished:
            await self.my_print(f"广告工具 - 已到达指定时间, 任务结束")
        else:
            await self.my_print(f"广告工具 - 手动终止任务, 任务结束")
