import hashlib
import random
import asyncio

import config
from soraha_utils import retry, logger, async_uiclient

api_id = config.baidu_translate_api_id
secret_key = config.baidu_translate_secret_key


@retry(logger=logger)
async def baidu_translate(text: str) -> str:
    """调用百度翻译api进行翻译

    Args:
        text (str): 需要翻译的文本

    Returns:
        str: 翻译后的文本
    """
    if not text:
        return
    url = "https://fanyi-api.baidu.com/api/trans/vip/translate"
    data = {
        "appid": api_id,
        "secretKey": secret_key,
        "salt": random.randint(32768, 65536),
        "sign": "",
        "q": text,
        "from": "auto",
        "to": "zh",
    }
    sign = data["appid"] + data["q"] + str(data["salt"]) + data["secretKey"]
    data["sign"] = hashlib.md5(sign.encode()).hexdigest()
    async with async_uiclient(
        request_params=data, proxy=config.proxies_for_all
    ) as client:
        res = await client.uiget(url)
        js = res.json()
        if "error_code" in js:
            await asyncio.sleep(1)
            raise RuntimeError
    for i in js["trans_result"]:
        text = text.replace(i["src"], i["dst"])
    return text
