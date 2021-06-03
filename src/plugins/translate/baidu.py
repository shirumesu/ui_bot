import os
import random
import httpx
import base64
import string
import hashlib
from PIL import Image
from typing import Tuple
from retrying import retry
from loguru import logger

import config
from src.plugins.translate import embed


url_high = 'https://aip.baidubce.com/rest/2.0/ocr/v1/accurate'
url_low = 'https://aip.baidubce.com/rest/2.0/ocr/v1/general'


async def process(image_url: str, vertical: bool) -> Tuple[dict, str]:
    """对单张图片进行各种请求,ocr以及翻译等

    Args:
        image_url (str): 图片的链接
        vertical (bool): 图片是否为竖板,竖板横版处理方法有微小不同

    Returns:
        Tuple[dict,str]: 再次整理封装的文字ocr数据以及图片路径
    """
    path = await save_image(image_url)
    image = Image.open(path)
    size = image.size
    try:
        word_res = (await baidu_ocr(path))['words_result']
    except:
        word_res = (await baidu_ocr(path, False))['word_result']
    words_data, path = await embed.process_photo(word_res, size, path, vertical)
    return words_data, path


@retry(stop_max_attempt_number=5)
async def save_image(url: str) -> str:
    """下载保存图片

    Args:
        url (str): 图片链接

    Returns:
        str: 保存路径
    """
    async with httpx.AsyncClient(proxies=config.proxies_for_all, timeout=15) as s:
        res = await s.get(url)
        if res.status_code != 200:
            raise RuntimeError
    path = os.path.join(config.res, 'cacha', 'translate', ''.join(
        random.sample(string.ascii_letters + string.digits, 8)) + '.png')
    with open(path, 'wb') as f:
        f.write(res.content)
    return path


@retry(stop_max_attempt_number=3)
async def baidu_ocr(image_path: str, accuracy_high: bool = True) -> dict:
    """请求百度api

    Args:
        image_path (str): 图片的链接地址
        accuracy_high (bool, optional): 是否使用高精度模式. Defaults to True.

    Raises:
        RuntimeError: 请求失败raise错误retry

    Returns:
        dict: api返回的ocr结果
    """
    url = f'https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={config.baidu_ocr_client_id}&client_secret={config.baidu_ocr_client_secret}'
    with open(image_path, 'rb') as f:
        image = base64.b64encode(f.read())
    data = {
        'image': image,
        'language_type': 'auto_detect' if accuracy_high else 'JRA',
        'vertexes_location': 'True'
    }
    header = {
        'content-type': 'application/x-www-form-urlencoded'
    }
    para = {
        'access_token': None
    }
    async with httpx.AsyncClient(proxies=config.proxies_for_all, timeout=15) as s:
        res = await s.get(url)
        if res.status_code != 200:
            logger.error('请求百度ocr翻译错误,无法获取token')
            raise RuntimeError
        js = res.json()
        para['access_token'] = js['access_token']
        response = await s.post(url_high if accuracy_high else url_low, data=data, params=para, headers=header)
    return response.json()


@retry(stop_max_attempt_number=5)
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
    sign_text = data["appid"] + data["q"] + \
        str(data["salt"]) + data["secretKey"]
    data["sign"] = hashlib.md5(sign_text.encode()).hexdigest()
    async with httpx.AsyncClient(params=data, proxies=config.proxies_for_all, timeout=15) as s:
        res = await s.get(url)
        if res.status_code != 200:
            logger.error('请求百度翻译出现错误,返回码:' + res.status_code)
            raise RuntimeError
    res = res.json()
    if 'error_code' in res:
        logger.error('请求百度翻译api出现错误' + res['error_code'])
        raise RuntimeError

    for i in res['trans_result']:
        text = text.replace(i['src'], i['dst'])
    return text
