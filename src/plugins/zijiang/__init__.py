import random
import time
from nonebot import CommandSession

from .get_api import cachong, haha
from src.Services import uiPlugin

sv_help = """枝江查重| 使用说明
[小作文查重 (作文)] -> 送去枝江查重
    特别注意:
        字数要求: 10-1000
[随机发病] -> 三天内前十条随机发病集合捏~
"""

sv = uiPlugin(["zijiang", "枝江查重"], False, usage=sv_help)


@sv.ui_command("小作文查重", aliases=("枝江查重",))
async def yanbijinggao(session: CommandSession):
    if (
        len(session.current_arg_text.strip()) < 10
        or len(session.current_arg_text.strip()) > 1000
    ):
        await session.finish("字数要求10-1000捏~")
    res = await cachong(session.current_arg_text.strip())
    if not res["data"]["related"]:
        await session.finish("没有找到小作文捏~")
    else:
        text = (
            f"被发现了捏~\n"
            f"查重率:{int(res['data']['related'][0]['rate'])*100}%\n"
            f"原创|原偷作者: {res['data']['related'][0]['reply']['m_name']}(uid: {res['data']['related'][0]['reply']['mid']})\n"
            f"原文: {res['data']['related'][0]['reply']['content']}\n"
            f"发送时间: {time.strftime('%Y年%m月%d日 %H:%M:%S',time.localtime(int(res['data']['related'][0]['reply']['ctime'])))}\n"
            f"原文链接: {res['data']['related'][0]['reply_url']}"
        )
        await session.finish(text)


@sv.ui_command("随机发病")
async def random_haha(session: CommandSession):
    res = await haha()
    await session.finish(random.choice(res))
