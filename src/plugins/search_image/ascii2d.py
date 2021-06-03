import httpx
import lxml
from retrying import retry
from bs4 import BeautifulSoup
from loguru import logger

from nonebot import MessageSegment
from six import with_metaclass

import config
from src.plugins.search_image import saucenao_config as sauce


@retry(stop_max_attempt_number=5)
async def search_color(image_url: str) -> str:
    """ascii2d的色合搜索

    Args:
        image_url (str): 图片的地址

    Returns:
        str: 处理好可以直接发送的文本
    """
    url = "https://ascii2d.net/search/url/" + image_url
    async with httpx.AsyncClient(proxies=config.proxies, verify=False, timeout=15) as s:
        res = await s.get(url)
        if res.status_code != 200:
            raise RuntimeError
    color_res = await parser(res.text)
    color_text = await map_text(color_res)
    bovw_text = await search_bovw(color_res['bovw_link'])
    text = ('ascii2d色合搜索\n'
            f'{color_text}'
            '\n============\n'
            f'{bovw_text}')
    return text


async def search_bovw(ascii_url: str) -> str:
    """ascii2d的特征搜索

    Args:
        ascii_url (str): 爬虫得到的特征搜索的地址

    Returns:
        str: 处理好的文本
    """
    async with httpx.AsyncClient(proxies=config.proxies, verify=False, timeout=15) as s:
        res = await s.get(ascii_url)
        if res.status_code != 200:
            raise RuntimeError
    bovw_res = await parser(res.text)
    bovw_text = await map_text(bovw_res)
    text = ('ascii2d特征搜索\n'
            f'{bovw_text}')
    return text


async def map_text(data: dict) -> str:
    """处理消息

    Args:
        data (dict): parser函数封装好的字典

    Returns:
        str: 处理好的消息
    """
    if 'image_link' in data:
        seq = MessageSegment.image(data['image_link'])
    else:
        seq = ''
    if data['is_detail']:
        text = f"图片已有详细登录信息:{data['detail']}\n{seq}"
    else:
        text = (f"图片在{data['platform'] if 'platform' in data else '未知网站'}下\n"
                f"作品名称(或推文时间):{data['work_name'] if 'work_name' in data else '未知'}\n"
                f"作者名称(或是id):{data['user_name'] if 'user_name' in data else '未知'}\n"
                f"作品链接:{data['work_link'] if 'work_link' in data else '未知'}\n"
                f'{seq}')
    return text


async def parser(res: str) -> dict:
    """解析网页

    Args:
        res (str): 爬回来的网页源码

    Returns:
        dict: 封装好的字典
    """
    result = {}
    soup = BeautifulSoup(res, "lxml")

    data = soup.select(
        "div:nth-child(3) > div.detail-link.pull-xs-right.hidden-sm-down.gray-link > span:nth-child(2) > a")
    for item in data:
        result["bovw_link"] = f"https://ascii2d.net{item.get('href')}"
    data = soup.select(
        "div:nth-child(6) > div.col-xs-12.col-sm-12.col-md-4.col-xl-4.text-xs-center.image-box > img")
    for item in data:
        result["image_link"] = f"https://ascii2d.net{item.get('src')}"

    data = soup.select(
        "div:nth-child(6) > div.col-xs-12.col-sm-12.col-md-8.col-xl-8.info-box > div.detail-box.gray-link > strong")
    if data:
        result["is_detail"] = True
        data = soup.select(
            "div:nth-child(6) > div.col-xs-12.col-sm-12.col-md-8.col-xl-8.info-box > div.detail-box.gray-link > div")
        for item in data:
            result["detail"] = item.get_text()
    else:
        result["is_detail"] = False
        data = soup.select(
            "div:nth-child(6) > div.col-xs-12.col-sm-12.col-md-8.col-xl-8.info-box > div.detail-box.gray-link > h6 > a:nth-child(2)")
        for item in data:
            result["work_link"] = item.get("href")
            result["work_name"] = item.get_text()
        data = soup.select(
            "div:nth-child(6) > div.col-xs-12.col-sm-12.col-md-8.col-xl-8.info-box > div.detail-box.gray-link > h6 > a:nth-child(3)")
        for item in data:
            #result["user_link"] = item.get("href")
            result["user_name"] = item.get_text()
        data = soup.select(
            "div:nth-child(6) > div.col-xs-12.col-sm-12.col-md-8.col-xl-8.info-box > div.detail-box.gray-link > h6 > small")
        for item in data:
            result["platform"] = item.get_text().strip()
    return result
