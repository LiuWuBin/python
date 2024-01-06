from playwright.async_api import Page
from ads.ads_config_menu import *
from ads.ads_config_cookie import *


# video
c_video = [
    # https://hemanext.com/moa-video
    "a[class='et_pb_video_play']"
]


# back
c_back = [
    # https://www.samsung.com.cn/
    "a[class='footer-category__link']",
]

# 可点击标签
c_click = [
    "a",
]

# 可点击标签的补充
c_click += [item.strip() for cul in c_menu for item in cul.split(">>")]


# js 获取弹出层的点击的selector
async def js_find_pup_selector(page: Page):
    js_method = """
       () => {
           function getSelector(element) {
               if (!(element instanceof Element)) return;

               const selectors = [];

               while (element.parentNode) {
                   let selector = element.tagName.toLowerCase();

                   if (element.id) {
                       selector += `#${element.id}`;
                       selectors.unshift(selector);
                       break; // Stop at the first ID found
                   } else if (element.className) {
                       const classes = Array.from(element.classList).join('.');
                       selector += `.${classes}`;
                   }

                   selectors.unshift(selector);
                   element = element.parentNode;
               }

               return selectors.join(' > ');
           }

           function findSelector() {
               // 所有需要点击的selector
               let need_click_selectors = []
               // 所有节点
               let allNode = document.getElementsByTagName("*");
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
                   if (tagName === "button") {
                       if (element_id === "onetrust-accept-btn-handler" ||
                           element_id === "tracking-consent-dialog-accept" ||
                           element_id === "adopt-accept-all-button") {
                           accept_result = true;
                           need_click_selectors.push(getSelector(element));
                       }
                       if (element_id.includes("cookie") && element_id.includes("accept")) {
                           accept_result = true;
                           need_click_selectors.push(getSelector(element));
                       }
                       if (element_ariaLabel.includes("accept") || element_ariaLabel.includes("confirm") || element_ariaLabel.includes("agree")) {
                           accept_result = true;
                           need_click_selectors.push(getSelector(element));
                       }
                       if ((element_onclick.includes("cookie") && element_onclick.includes("accept"))
                           || (element_onclick.includes("confirmhcp"))) {
                           accept_result = true;
                           need_click_selectors.push(getSelector(element));
                       }
                       if (element_classList.contains("agree-button") ||
                           element_classList.contains("eu-cookie-compliance-default-button") ||
                           element_classList.contains("confirm-button")) {
                           accept_result = true;
                           need_click_selectors.push(getSelector(element));
                       }
                       if (element_value === "yes") {
                           accept_result = true;
                           need_click_selectors.push(getSelector(element));
                       }
                       for (let key in element_dataset) {
                           if (Object.hasOwnProperty.call(element_dataset, key)) {
                               let value = element_dataset[key];
                               if (value === "accept") {
                                   accept_result = true;
                                   need_click_selectors.push(getSelector(element));
                               }
                           }
                       }
                   }
                   if (tagName === "a") {
                       if (element_id === "hs-eu-confirmation-button" ||
                           element_id === "cookie_action_close_header") {
                           accept_result = true;
                           need_click_selectors.push(getSelector(element));
                       }
                   }
                   if (tagName === "div") {
                       if (element_classList.contains("cookie-btn")) {
                           accept_result = true;
                           need_click_selectors.push(getSelector(element));
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
                       if (tagName === "button") {
                           if (element_id === "onetrust-pc-btn-handler") {
                               cookie_setting_result = true;
                               need_click_selectors.push(getSelector(element));
                           }
                           if (!element_ariaLabel.includes("close")) {
                               if (element_classList.contains("onetrust-close-btn-handler")) {
                                   cookie_setting_result = true;
                                   need_click_selectors.push(getSelector(element));
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
                           if (tagName === "button") {
                               if (element_id === "banner-close-button" ||
                                   element_id === "cboxClose") {
                                   need_click_selectors.push(getSelector(element));
                               }
                               if (element_ariaLabel.includes("close") || element_ariaLabel.includes("dismiss")) {
                                   need_click_selectors.push(getSelector(element));
                               }
                               if (element_classList.contains("cookie-alert-close-btn") ||
                                   element_classList.contains("slidedown-button") ||
                                   element_classList.contains("ub-emb-close") ||
                                   element_classList.contains("sparkle-close")) {
                                   need_click_selectors.push(getSelector(element));
                               }
                           }
                           if (tagName === "img") {
                               let element_src = element.getAttribute("src");
                               if (element_src != null) {
                                   element_src = element_src.toLowerCase();
                               } else {
                                   element_src = "";
                               }
                               if (element_src.includes("close-btn")) {
                                   need_click_selectors.push(getSelector(element));
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
                   if (tagName === "a") {
                       let element_data_audience = element.getAttribute("data-audience");
                       if (element_data_audience === "hcp") {
                           need_click_selectors.push(getSelector(element));
                       }
                   }
               }
               return JSON.stringify(need_click_selectors)
           }

           return findSelector()
       }
       """
    selectors: list[str] = await page.evaluate(js_method)
    return selectors
