import random
import base64
import hashlib

import config
from src.plugins.translate import embed
from src.ui_exception import baidu_ocr_get_Error
from soraha_utils import retry, logger, async_uiclient


url_high = "https://aip.baidubce.com/rest/2.0/ocr/v1/accurate"
url_low = "https://aip.baidubce.com/rest/2.0/ocr/v1/general"


async def process_manga(image_path: str) -> str:
    word_translate = await baidu_ocr(image_path)
    words_data, path = await embed.process_photo(
        word_translate, image_path=image_path, vertical=True
    )
    path = await embed.process_manga(words_data, path)
    return path


@retry()
async def baidu_ocr(image_path: str) -> dict:
    """请求百度api

    Args:
        image_path (str): 图片的链接地址
        accuracy_high (bool, optional): 是否使用高精度模式. Defaults to True.

    Raises:
        RuntimeError: 请求失败raise错误retry

    Returns:
        dict: api返回的ocr结果
    """
    async with async_uiclient(proxy=config.proxies_for_all) as client:
        res = await client.uiget(
            f"https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={config.baidu_ocr_client_id}&client_secret={config.baidu_ocr_client_secret}"
        )
        res = res.json()

    f = open(image_path, "rb")
    img = base64.b64encode(f.read())
    data = {"image": img, "language_type": "auto_detect", "vertexes_location": "True"}
    header = {"content-type": "application/x-www-form-urlencoded"}
    params = {"access_token": res["access_token"]}

    async with async_uiclient(
        proxy=config.proxies_for_all,
        request_headers=header,
        request_params=params,
        request_data=data,
    ) as client:
        res = await client.uipost("https://aip.baidubce.com/rest/2.0/ocr/v1/accurate")
        res = res.json()

    if "error_code" in res:
        logger.error(f"百度ocr请求发生异常: {res['error_msg']}(code:{res['error_code']})")
        return
    return res["words_result"]


@retry()
async def baidu_fanyi(text: str) -> str:
    """百度翻译api请求函数

    Args:
        text (str): 需要翻译的文本

    Returns:
        str: 翻译结果
    """
    url = "https://fanyi-api.baidu.com/api/trans/vip/translate"
    data = {
        "appid": config.baidu_translate_api_id,
        "secretKey": config.baidu_translate_secret_key,
        "salt": random.randint(32768, 65536),
        "sign": "",
        "q": text,
        "from": "auto",
        "to": "zh",
    }
    if not text:
        return
    sign_text = data["appid"] + data["q"] + str(data["salt"]) + data["secretKey"]
    data["sign"] = hashlib.md5(sign_text.encode()).hexdigest()
    async with async_uiclient(
        request_params=data, proxy=config.proxies_for_all
    ) as client:
        res = await client.uiget(url)
    res = res.json()
    if "error_code" in res:
        logger.error("请求百度翻译api出现错误" + res["error_code"])
        raise RuntimeError

    for i in res["trans_result"]:
        text = text.replace(i["src"], i["dst"])
    return text
