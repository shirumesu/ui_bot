from aiocqhttp import message
from nonebot import on_command, CommandSession, CQHttpError, get_bot

import config
from src.Services import Service, Service_Master, perm, SUPERUSER


sv_help = """人偶功能 | 使用帮助
括号内的文字即为指令,小括号内为可选文字(是否必带请自行参照使用示例)
[发送私聊消息 (要发送的qq号) (要发送的消息)] -> 发送私聊消息给人
[发送群消息 (要发送的群号) (要发送的消息)] -> 发送群消息
[联系主人 (消息)] -> 字面意思
特别注意:
    主人问题 -> 如果有多个超级用户,将会发送配置文件中的第一个
    权限问题 -> 请确保羽衣酱有办法发送到该人/群！
    图片问题 -> 是可以发送图片过去的！请连带在**一个消息**里
"""
sv = Service(
    ["marionette", "人偶"],
    sv_help,
    permission_use=SUPERUSER,
    permission_change=SUPERUSER,
    priv_use=False,
)

bot = get_bot()


@on_command("发送私聊消息", aliases=["发送给人", "发送到人"])
async def send_pri_msg(session: CommandSession) -> None:
    """发送私聊消息给人

    Args:
        session (CommandSession): bot封装的消息
    """
    stat = await Service_Master().check_permission("marionette", session.event)
    if not stat[0]:
        if stat[3]:
            await session.finish(stat[3])
        else:
            await session.finish(
                f"你没有足够权限使用此插件,要求权限{perm[stat[2]]},你的权限:{perm[stat[1]]}"
            )
    msg = session.get("msg")
    userid = session.get("userid")
    try:
        respon = await bot.send_private_msg(user_id=userid, message=msg)
    except CQHttpError:
        stranger_info = await bot.get_stranger_info(user_id=userid)
        nickname = stranger_info["nickname"]
        await session.finish("权限不足,%s(qq:%s)不是我的好友" % (nickname, userid))
    if respon:
        await session.finish("发送成功")
    else:
        await session.finish("发送失败,可能被风控了")


@on_command("发送群消息", aliases=["发送给群", "发送到群"])
async def send_grp_msg(session: CommandSession) -> None:
    """发送群消息到群

    Args:
        session (CommandSession): bot封装的信息
    """
    stat = await Service_Master().check_permission("marionette", session.event)
    if not stat[0]:
        if stat[3]:
            await session.finish(stat[3])
        else:
            await session.finish(
                f"你没有足够权限使用此插件,要求权限{perm[stat[2]]},你的权限:{perm[stat[1]]}"
            )
    msg = session.get("msg")
    userid = session.get("grpid")
    try:
        respon = await bot.send_group_msg(user_id=userid, message=msg)
    except CQHttpError:
        await session.finish(f"发送失败,我还没有加{userid}群")
    if respon:
        await session.finish("发送成功")
    else:
        await session.finish("发送失败,可能被风控了")


@on_command("联系主人")
async def send_to_master(session: CommandSession) -> None:
    """联系主人,发送给superuser

    Args:
        session (CommandSession): bot封装的消息
    """
    msg = session.get("msg")
    respon = None
    respon = await bot.send_private_msg(user_id=config.SUPERUSERS[0], message=msg)
    if respon == None:
        await session.send("被风控了发不出去了")
    else:
        await session.send("发送成功")


@send_pri_msg.args_parser
async def _(session: CommandSession):
    """解析指令

    Args:
        session (CommandSession): bot封装的消息
    """
    strp = session.current_arg.strip()
    msg = strp.split(" ", 1)
    session.state["userid"] = msg[0]
    session.state["msg"] = msg[1]


@send_grp_msg.args_parser
async def _(session: CommandSession):
    """解析指令

    Args:
        session (CommandSession): bot封装的消息
    """
    strp = session.current_arg.strip()
    msg = strp.split(" ", 1)
    session.state["grpid"] = msg[0]
    session.state["msg"] = msg[1]


@send_to_master.args_parser
async def _(session: CommandSession):
    """解析指令

    Args:
        session (CommandSession): bot封装的消息
    """
    msg = session.current_arg.strip()
    if not msg:
        session.pause("你确定什么都不发吗?\n发送 done 结束")
    if msg == "done":
        session.finish("会话已结束")
    session.state["msg"] = msg
