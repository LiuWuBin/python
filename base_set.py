import subprocess
import random
import time
import json
import os
import sys
import asyncio
import traceback
from playwright.async_api import Page
from tornado.websocket import WebSocketHandler
from huawei_phone_sid import huawei_phone_sid_object

sys.path.append(os.getcwd())


# 操作的脚本

class BaseSet:
    # playwright的page对象
    myPage: Page
    # 手机sid
    sid = ""
    # websocket连接
    websocket_client: WebSocketHandler
    # 任务session_id，点击滑动命令需要
    session_id = ""
    # 服务器下发 - 手机屏幕宽高
    RealMetrics_Width = 1080
    RealMetrics_Height = 1920
    Metrics_Width = 1080
    Metrics_Height = 1920

    # 302跳转的地址，是这样地址，不能算作广告页面计数，并且广告内部点击a元素href以这个开头才是正确的href
    redirectUrlHost_array = ["https://googleads.g.doubleclick.net", "https://adclick.g.doubleclick.net",
                             "https://www.googleadservices.com", "https://related.", "https://presentation.",
                             "https://trc.taboola.com"]

    def __init__(self, playwright_page, sid, websocket_client, session_id, RealMetrics_Width, RealMetrics_Height,
                 Metrics_Width, Metrics_Height):
        self.myPage = playwright_page
        self.sid = sid
        self.websocket_client = websocket_client
        self.session_id = session_id
        self.RealMetrics_Width = RealMetrics_Width
        self.RealMetrics_Height = RealMetrics_Height
        self.Metrics_Width = Metrics_Width
        self.Metrics_Height = Metrics_Height

    async def my_print(self, *args):
        nowTime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        print(nowTime, self.sid, *args)

    async def page_click(self, x, y):
        await self.my_print("page_click -x:", x, " -y:", y)
        x = int(x)
        y = int(y)
        screenWidth = 360
        screenHeight = 640
        # 点击的时候，注意区别手机真实的分辨率
        visualViewport_width = await self.myPage.evaluate("window.visualViewport.width")
        await self.my_print("visualViewport_width:", visualViewport_width)
        if visualViewport_width == 360:
            screenWidth = 360
            screenHeight = 640
        if visualViewport_width == 540:
            screenWidth = 540
            screenHeight = 960
        visualViewport_height = await self.myPage.evaluate("window.visualViewport.height")
        screenOtherHeight = screenHeight - visualViewport_height
        js_screenWidth = await self.myPage.evaluate("window.screen.width")
        js_screenHeight = await self.myPage.evaluate("window.screen.height")
        await self.my_print("js_screenWidth:", js_screenWidth, " -js_screenHeight:", js_screenHeight)
        await self.my_print("screenWidth:", screenWidth, "screenHeight:", screenHeight, " -visualViewport_height:",
                            visualViewport_height, " -screenOtherHeight:", screenOtherHeight)
        y = y + screenOtherHeight
        clickX = self.RealMetrics_Width / screenWidth * x
        clickY = self.RealMetrics_Height / screenHeight * y
        screenButtonHeight = self.RealMetrics_Height - self.Metrics_Height
        # 华为云手机，屏幕没有虚拟按钮，也会有差值
        if not ((self.RealMetrics_Height == 1280) and (self.Metrics_Height == 1184)):
            clickY = clickY - screenButtonHeight
        clickX = int(clickX)
        clickY = int(clickY)
        clickObject = {"type": "click", "sessionId": self.session_id, "startX": clickX, "startY": clickY}
        await self.my_print("点击:", json.dumps(clickObject))
        await self.websocket_client.write_message(json.dumps(clickObject))

    async def page_swipeUp(self):
        # x:屏幕的 0.35 - 0.65
        # y:屏幕的 0.35 - 0.65
        x_left = int(self.Metrics_Width * 0.35)
        x_right = int(self.Metrics_Width * 0.65)
        y_top = int(self.Metrics_Height * 0.35)
        y_bottom = int(self.Metrics_Height * 0.65)
        swipeX = random.randint(x_left, x_right)
        start_x = swipeX + random.randint(-15, 15)
        start_y = y_bottom + random.randint(-15, 15)
        end_x = swipeX + random.randint(-15, 15)
        end_y = y_top + random.randint(-15, 15)
        duration = random.randint(300, 450)
        scrollObject = {"type": "scroll", "sessionId": self.session_id, "startX": start_x, "startY": start_y, "toX": end_x, "toY": end_y}
        await self.my_print("向上滑动:", json.dumps(scrollObject))
        await self.websocket_client.write_message(json.dumps(scrollObject))

    async def page_swipeDown(self):
        # x:屏幕的 0.35 - 0.65
        # y:屏幕的 0.35 - 0.65
        x_left = int(self.Metrics_Width * 0.35)
        x_right = int(self.Metrics_Width * 0.65)
        y_top = int(self.Metrics_Height * 0.35)
        y_bottom = int(self.Metrics_Height * 0.65)
        swipeX = random.randint(x_left, x_right)
        start_x = swipeX + random.randint(-15, 15)
        start_y = y_top + random.randint(-15, 15)
        end_x = swipeX + random.randint(-15, 15)
        end_y = y_bottom + random.randint(-15, 15)
        duration = random.randint(300, 450)
        scrollObject = {"type": "scroll", "sessionId": self.session_id, "startX": start_x, "startY": start_y, "toX": end_x, "toY": end_y}
        await self.my_print("向下滑动:", json.dumps(scrollObject))
        await self.websocket_client.write_message(json.dumps(scrollObject))

    async def page_coordinate_transformation(self, x, y):
        screenWidth = 360
        screenHeight = 640
        # 点击的时候，注意区别手机真实的分辨率
        visualViewport_width = await self.myPage.evaluate("window.visualViewport.width")
        await self.my_print("visualViewport_width:", visualViewport_width)
        if visualViewport_width == 360:
            screenWidth = 360
            screenHeight = 640
        if visualViewport_width == 540:
            screenWidth = 540
            screenHeight = 960
        visualViewport_height = await self.myPage.evaluate("window.visualViewport.height")
        screenOtherHeight = screenHeight - visualViewport_height
        js_screenWidth = await self.myPage.evaluate("window.screen.width")
        js_screenHeight = await self.myPage.evaluate("window.screen.height")
        await self.my_print("js_screenWidth:", js_screenWidth, " -js_screenHeight:", js_screenHeight)
        await self.my_print("screenWidth:", screenWidth, "screenHeight:", screenHeight, " -visualViewport_height:",
                            visualViewport_height, " -screenOtherHeight:", screenOtherHeight)
        y = y + screenOtherHeight
        clickX = self.RealMetrics_Width / screenWidth * x
        clickY = self.RealMetrics_Height / screenHeight * y
        screenButtonHeight = self.RealMetrics_Height - self.Metrics_Height
        clickY = clickY - screenButtonHeight
        clickX = int(clickX)
        clickY = int(clickY)
        return clickX, clickY

    async def page_swipe(self, start_x, start_y, end_x, end_y):
        startX, startY = self.page_coordinate_transformation(start_x, start_y)
        endX, endY = self.page_coordinate_transformation(end_x, end_y)
        scrollObject = {"type": "scroll", "sessionId": self.session_id, "startX": startX, "startY": startY,
                        "toX": endX, "toY": endY}
        if start_y > end_y:
            await self.my_print("向上滑动:", json.dumps(scrollObject))
        else:
            await self.my_print("向下滑动:", json.dumps(scrollObject))
        await self.websocket_client.write_message(json.dumps(scrollObject))

    async def page_back(self):
        # keyevent 4 返回键
        local_sid_port = str(self.sid) + ":5555"
        if local_sid_port in huawei_phone_sid_object:
            huawei_sid_port = huawei_phone_sid_object[local_sid_port]
            backCommand = "adb -s " + huawei_sid_port + " shell input keyevent 4"
        else:
            backCommand = "adb -s " + local_sid_port + " shell input keyevent 4"
        await self.my_print("返回:", backCommand)
        subprocess.call(backCommand, shell=True)

    async def page_randomSwipe(self):
        scrollTop = 0
        try:
            scrollTop = await asyncio.wait_for(self.myPage.evaluate("document.documentElement.scrollTop || document.body.scrollTop"), timeout=5)
        except asyncio.TimeoutError:
            await self.my_print("scrollTop 获取异常")

        scrollHeight = 880
        try:
            scrollHeight = await asyncio.wait_for(self.myPage.evaluate("document.body.scrollHeight"), timeout=5)
        except asyncio.TimeoutError:
            await self.my_print("scrollHeight 获取异常")

        innerHeight = 880
        try:
            innerHeight = await asyncio.wait_for(self.myPage.evaluate("window.visualViewport.height"), timeout=5)
        except asyncio.TimeoutError:
            await self.my_print("innerHeight 获取异常")

        await self.my_print("判断是否滑动到最底部 - scrollTop:", scrollTop, " - innerHeight:", innerHeight,
                            " - scrollHeight:", scrollHeight)
        if scrollTop <= (innerHeight * 0.33):
            await self.my_print("接近顶部，向上滑动")
            await self.page_swipeUp()
        else:
            if scrollTop >= (scrollHeight - innerHeight * 1.33):
                await self.my_print("接近底部，向下滑动")
                await self.page_swipeDown()
            else:
                swipeRandom = random.randint(1, 100)
                if swipeRandom <= 70:
                    await self.my_print("接近中部，随机向上滑动")
                    await self.page_swipeUp()
                else:
                    await self.my_print("接近中部，随机向下滑动")
                    await self.page_swipeDown()

    async def page_step_swipe(self, start_x: int, start_y: int, end_x: int, end_y: int, step: int, wait_time=None):
        startX, startY = await self.page_coordinate_transformation(start_x, start_y)
        endX, endY = await self.page_coordinate_transformation(end_x, end_y)
        scrollObject = {"type": "scrollByStep", "sessionId": self.session_id,
                        "startX": startX, "startY": startY,
                        "toX": endX, "toY": endY, "step": step}
        if start_y > end_y:
            await self.my_print("向上滑动:", json.dumps(scrollObject))
        elif start_y == end_y:
            await self.my_print("平滑:", json.dumps(scrollObject))
        else:
            await self.my_print("向下滑动:", json.dumps(scrollObject))
        await self.websocket_client.write_message(json.dumps(scrollObject))
        if wait_time is not None:
            await self.myPage.wait_for_timeout(wait_time)

    # 广告页面点击按钮
    async def some_setting(self):
        await self.my_print("some_setting")
        try:
            # 广告页面的一些按钮，先用js点击
            jsCode = """
            try {
                //some test
                let allNode = document.getElementsByTagName("*");
                for (let index = 0; index < allNode.length; index++) {
                    let element = allNode[index];
                    let element_classList = element.classList;
                    if (element_classList.contains("topContenBox")) {
                        let float_img = element.querySelector("img[src*='table-C.png']");
                        if(float_img != null){
                            element.style.display = "none";
                        }
                    }
                    let rect = element.getBoundingClientRect();
                    let width = rect.width;
                    if(width >= 800){
                        let screen_width = window.visualViewport.width;
                        element.style.setProperty("width", screen_width + "px");
                    }
                }
                //Accept All Cookies - Accept Cookies
                let accept_result = false;
                for (let index = 0; index < allNode.length; index++) {
                    let element = allNode[index];
                    let tagName = element.tagName;
                    if (tagName != null) {
                        tagName = tagName.toLowerCase();
                    }
                    let element_id = element.getAttribute("id");
                    if (element_id != null) {
                        element_id = element_id.toLowerCase();
                    } else {
                        element_id = "";
                    }
                    let element_classList = element.classList;
                    let element_ariaLabel = element.getAttribute("aria-label");
                    if (element_ariaLabel != null) {
                        element_ariaLabel = element_ariaLabel.toLowerCase();
                    } else {
                        element_ariaLabel = "";
                    }
                    let element_onclick = element.getAttribute("onclick");
                    if (element_onclick != null) {
                        element_onclick = element_onclick.toLowerCase();
                    } else {
                        element_onclick = "";
                    }
                    let element_value = element.getAttribute("value");
                    if (element_value != null) {
                        element_value = element_value.toLowerCase();
                    } else {
                        element_value = "";
                    }
                    let element_dataset = element.dataset;
                    if (tagName == "button") {
                        if (element_id == "onetrust-accept-btn-handler" ||
                            element_id == "tracking-consent-dialog-accept" ||
                            element_id == "adopt-accept-all-button") {
                            accept_result = true;
                            element.click();
                        }
                        if (element_id.includes("cookie") && element_id.includes("accept")) {
                            accept_result = true;
                            element.click();
                        }
                        if (element_ariaLabel.includes("accept") || element_ariaLabel.includes("confirm") || element_ariaLabel.includes("agree")) {
                            accept_result = true;
                            element.click();
                        }
                        if ((element_onclick.includes("cookie") && element_onclick.includes("accept"))
                            || (element_onclick.includes("confirmhcp"))) {
                            accept_result = true;
                            element.click();
                        }
                        if (element_classList.contains("agree-button") ||
                            element_classList.contains("eu-cookie-compliance-default-button") ||
                            element_classList.contains("confirm-button")) {
                            accept_result = true;
                            element.click();
                        }
                        if (element_value == "yes") {
                            accept_result = true;
                            element.click();
                        }
                        for (let key in element_dataset) {
                            if (Object.hasOwnProperty.call(element_dataset, key)) {
                                let value = element_dataset[key];
                                if (value == "accept") {
                                    accept_result = true;
                                    element.click();
                                }
                            }
                        }
                    }
                    if (tagName == "a") {
                        if (element_id == "hs-eu-confirmation-button" ||
                            element_id == "cookie_action_close_header") {
                            accept_result = true;
                            element.click();
                        }
                    }
                    if (tagName == "div") {
                        if (element_classList.contains("cookie-btn")) {
                            accept_result = true;
                            element.click();
                        }
                    }
                }
                if (!accept_result) {
                    let cookie_setting_result = false;
                    //Cookies Settings - Confirm My Choices
                    for (let index = 0; index < allNode.length; index++) {
                        let element = allNode[index];
                        let tagName = element.tagName;
                        if (tagName != null) {
                            tagName = tagName.toLowerCase();
                        }
                        let element_id = element.getAttribute("id");
                        if (element_id != null) {
                            element_id = element_id.toLowerCase();
                        } else {
                            element_id = "";
                        }
                        let element_classList = element.classList;
                        let element_ariaLabel = element.getAttribute("aria-label");
                        if (element_ariaLabel != null) {
                            element_ariaLabel = element_ariaLabel.toLowerCase();
                        } else {
                            element_ariaLabel = "";
                        }
                        if (tagName == "button") {
                            if (element_id == "onetrust-pc-btn-handler") {
                                cookie_setting_result = true;
                                element.click();
                            }
                            if (!element_ariaLabel.includes("close")) {
                                if (element_classList.contains("onetrust-close-btn-handler")) {
                                    cookie_setting_result = true;
                                    element.click();
                                }
                            }
                        }
                    }
                    if (!cookie_setting_result) {
                        //close
                        for (let index = 0; index < allNode.length; index++) {
                            let element = allNode[index];
                            let tagName = element.tagName;
                            if (tagName != null) {
                                tagName = tagName.toLowerCase();
                            }
                            let element_id = element.getAttribute("id");
                            if (element_id != null) {
                                element_id = element_id.toLowerCase();
                            } else {
                                element_id = "";
                            }
                            let element_classList = element.classList;
                            let element_ariaLabel = element.getAttribute("aria-label");
                            if (element_ariaLabel != null) {
                                element_ariaLabel = element_ariaLabel.toLowerCase();
                            } else {
                                element_ariaLabel = "";
                            }
                            if (tagName == "button") {
                                if (element_id == "banner-close-button" ||
                                    element_id == "cboxClose") {
                                    element.click();
                                }
                                if (element_ariaLabel.includes("close") || element_ariaLabel.includes("dismiss")) {
                                    element.click();
                                }
                                if (element_classList.contains("cookie-alert-close-btn") ||
                                    element_classList.contains("slidedown-button") ||
                                    element_classList.contains("ub-emb-close") ||
                                    element_classList.contains("sparkle-close")) {
                                    element.click();
                                }
                            }
                            if (tagName == "img") {
                                let element_src = element.getAttribute("src");
                                if (element_src != null) {
                                    element_src = element_src.toLowerCase();
                                } else {
                                    element_src = "";
                                }
                                if (element_src.includes("close-btn")) {
                                    element.click();
                                }
                            }
                        }
                    }
                }
                //other click
                for (let index = 0; index < allNode.length; index++) {
                    let element = allNode[index];
                    let tagName = element.tagName;
                    if (tagName != null) {
                        tagName = tagName.toLowerCase();
                    }
                    let element_id = element.getAttribute("id");
                    if (element_id != null) {
                        element_id = element_id.toLowerCase();
                    } else {
                        element_id = "";
                    }
                    let element_ariaLabel = element.getAttribute("aria-label");
                    if (element_ariaLabel != null) {
                        element_ariaLabel = element_ariaLabel.toLowerCase();
                    } else {
                        element_ariaLabel = "";
                    }
                    if (tagName == "a") {
                        let element_data_audience = element.getAttribute("data-audience");
                        if (element_data_audience == "hcp") {
                            element.click();
                        }
                    }
                }
            } catch (error) {
                
            }
            """
            asyncio.create_task(self.myPage.evaluate(jsCode))
        except Exception as e:
            await self.my_print("some_setting-异常:", str(traceback.format_exc()))
