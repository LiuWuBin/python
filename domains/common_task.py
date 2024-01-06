import json
from playwright.async_api import async_playwright, Playwright
from public_utils import PublicUtils
from public_utils_new import PublicUtils_new


class AdTask:
    # 公共类对象
    pu: PublicUtils = None
    pu_new: PublicUtils_new = None

    def __init__(self, websocket_client, session_id, sid, device_port, ad_base_url, real_metrics_width,
                 real_metrics_height, metrics_width, metrics_height, task_page_duration, task_click_rate,
                 task_page_view, task_time_max, task_json_info, ggw_json_info, gmail, search_key, task_url_id, base_url, extra):
        # 参数赋予共享变量中
        isGgwModel = "0"
        if extra != "":
            extra_object = json.loads(extra)
            if "isGgwModel" in extra_object:
                isGgwModel = extra_object["isGgwModel"]
        if isGgwModel == "1":
            self.pu_new = PublicUtils_new(websocket_client, session_id, sid, device_port, ad_base_url, real_metrics_width,
                                          real_metrics_height, metrics_width, metrics_height, task_page_duration, task_click_rate,
                                          task_page_view, task_time_max, task_json_info, ggw_json_info, gmail, search_key, task_url_id, base_url, extra)
        else:
            self.pu = PublicUtils(websocket_client, session_id, sid, device_port, ad_base_url, real_metrics_width,
                                  real_metrics_height, metrics_width, metrics_height, task_page_duration, task_click_rate,
                                  task_page_view, task_time_max, task_json_info, extra)

    async def start_task(self):
        async def run(p: Playwright):
            if self.pu is not None:
                await self.pu.task_run(p, False)
            if self.pu_new is not None:
                await self.pu_new.task_run(p, True)

        async with async_playwright() as playwright:
            await run(playwright)

    async def task_data(self):
        if self.pu is not None:
            return await self.pu.task_data()
        if self.pu_new is not None:
            return await self.pu_new.task_data()

    async def finish_task(self):
        if self.pu is not None:
            await self.pu.finish_task()
            del self.pu
        if self.pu_new is not None:
            await self.pu_new.finish_task()
            del self.pu_new
