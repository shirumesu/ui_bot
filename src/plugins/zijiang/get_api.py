import json

from soraha_utils import async_uiclient, retry, logger
import config


@retry(logger=logger)
async def cachong(text):
    headers = {"Content-Type": "application/json"}
    data = json.dumps({"text": text})
    async with async_uiclient(
        proxy=config.proxies_for_all, other_headers=headers, request_data=data
    ) as client:
        res = await client.uipost("https://asoulcnki.asia/v1/api/check")
    return res.json()
