import re
from urllib.parse import urlparse, parse_qs, unquote

target_param_list = ["&adurl="]
protocol_https = "https://"
protocol_http = "http://"


def check_ad_real_url(url):
    result = ""
    try:
        if (url != "") and (url is not None):
            decoded_url = unquote(url)
            parsed_url = urlparse(decoded_url)
            url_lower = decoded_url.lower()
            url_is_contain_target_param = False
            for target_param in target_param_list:
                pattern_https = r'' + target_param + protocol_https + '[a-zA-Z]'
                if re.search(pattern_https, url_lower):
                    url_is_contain_target_param = True
                    break
                pattern_http = r'' + target_param + protocol_http + '[a-zA-Z]'
                if re.search(pattern_http, url_lower):
                    url_is_contain_target_param = True
                    break
            if url_is_contain_target_param:
                query_params = parse_qs(parsed_url.query)
                for key, values in query_params.items():
                    for value in values:
                        value_lower = value.lower()
                        if value_lower.startswith("http"):
                            value_lower_is_contain_target_param = False
                            for target_param in target_param_list:
                                pattern_https = r'' + target_param + protocol_https + '[a-zA-Z]'
                                if re.search(pattern_https, value_lower):
                                    value_lower_is_contain_target_param = True
                                    break
                                pattern_http = r'' + target_param + protocol_http + '[a-zA-Z]'
                                if re.search(pattern_http, value_lower):
                                    value_lower_is_contain_target_param = True
                                    break
                            if value_lower_is_contain_target_param:
                                result = check_ad_real_url(value_lower)
                            else:
                                result = value_lower
            else:
                result = url
    except Exception as e:
        print(f'check_ad_real_url错误：{e}')
    if (result is None) or (result == ""):
        result = url
    return result


# 如果获取的ad_real_url结果是https://ad.doubleclick.net,再次检测
def check_doubleclick_url(url):
    result = ""
    try:
        if (url != "") and (url is not None):
            decoded_url = unquote(url)
            parsed_url = urlparse(decoded_url)
            query_params = parse_qs(parsed_url.query)
            for key in query_params:
                if key.startswith("http"):
                    key_is_contain_target_param = False
                    pattern_https = r'' + protocol_https + '[a-zA-Z]'
                    if re.search(pattern_https, key):
                        key_is_contain_target_param = True
                    pattern_http = r'' + protocol_http + '[a-zA-Z]'
                    if re.search(pattern_http, key):
                        key_is_contain_target_param = True
                    if key_is_contain_target_param:
                        result = key
    except Exception as e:
        print(f'check_ad_real_url_second错误：{e}')
    if (result == "") or (result is None):
        result = url
    return result
