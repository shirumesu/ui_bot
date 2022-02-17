import os

from nonebot import CommandSession, MessageSegment

from soraha_utils import async_uiclient

import config
from src.Services import uiPlugin


sv_help = """60sec看世界 | 使用帮助
括号内的文字即为指令,小括号内为可选文字(是否必带请自行参照使用示例)
[今日新闻] -> 调用60s看世界
"""
sv = uiPlugin(["60sec", "60秒看世界"], False, use_cache_folder=True, usage=sv_help)
image_path = os.path.join(config.res, "cacha", "60sec", "img.png")


@sv.ui_command("今日新闻")
async def daily_news(session: CommandSession):
    url = "https://api.iyk0.com/60s/"
    async with async_uiclient(proxy=config.proxies_for_all) as cl:
        res = await cl.uiget(url)
        res = res.json()
        if res["msg"] != "Success":
            await session.finish(f"有哪里出错了!: {res['msg']}")
        res = await cl.uiget(res["imageUrl"])
        with open(image_path, "wb+") as f:
            f.write(res.content)

    await session.finish(MessageSegment.image("file:///" + image_path))
