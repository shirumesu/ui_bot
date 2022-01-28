import asyncio
import httpx

from nonebot import CommandSession

import config
from src.plugins.search_image import saucenao, ascii2d, ehentai
from src.Services import uiPlugin


sv_help = """以图搜图 | 使用帮助
括号内的文字即为指令,小括号内为可选文字(是否必带请自行参照使用示例)
[搜图(图片)] -> 搜图
    特别注意:
        屎山qq -> qq在文件过大的时候会用文件的方式发出来,此时羽衣无法获取到图片
        多张图片 -> 支持,但请在一个消息内发送所有图片,搜索结果会分多个消息发送
    使用示例:
        搜图 (某张图片):
            -> (结果)
        搜图:
            -> 羽衣不会读心哦,要把图片发出来才行！(这里是羽衣的回复)
            (图片) -> 你的发送(此时发送一张图片):
            -> (结果)
        搜图:
            -> 羽衣不会读心哦,要把图片发出来才行！
            (非图片):
            -> 羽衣不会读心哦,要把图片发出来才行！ 
            (非图片):
            -> (结束搜图)
[搜本(图片)] -> 同上
额外PS：
    由于搜图结果存在R18,并且无法识别去除,如果群里禁用了请:
        使用'联系主人'功能或是直接联系羽衣的维护组 -> 要求开启该插件
        私聊使用:
            -> 如果羽衣不幸被qq封了一次,那么可能会开启此插件私聊白名单
            -> 获取白名单的方法同上
""".strip()
sv = uiPlugin(["search_image", "以图搜图"], True, usage=sv_help, use_cache_folder=True)


@sv.ui_command("搜图", patterns=r"^搜图")
async def search_image(session: CommandSession):
    """搜图功能的主函数

    Args:
        session (CommandSession): bot封装的信息
    """
    image = session.get("image")
    for i in image:
        coro = [saucenao.get_sauce(i), ascii2d.search_color(i)]
        res = await asyncio.gather(*coro, return_exceptions=True)
        ascii2d_text = ""
        if not isinstance(res[0], dict):
            sauce_text = "sauceNao访问失败"
        else:
            sauce_text = await saucenao.text(res[0])
            if float(res[0]["sim"].replace("%", "")) < config.sim_to_ascii2d:
                ascii2d_text = res[1]
        url_list = [
            f"https://saucenao.com/search.php?db=999&url={i}",
            f"https://ascii2d.net/search/url/{i}",
        ]
        urls = await short_url(url_list)
        more_result = f"更多结果\n" f"sauceNao: {urls[0]}\n" f"ascii2d: {urls[1]}"
        if ascii2d_text:
            msg = (
                f"{sauce_text}" f"\n============\n" f"{ascii2d_text}\n" f"{more_result}"
            )
        else:
            msg = f"{sauce_text}\n{more_result}"
        await session.send(msg, at_sender=True)


@sv.ui_command("搜本")
async def search_eh(session: CommandSession):
    """搜本的主函数

    Args:
        session (CommandSession): bot封装的信息
    """
    image = session.get("image")
    for url in image:
        content = await ehentai.dl_src(url)
        data = await ehentai.get_search(content)
        data = await ehentai.parser(data)
        if isinstance(data, str):
            await session.send(data)
            continue
        msg = ""
        for i in data:
            msg += (
                f"标题: {i['title']}\n"
                f"类型: {i['type']}\n"
                f"页数: {i['page_count']}\n"
                f"链接: {i['link']}\n"
                f"{i['im_seq']}\n"
            )
        await session.send(msg)


async def short_url(url_list: list) -> list:
    """调用uisbox短链服务把更多结果的连接缩短

    Args:
        url_list (list): 由两个连接组成的列表

    Returns:
        list: 缩短的两个连接
    """
    if not config.short_url_apikey:
        return url_list
    url = "http://short.uisbox.com/api/v2/action/shorten"
    urls = []
    for i in url_list:
        params = {"key": config.short_url_apikey, "url": i}
        async with httpx.AsyncClient(
            proxies=config.proxies, params=params, timeout=5
        ) as client:
            s = await client.get(url)
            if s.status_code != 200:
                return url_list
            urls.append(s.text)
    return urls


@search_image.args_parser
async def _(session: CommandSession):
    """指令解析器

    Args:
        session (CommandSession): bot封装的消息
    """

    if session.current_arg_images:
        session.state["image"] = session.current_arg_images
        return

    if session.current_arg_text:
        if session.current_arg_text.strip() == "done":
            await session.finish("会话已结束")

    if not session.current_arg_images:
        await session.pause("羽衣不会读心哦,要把图片发出来才行！")


@search_eh.args_parser
async def _(session: CommandSession):
    """指令解析器

    Args:
        session (CommandSession): bot封装的消息
    """

    if session.current_arg_images:
        session.state["image"] = session.current_arg_images
        return

    if session.current_arg_text:
        if session.current_arg_text.strip() == "done":
            await session.finish("会话已结束")

    if not session.current_arg_images:
        await session.pause("羽衣不会读心哦,要把图片发出来才行！")
