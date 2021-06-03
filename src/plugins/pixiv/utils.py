import os
import httpx
import random
import string
from retrying import retry

import config


@retry(stop_max_attempt_number=3)
async def dl_image(url: str) -> list:
    """下载图片的函数

    Args:
        url (str): 图片链接

    Returns:
        list: 保存路径
    """
    async with httpx.AsyncClient(proxies=config.proxies, timeout=25) as s:
        res = await s.get(url)
        if res.status_code == 404:
            url = url.replace(
                'jpg', 'png') if '.jpg' in url else url.replace('png', 'jpg')
            async with httpx.AsyncClient(proxies=config.proxies, timeout=25) as s:
                res = await s.get(url)
                if res.status_code != 200:
                    raise RuntimeError
        elif res.status_code != 200:
            raise RuntimeError
    file_name = ''.join(random.sample(string.ascii_letters + string.digits, 8))
    save_path = os.path.join(config.res, 'cacha', 'pixiv', file_name + '.png')
    with open(save_path, 'wb') as f:
        f.write(res.content)
    return save_path
