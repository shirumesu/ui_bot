import os
import re
import ujson
import base64
import httpx
import asyncio
import string
import random
from PIL import Image
from io import BytesIO
from html import unescape
from retrying import retry
from bs4 import BeautifulSoup
from feedparser import parse
from hashlib import md5
from loguru import logger

from nonebot import CommandSession, scheduler, MessageSegment, get_bot

import config
from src.Services import uiPlugin, GROUP_ADMIN, SUPERUSER
from src.shared import shutup

bot_name = config.bot_name
sv_help = f"""RssHub订阅 | 使用帮助
括号内的文字即为指令,小括号内为可选文字(是否必带请自行参照使用示例)
[订阅rss (rss链接)] -> 订阅Rss
    参数详解:
        rss链接:
            -> 请参照官方指南https://docs.rsshub.app/
            -> 然后回复{bot_name}示例链接 例如:https://rsshub.app/bilibili/bangumi/media/9192
            -> 请注意示例链接旁边的图标status是否为up,如果为down代表失效,无法获取
            -> 会5/30分钟更新一次(与使用自建rss或是官方demo有关,官方demo30分钟更新一次,直接回复官方demo示例即可,如果有使用自建会自动替换链接)
    特别注意:
        失效链接 -> 如果有链接连续5次以上访问失败(超时/返回格式不正确/或是404等),会自动删除
        其他订阅 -> Pixiv,Twitter,pcr新闻建议使用订阅pixiv,订阅推特,yobot进行订阅而非RSS
        风控问题 -> 某些订阅源的详细内容过多,可能导致bot被风控因此发送了非详细推送,此为正常情况,目前已知但不限于大概率无法详细推送的rss源包括: 观察者网头条
    使用示例:
        订阅rss https://rsshub.app/bilibili/bangumi/media/9192
        -> 是否需要详细推送?(会额外多出更新时间以及内容全文/摘要(取决于Rss))
           (回复y/n)
        y
        -> 订阅成功
[查看rss订阅] -> 查看本群/私聊订阅的所有rss源
[设置rss] -> 设置是否需要全文推送(依照指示来输入就好)
[删除rss] -> 删除rss订阅 同样,会有指示说明的
""".strip()
sv = uiPlugin(
    ["rsshub", "订阅RssHub"],
    True,
    usage=sv_help,
    use_cache_folder=True,
    perm_use=GROUP_ADMIN,
    perm_manager=SUPERUSER,
)

bot = get_bot()


subc_path = os.path.join(os.getcwd(), "src", "plugins", "rsshub", "subcribe.json")
if os.path.exists(subc_path):
    with open(subc_path, "r", encoding="utf-8") as f:
        subcribe = ujson.load(f)
else:
    with open(subc_path, "w", encoding="utf-8") as f:
        subcribe = {}
        ujson.dump(subcribe, f, ensure_ascii=False, indent=4)


class DelError(Exception):
    pass


@sv.ui_command("订阅rss")
async def subc_rss(session: CommandSession):
    """订阅rsshub的主函数

    Args:
        session (CommandSession): bot封装的信息
    """
    rss_link = session.current_arg_text.strip()
    if (
        "twitter" in rss_link
        or "pixiv" in rss_link
        or "fanbox" in rss_link
        or "pcr" in rss_link
    ):
        await session.finish("请参照使用说明,使用另外的插件订阅")
    if not re.match(r"https://rsshub.app/[\d\w/]*", rss_link):
        await session.finish("请检查是否使用了有效的链接,具体请参照使用说明")

    if config.use_self_Rss:
        rss_link = rss_link.replace("https://rsshub.app", config.Rss_route)

    if session.event.detail_type == "group":
        gid = session.event.group_id
        uid = None
        if rss_link in subcribe and gid in subcribe[rss_link]["subcribe_group"]:
            await session.finish("本群已经订阅过了")
    else:
        uid = session.event.user_id
        gid = None
        if rss_link in subcribe and uid in subcribe[rss_link]["subcribe_user"]:
            await session.finish("本群已经订阅过了")

    await session.apause("是否需要详细推送?(会额外多出更新时间以及内容全文/摘要(取决于Rss))\n(回复y/n)")
    full_text = session.current_arg_text.strip()
    if full_text not in ["n", "y"]:
        await session.finish("错误输入,请重新使用此功能")
    full_text = True if full_text == "y" else False

    await add_config(rss_link, full_text, gid, uid)
    try:
        await update_hash(rss_link)
    except:
        await session.finish("链接超过三次无法访问,判断为无效连接,已删除订阅")
    await session.finish("订阅成功")


@sv.ui_command("查看rss订阅")
async def check_subc(session: CommandSession):
    """查看rss订阅的主函数

    Args:
        session (CommandSession): bot封装的信息
    """
    if session.event.detail_type == "group":
        gid = str(session.event.group_id)
        name_list = [
            y["name"] for x, y in subcribe.items() if gid in y["subcribe_group"]
        ]
        status_list = [
            y["subcribe_group"][gid]
            for x, y in subcribe.items()
            if gid in y["subcribe_group"]
        ]
        if not name_list:
            await session.finish("本群还没有订阅任何rss！")
        msg = "本群订阅了以下rss:\n"
        for name, status, index in zip(
            name_list, status_list, [x for x in range(len(name_list))]
        ):
            msg += f"{index + 1}: {name} -> {'[√]详细订阅' if status else '[×]详细订阅'}\n"

    elif session.event.detail_type == "private":
        uid = str(session.event.user_id)
        name_list = [
            x["name"] for y, x in subcribe.items() if uid in x["subcribe_user"]
        ]
        status_list = [
            x["subcribe_user"][uid]
            for y, x in subcribe.items()
            if uid in x["subcribe_user"]
        ]
        if not name_list:
            await session.finish("本群还没有订阅任何rss！")
        msg = "你订阅了以下rss:\n"
        for name, status, index in zip(
            name_list, status_list, [x for x in range(len(name_list))]
        ):
            msg += f"{index + 1}: {name} -> {'[√]详细订阅' if status else '[×]详细订阅'}\n"

    else:
        await session.finish("目前仅支持在群聊/私聊使用该功能")

    await session.finish(msg)


@sv.ui_command("删除rss")
async def del_rss(session: CommandSession):
    """删除rss的函数

    Args:
        session (CommandSession): bot封装的信息
    """
    if session.event.detail_type == "group":
        gid = str(session.event.group_id)
        name_list = [
            x["name"] for y, x in subcribe.items() if gid in x["subcribe_group"]
        ]
        status_list = [
            x["subcribe_group"][gid]
            for y, x in subcribe.items()
            if gid in x["subcribe_group"]
        ]
        if not name_list:
            await session.finish("本群还没有订阅任何rss！")
        msg = "本群订阅了以下rss:\n"
        for name, status, index in zip(name_list, status_list, range(len(name_list))):
            msg += f"{index + 1}: {name} -> {'[√]详细订阅' if status else '[×]详细订阅'}\n"
        msg = msg.strip() + "\n输入数字进行设置反转"
        uid = None

    elif session.event.detail_type == "private":
        uid = str(session.event.user_id)
        name_list = [
            x["name"] for y, x in subcribe.items() if uid in x["subcribe_user"]
        ]
        status_list = [
            x["subcribe_user"][uid]
            for y, x in subcribe.items()
            if uid in x["subcribe_user"]
        ]
        if not name_list:
            await session.finish("本群还没有订阅任何rss！")
        msg = "你订阅了以下rss:\n"
        for name, status, index in zip(name_list, status_list, range(len(name_list))):
            msg += f"{index + 1}: {name} -> {'[√]详细订阅' if status else '[×]详细订阅'}\n"
        msg = msg.strip() + "\n输入数字进行删除"
        gid = None

    else:
        await session.finish("目前仅支持在群聊/私聊使用该功能")

    await session.apause(msg)

    if not re.match(r"\d+", session.current_arg_text.strip()) and int(
        session.current_arg_text.strip()
    ) <= len(name_list):
        await session.finish("输入错误")

    index = int(session.current_arg_text.strip()) - 1
    name = name_list[index]
    for x, y in subcribe.items():
        if gid:
            if gid in y["subcribe_group"] and y["name"] == name:
                y["subcribe_group"].remove(gid)
        else:
            if uid in y["subcribe_user"] and y["name"] == name:
                y["subcribe_user"].remove(uid)

    with open(subc_path, "w", encoding="utf-8") as f:
        ujson.dump(subcribe, f, ensure_ascii=False, indent=4)

    await session.finish("删除成功！")


@sv.ui_command("设置rss")
async def set_subc(session: CommandSession):
    """设置rss的主函数

    Args:
        session (CommandSession): bot封装的信息
    """
    if session.event.detail_type == "group":
        gid = str(session.event.group_id)
        name_list = [
            x["name"] for y, x in subcribe.items() if gid in x["subcribe_group"]
        ]
        status_list = [
            x["subcribe_group"][gid]
            for y, x in subcribe.items()
            if gid in x["subcribe_group"]
        ]
        if not name_list:
            await session.finish("本群还没有订阅任何rss！")
        msg = "本群订阅了以下rss:\n"
        for name, status, index in zip(name_list, status_list, range(len(name_list))):
            msg += f"{index + 1}: {name} -> {'[√]详细订阅' if status else '[×]详细订阅'}\n"
        msg = msg.strip() + "\n输入数字进行设置反转"
        uid = None

    elif session.event.detail_type == "private":
        uid = str(session.event.user_id)
        name_list = [
            x["name"] for y, x in subcribe.items() if uid in x["subcribe_user"]
        ]
        status_list = [
            x["subcribe_user"][uid]
            for y, x in subcribe.items()
            if uid in x["subcribe_user"]
        ]
        if not name_list:
            await session.finish("本群还没有订阅任何rss！")
        msg = "你订阅了以下rss:\n"
        for name, status, index in zip(name_list, status_list, range(len(name_list))):
            msg += f"{index + 1}: {name} -> {'[√]详细订阅' if status else '[×]详细订阅'}\n"
        msg = msg.strip() + "\n输入数字进行设置反转"
        gid = None

    else:
        await session.finish("目前仅支持在群聊/私聊使用该功能")

    await session.apause(msg)

    if not re.match(r"\d+", session.current_arg_text.strip()) and int(
        session.current_arg_text.strip()
    ) <= len(name_list):
        await session.finish("输入错误")

    index = int(session.current_arg_text.strip()) - 1
    name = name_list[index]
    for x, y in subcribe.items():
        if gid:
            if gid in y["subcribe_group"] and y["name"] == name:
                y["subcribe_group"][gid] = not status_list[index]
        else:
            if uid in y["subcribe_user"] and y["name"] == name:
                y["subcribe_user"][uid] = not status_list[index]

    with open(subc_path, "w", encoding="utf-8") as f:
        ujson.dump(subcribe, f, ensure_ascii=False, indent=4)

    await session.finish("修改成功！")


async def add_config(
    link: str, full_text: bool = False, gid: int = None, uid: int = None
):
    """保存传入的链接

    Args:
        link (str): 链接
        full_text (bool): 是否推送全文
        gid (int): 群号
        uid (int): qq号,与群号二选一传入
    """
    if link in subcribe:
        if gid:
            subcribe[link]["subcribe_group"][gid] = full_text
        else:
            subcribe[link]["subcribe_user"][uid] = full_text
    else:
        if gid:
            subcribe[link] = {
                "subcribe_group": {gid: full_text},
                "subcribe_user": {},
                "error_times": 0,
                "hash_cacha": [],
            }
        else:
            subcribe[link] = {
                "subcribe_group": {},
                "subcribe_user": {uid: full_text},
                "error_times": 0,
                "hash_cacha": [],
            }
    with open(subc_path, "w", encoding="utf-8") as f:
        ujson.dump(subcribe, f, ensure_ascii=False, indent=4)


@retry(stop_max_attempt_number=5)
async def update_hash(link: str):
    """更新缓存哈希值缓存

    Args:
        link (str): 需要更新的键
    """
    if link not in subcribe:
        return
    js = parse(link + "?mode=fulltext")
    if js["status"] != 200:
        subcribe[link]["error_times"] += 1
        if subcribe[link]["error_times"] >= 5:
            del subcribe[link]
            raise DelError
        raise RuntimeError
    else:
        md5_list = [md5(str(x).encode("utf-8")).hexdigest() for x in js["entries"]]
        subcribe[link]["hash_cacha"] = md5_list
        subcribe[link]["name"] = js["feed"]["title"]
    subcribe[link]["error_times"] = 0


async def check_update(link):
    """检查订阅的主函数

    会自动解析base64加密的图片或是url
    然后下载并且替换内容
    最后推送到群/私聊
    """

    js = parse(link + "?mode=fulltext")
    if js["status"] != 200:
        subcribe[link]["error_times"] += 1
        raise RuntimeError
    news_list = [
        x
        for x in js["entries"]
        if md5(str(x).encode("utf-8")).hexdigest() not in subcribe[link]["hash_cacha"]
    ]
    if not news_list:
        return link
    logger.info(f"发现RSS源:{link}更新,一共{len(news_list)}条")
    for item in news_list:
        title = item["title"]
        page_link = item["link"]
        update_time = item["published"]
        descrip = unescape(item["summary"])
        b64_image = [x for x in re.findall(r'(<img .*?src="data:image/.*?>)', descrip)]
        url_image = [
            x
            for x in re.findall(
                r'(<img .*?src="(?:http[s]://[0-9a-zA-Z-./]*.(?:png|jpg)).*?>)', descrip
            )
        ]
        urls = [
            x for x in re.findall(r"(http[s]://[0-9a-zA-Z-./]*.(?:png|jpg))", descrip)
        ]
        if urls:
            for x, y in zip(url_image, urls):
                descrip = descrip.replace(x, f"图片加载失败了切噜噜…{y}")
            coros = [dl_image(x) for x in urls]
            result = await asyncio.gather(*coros, return_exceptions=True)
            for index, i in enumerate(result):
                if isinstance(i, Exception):
                    logger.error("尝试下载rss中的图片失败")
                    continue
                path = r"file:///" + i
                seq = MessageSegment.image(path)
                descrip = descrip.replace("图片加载失败了切噜噜…" + urls[index], str(seq))
        if b64_image:
            for x, y in enumerate(b64_image):
                descrip = descrip.replace(y, f"没有被加载的图片君{x + 1}号")
            coro = [process_b64(x) for x in b64_image]
            res = await asyncio.gather(*coro, return_exceptions=True)
            for index, i in enumerate(res):
                if isinstance(i, Exception):
                    logger.error("尝试解析rss中的base64图片失败")
                    continue
                path = r"file:///" + i
                seq = MessageSegment.image(path)
                descrip = descrip.replace(f"没有被加载的图片君{index + 1}号", str(seq))
        descrip = re.sub(r"<(\S*?)[^>]*>.*?|<.*? />", "", descrip)

        text = f"""
{js['feed']['title']}更新:
更新时间: {update_time}
标题: {title}
页面链接: {page_link}
        """.strip()
        fulltext = f"""
{js['feed']['title']}更新:
更新时间: {update_time}
标题: {title}
内容:
{descrip.strip()}
页面链接: {page_link}
        """.strip()
        if subcribe[link]["subcribe_group"]:
            for gid, full_text in subcribe[link]["subcribe_group"].items():
                try:
                    if not gid or (gid in shutup and not shutup[gid][0]):
                        break
                    if full_text:
                        try:
                            await bot.send_group_msg(group_id=gid, message=fulltext)
                        except:
                            await bot.send_group_msg(group_id=gid, message=text)
                    else:
                        await bot.send_group_msg(group_id=gid, message=text)
                except:
                    continue
        if subcribe[link]["subcribe_user"]:
            for uid, full_text in subcribe[link]["subcribe_user"].items():
                try:
                    if not uid:
                        break
                    if full_text:
                        try:
                            await bot.send_private_msg(user_id=uid, message=fulltext)
                        except:
                            await bot.send_private_msg(user_id=uid, message=text)
                    else:
                        await bot.send_private_msg(user_id=uid, message=text)
                except:
                    continue
    return link


async def process_b64(b64_encode: str) -> str:
    """将rss返回的图片中使用b64加密而非url链接的图片解密并保存

    Args:
        b64_encode (str): b64加密文本

    Returns:
        str: 保存路径
    """
    soup = BeautifulSoup(b64_encode, "lxml")
    src = soup.find("img").get("src")

    code = re.findall(r"data:image/(png|jpg|jpeg);base(\d+),.*?", src)

    b64_encode = re.sub(r"data:image/(jpeg|png|jpg)?;base\d+,", "", src)

    if code[0][1] == "85":
        b64_decode = base64.b85decode(b64_encode)
    elif code[0][1] == "64":
        b64_decode = base64.b64decode(b64_encode)
    elif code[0][1] == "32":
        b64_decode = base64.b32decode(b64_encode)
    elif code[0][1] == "16":
        b64_decode = base64.b16decode(b64_encode)

    image = BytesIO(b64_decode)
    image = Image.open(image)

    file_name = "".join(random.sample(string.ascii_letters + string.digits, 8)) + ".png"
    save_path = os.path.join(config.res, "cacha", "rsshub", file_name)

    image.save(save_path)

    return save_path


@retry(stop_max_attempt_number=3)
async def dl_image(image_url: str) -> str:
    """下载图片

    Args:
        image_url(str): 图片链接

    Returns:
        str: 保存到的链接地址
    """
    async with httpx.AsyncClient(proxies=config.proxies, timeout=15) as s:
        res = await s.get(image_url)
        if res.status_code != 200:
            raise RuntimeError
    file_name = "".join(random.sample(string.ascii_letters + string.digits, 8)) + ".png"
    save_path = os.path.join(config.res, "cacha", "rsshub", file_name)
    with open(save_path, "wb") as f:
        f.write(res.content)
    return save_path


@scheduler.scheduled_job(
    "interval",
    minutes=1,
    # seconds=10,
)
async def check_multi_rss():
    logger.info("检查RSS订阅")
    coros = [check_update(x) for x in subcribe.keys()]
    res = await asyncio.gather(*coros, return_exceptions=True)
    for url, i in zip([x for x in subcribe.keys()], res):
        if isinstance(i, Exception):
            logger.error(
                f"检查RSS订阅源{url}失败,连续失败次数:{subcribe[url]['error_times'] + 1},错误信息:{i}"
            )
            if subcribe[url]["error_times"] >= 5:
                del subcribe[url]
            continue
        await update_hash(i)
    with open(subc_path, "w", encoding="utf-8") as f:
        ujson.dump(subcribe, f, ensure_ascii=False, indent=4)
    logger.info("检查完毕")
