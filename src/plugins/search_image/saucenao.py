import os
import httpx
from retrying import retry

from nonebot import MessageSegment

import config
from src.plugins.search_image import saucenao_config as sauce
from soraha_utils import logger


async def text(image_data: dict) -> str:
    """将封装好的图片信息整合成待发送的msg

    Args:
        image_data (dict): 封装好的api return

    Returns:
        str: 直接发送的msg
    """
    try:
        seq = await dl_image(image_data["url_for_dl"])
    except RuntimeError:
        seq = None
    except:
        seq = None
        logger.error("下载图片发现未知错误,下载失败")
    seq = MessageSegment.image("file:///" + seq)
    text = (
        f"\n图片在{image_data['servicename']}下\n"
        f"相似度: {image_data['sim']}\n"
        f"图片标题: {image_data['illid']}(id:{image_data['ill_uid']})\n"
        f"画师名字: {image_data['memid']}(id:{image_data['member_uid']})\n"
        f"图片地址: {image_data['url']}\n"
        f"{'图片已被删除或请求失败' if not seq else seq}"
    )
    return text


@retry(stop_max_attempt_number=5)
async def get_sauce(image_url: str) -> dict:
    """请求SauceNao搜图API

    Args:
        image_url (str): 图片的地址

    Returns:
        dict: 封装好的消息
    """
    url = "https://saucenao.com/search.php"
    data = {
        "output_type": "2",
        "numres": "1",
        "api_key": config.sauceNAO_api,
        "db": 999,
        "url": image_url,
    }
    async with httpx.AsyncClient(
        proxies=config.proxies, params=data, timeout=15, verify=False
    ) as s:
        res = await s.get(url)
        if res.status_code != 200:
            raise RuntimeError
    res = res.json()
    image_data = sauce.get_img_id(res)
    return image_data


@retry(stop_max_attempt_number=5)
async def dl_image(url: str) -> str:
    """下载对应图片

    Args:
        url (str): 图片的连接

    Returns:
        str: 图片保存的路径
    """
    async with httpx.AsyncClient(proxies=config.proxies, verify=False, timeout=15) as s:
        res = await s.get(url)
        if res.status_code != 200:
            raise RuntimeError
    path = os.path.join(config.res, "cacha", "search_image", url[-10:])
    with open(path, "wb") as f:
        f.write(res.content)
    return path
