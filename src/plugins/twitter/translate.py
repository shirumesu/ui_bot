import hashlib
import random
import httpx
import asyncio
from retrying import retry

import config

api_id = config.baidu_translate_api_id
secret_key = config.baidu_translate_secret_key


@retry(stop_max_attempt_number=5)
async def baidu_translate(text: str) -> str:
    """调用百度翻译api进行翻译

    Args:
        text (str): 需要翻译的文本

    Returns:
        str: 翻译后的文本
    """
    url = 'https://fanyi-api.baidu.com/api/trans/vip/translate'
    data = {
        'appid': api_id,
        'secretKey': secret_key,
        'salt': random.randint(32768, 65536),
        'sign': '',
        'q': text,
        'from': 'auto',
        'to': 'zh'
    }
    if not text:
        return
    sign = data['appid'] + data['q'] + str(data['salt']) + data['secretKey']
    sign.encode()
    data['sign'] = hashlib.md5(sign.encode()).hexdigest()
    async with httpx.AsyncClient(params=data, proxies=config.proxies_for_all, timeout=15) as s:
        res = await s.get(url)
        if res.status_code != 200:
            raise RuntimeError
        js = res.json()
        if 'error_code' in js:
            await asyncio.sleep(1)
            raise RuntimeError
    for i in js['trans_result']:
        text = text.replace(i['src'], i['dst'])
    return text
