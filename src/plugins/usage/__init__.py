from loguru import logger

from nonebot import on_command, CommandSession
from aiocqhttp import MessageSegment

import config as cfg
from src.Services import Service_Master, Service, GROUP_ADMIN, perm


sv_help = """使用帮助 |使用帮助
括号内的文字即为指令,小括号内为可选文字(是否必带请自行参照使用示例)
[使用帮助 (插件名)] -> 获取插件的使用帮助
    特别注意:
        插件名并非必带,不带插件名就会发这个使用帮助
        插件名可以是中文也可以是括号内的英文
        如果是第一次使用,可以发送详细使用帮助获取超级完整的使用帮助(包含所有插件)
题外话:
    诶…真的有人连使用帮助怎么用都要使用帮助吗？这也太好笑了吧
    诶？！先辈？原来需要的人就是你啊…诶……？开玩笑的吧,好好笑
    噗…别再逗羽衣笑了啦……噗…gu……
    不过话说回来啊,你真的不会吗？诶？真的？没在开玩笑？诶……噗…(捂嘴)
""".strip()
all_help = """详细使用帮助
咕了
""".strip()
sv = Service(['usage', '使用帮助'], sv_help, permission_change=GROUP_ADMIN)
svm = Service_Master()


@on_command('使用帮助', aliases=('帮助', 'help'))
async def usage(session: CommandSession):
    """发送使用帮助

    如果没有接收到，发送sv_help
    收到了则对应发送usage

    Args:
        session: bot封装的信息
    """
    stat = await Service_Master().check_permission('usage', session.event)
    if not stat[0]:
        if stat[3]:
            await session.finish(stat[3])
        else:
            await session.finish(f'你没有足够权限使用此插件,要求权限{perm[stat[2]]},你的权限:{perm[stat[1]]}')
    com = session.current_arg_text.strip()
    if not com:
        msg = sv_help
    elif com in svm.sv_list:
        plugin = svm.sv_list[com]
        msg = plugin.usage
    else:
        found = False
        for x, y in svm.sv_list.items():
            if com in y.plugin_name:
                msg = y.usage
                found = True
                break
        if not found:
            msg = '没有找到该插件,可以发送使用帮助获取使用帮助'
    await session.send(msg)


@on_command('详细使用帮助')
async def usage_all(session: CommandSession):
    """同上

    发送all_help
    本意为给第一次使用稽器人想知道全部功能的人使用

    Args:
        session: bot封装的信息
    """
    stat = await Service_Master().check_permission('usage', session.event)
    if not stat[0]:
        if stat[3]:
            await session.finish(stat[3])
        else:
            await session.finish(f'你没有足够权限使用此插件,要求权限{perm[stat[2]]},你的权限:{perm[stat[1]]}')
    await session.send(all_help)
