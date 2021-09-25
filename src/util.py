# 这个文件用于把一些需要bot全局共用的变量导入进来共享防止导入的非常乱
import nonebot
import asyncio
from typing import Callable
from functools import wraps, partial
import src.plugins.bot_manager.shutup

bot = nonebot.get_bot()
shutup = src.plugins.bot_manager.shutup.SHUTUP


def sync_to_async(func: Callable):
    @wraps(func)
    async def run(*args, loop=None, executor=None, **kwargs):
        if loop is None:
            loop = asyncio.get_event_loop()
        pfunc = partial(func, *args, **kwargs)
        return await loop.run_in_executor(executor, pfunc)

    return run
