import os

from aiocqhttp import Event
from nonebot.plugin import PluginManager

from nonebot import CommandSession, MessageSegment, message_preprocessor, NoneBot

from .datasource import get_text, update_photo, send_qiangdubang
from .game import Game_Master
from .uploader import updater
from .spider import Spider
from src.Services import uiPlugin

from config import proxies_for_all

sv_help = """碧蓝航线wiki | 使用帮助
括号内的文字即为指令,小括号内为可选文字(是否必带请自行参照使用示例)
[blhxwiki (舰娘/装备/特别页面)] -> 拿数据
    支持装备/舰娘,但要求全名,自定义词典正在咕咕叫
    特别页面支持以下:
        1. 强度榜(blhxwiki 强度榜)
        2. 一图榜 (使用方法同上,以下不再提)
        3. 秒伤榜 (小圣的全装备秒伤榜)
[blhxwiki 更新图片] -> 更新缓存图片
    特别注意: 请不要不停使用！累的是wiki,坏的是bot！
[猜头像 / 猜舰娘] -> 类pcr的游戏碧蓝移植版(?), 总之玩玩看?
[强制结束游戏] -> 为了防止因为bug导致游戏卡在那了, 可以强制结束一局游戏(不会发任何正确答案)
[添加舰娘别名 (公式名) (别名)] -> 添加别名！用于游戏不用非打公式名
    特别注意: 请注意别名没有歧义！比如布里是别名, 但这是禁止的, 因为可以指代各种布里, 请添加如金布里 彩布里等
[更新舰娘] -> 更新舰娘到数据库(用于猜头像|猜角色游戏)
    特别注意: 使用的是wiki的舰娘角色定位页面, 新舰船更新取决于wiki, 不一定是实时
"""
sv = uiPlugin(
    ["blhxwiki", "碧蓝航线wiki"],
    False,
    usage=sv_help,
    private_use=True,
    use_source_folder=True,
    use_cache_folder=True,
)
updater = updater()
path = os.path.join(os.getcwd(), "src", "plugins", "blhxwiki", "char_info.json")
spd = Spider(proxies_for_all, path)
GM = Game_Master(spd.config)


@sv.ui_command(
    "blhxwiki",
    aliases=["碧蓝航线wiki", "碧蓝wiki", "blhx维基", "blhx百科"],
    ignore_superuser=False,
)
async def blhxwiki(session: CommandSession):
    """blhxwiki的主函数

    Args:
        session (CommandSession): bot封装的消息
    """
    cmd = session.current_arg_text.strip()
    if cmd in updater.dicts.keys():
        res = await updater.get_image(cmd)
        if not res:
            text = "\n".join([x for x, y in updater.dicts.items() if y])
            await session.finish(
                f"没有找到对应榜单!目前有的榜单为:\n{text}\nps:如果确实存在该榜单依然发了这条信息请使用`blhxwiki 更新图片`进行更新"
            )
        images = [str(MessageSegment.image("file:///" + x)) for x in res]
        info = "".join(images)
    elif cmd == "更新图片":
        await session.send("正在尝试更新……因为要下载10+张图,可能会很久……")
        info = await updater.update_allinfo()
    else:
        await session.send("正在尝试获取……")
        info = await get_text(cmd)
    await session.finish(info)


@sv.ui_command("猜头像", patterns=r"^猜(舰娘|头像)$")
async def guess_game(session: CommandSession):
    """猜头像/猜舰娘的游戏！

    Args:
        session (CommandSession): bot封装的信息
    """
    cmd = session.current_arg_text.strip()
    if cmd == "猜头像":
        await GM.start_game(session, "avatar")
    elif cmd == "猜舰娘":
        await GM.start_game(session, "info")
    else:
        try:
            if session.cmd.name[0] == "猜头像":
                await GM.start_game(session, "avatar")
        except:
            pass


@sv.ui_command("强制结束游戏")
async def guess_game(session: CommandSession):
    """猜头像/猜舰娘的游戏！

    Args:
        session (CommandSession): bot封装的信息
    """
    gid = session.event.group_id
    game = await GM.get_game(gid)
    if game:
        game.winner = "123"
        GM.end_game(gid)
        await session.finish("本群的游戏已结束")


@message_preprocessor
async def _(bot: NoneBot, event: Event, plugin_manager: PluginManager):
    game = await GM.get_game(event.group_id)
    if not game:
        return
    try:
        game.ansing = True
        if await game.bingo(event.raw_message):
            game.winner = event.sender
            await bot.send_group_msg(
                message=f"恭喜你答对了!\n正确答案: {game.ans[0]}\n{game.message_image}",
                group_id=event.group_id,
            )
            game.ansing = False
            GM.end_game(event.group_id)
    except:
        pass


@sv.ui_command("添加舰娘别名")
async def guess_game(session: CommandSession):
    """更新舰娘到数据库

    Args:
        session (CommandSession): bot封装的信息
    """
    name = session.current_arg_text.strip().split(" ")
    for i in spd.config.values():
        if name[0] in i["name"]:
            if name[1] in i["name"]:
                await session.finish("已经存在该别名了!")
            else:
                i["name"].append(name[1])
                spd.dump()
                await session.finish("成功添加该别名!")
        else:
            continue

    await session.finish("没有找到该舰娘!")


@sv.ui_command("更新舰娘")
async def guess_game(session: CommandSession):
    """更新舰娘到数据库

    Args:
        session (CommandSession): bot封装的信息
    """
    new_list = await spd.get_info()

    if not new_list:
        await session.finish("没有发现舰娘更新!")
    else:
        text = "，".join(new_list)
        await session.finish(f"成功更新以下舰娘!:\n{text}")
