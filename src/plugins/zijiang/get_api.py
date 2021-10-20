import json
import time

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


@retry(logger=logger)
async def haha():
    params = {"timeRangeMode": 2, "sortMode": 0, "pageNum": 1, "pageSize": 10}
    async with async_uiclient(request_params=params) as client:
        res = await client.uiget("https://asoulcnki.asia/v1/api/ranking/")
    js = res.json()
    return [
        f"用户名: {i['m_name']}(uid: {i['mid']})\n评论: {i['content']}\n发布时间: {time.strftime('%Y年%m月%d日 %H:%M:%S',time.localtime(int(i['ctime'])))}"
        for i in js["data"]["replies"]
    ]
