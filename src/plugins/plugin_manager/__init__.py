import os
import json
from re import T
from loguru import logger

from nonebot import on_command, get_bot
from nonebot import plugin
from nonebot.plugin import PluginManager
from nonebot.command import CommandSession

import config
from src.Services import (
    GROUP_MEMBER,
    SUPERUSER,
    Service,
    GROUP_ADMIN,
    Service_Master,
    ALL_SERVICES,
    perm,
)


bot = get_bot()
sv_help = """插件管理器 | 使用帮助
括号内的文字即为指令,小括号内为可选文字(是否必带请自行参照使用示例)
**请不要关闭此插件或是将插件放入黑名单 否则需要改配置文件解除黑名单**
[查看插件列表] -> 获取所有插件,包括未启用的
    特别注意:
        由于存在介乎于功能与插件之间的插件,并非所有插件都会显示
        羽衣的管理员可以透过私聊使用此功能获取完整的插件列表
[(开启|关闭)插件 插件名] -> 在本群/私聊开启/关闭插件
    参数详解:
        插件名 -> 要求为插件的英文名(文件名)(也就是插件列表中括号内的文字)
    特别注意:
        一般插件权限要求:管理员以上
        在群中或私聊开启一个关闭的插件都会让插件全局启动
        此功能与其说是开启关闭,实际上是白名单黑名单的修改
    使用示例:
        开启插件 setu
        关闭插件 setu
[全局(开启|关闭)插件 插件名] -> 全局加载/删除一个插件
    参数详解:
        插件名 -> 同上
    特别注意:
        一般插件权限要求:超级用户
        此功能将会全局关闭或加载插件
    使用示例:
        全局关闭插件 setu
        全局开启插件 setu
"""
sv = Service(
    ["plugin_manager", "插件管理器"],
    sv_help,
    permission_change=SUPERUSER,
    permission_use=GROUP_ADMIN,
    visible=False,
)
svm = Service_Master()


@on_command("查看插件列表", aliases=("查看所有插件"))
async def plugin_list(session: CommandSession):
    """发送所有插件列表

    具体请参照上方的sv_help 会更加详细

    Args:
        session: bot封装的信息
    """
    try:
        stat = await svm.check_permission("plugin_manager", session.event, GROUP_MEMBER)
    except Exception:
        stat = [True, "", "", ""]
    if not stat[0]:
        if stat[3]:
            await session.finish(stat[3])
    enable_list = []
    disable_list = []
    if (
        session.event["user_id"] in config.SUPERUSERS
        and session.event["message_type"] == "private"
    ):
        plugins_namelist = [y.plugin_name for x, y in svm.sv_list.items()]
        msg = "所有插件:\n"
        for i in plugins_namelist:
            msg += f"{i[1]}({i[0]})\n"
    elif session.event["message_type"] == "group":
        for y in svm.sv_list.values():
            if not y.visible:
                continue
            perm = await svm.check_permission(
                y.plugin_name[0], session.event, disable_superuser=True
            )
            if perm[0]:
                enable_list.append(y.plugin_name)
            else:
                disable_list.append(y.plugin_name)
        msg = "=====可以发送使用帮助获取使用帮助=====\n=====正在使用的插件！=====\n"
        for i in enable_list:
            msg += f"{i[1]}({i[0]})\n"
        msg += "=====没有使用的插件!=====\n"
        for i in disable_list:
            msg += f"{i[1]}({i[0]})\n"
    else:
        for x, y in svm.sv_list.items():
            if not y.visible or y.priv_use:
                continue
            else:
                perm = await svm.check_permission(y.plugin_name[0], session.event)
                if perm[0]:
                    enable_list.append(y.plugin_name)
        msg = "你可以使用的插件有:\n"
        for i in enable_list:
            msg += f"{i[1]}({i[0]})\n"
    await session.send(msg.strip())


@on_command("开启插件")
async def load_plugin(session):
    """开启插件

    Args:
        session: bot封装的信息
    """
    stat = await svm.check_permission("plugin_manager", session.event, "upm")
    if not stat[0]:
        if stat[3]:
            await session.finish(stat[3])
    plugin_name = session.current_arg.strip()
    plugin_name = [x for x, y in svm.sv_list.items() if plugin_name in y.plugin_name]
    if not plugin_name:
        session.finish("未找到插件名字！请重新输入")
    else:
        plugin_name = plugin_name[0]
        if session.event.detail_type == "group":
            gid = session.event["group_id"]
            uid = None
        else:
            gid = None
            uid = session.event["user_id"]
        stat = await svm.enable_plugin(plugin_name, True, gid, uid)
    if stat:
        await session.send("开启成功！")
    else:
        await session.send("开启失败,出现未知错误")


@on_command("关闭插件")
async def end_plugin(session):
    """关闭插件

    Args:
        session: bot封装的信息
    """
    stat = await svm.check_permission("plugin_manager", session.event, "upm")
    if not stat[0]:
        if stat[3]:
            await session.finish(stat[3])
    plugin_name = session.current_arg.strip()
    plugin_name = [x for x, y in svm.sv_list.items() if plugin_name in y.plugin_name]
    if not plugin_name:
        session.finish("未找到插件名字！请重新输入")
    else:
        plugin_name = plugin_name[0]
        if session.event.detail_type == "group":
            gid = session.event["group_id"]
            uid = None
        else:
            gid = None
            uid = session.event["user_id"]
        stat = await svm.enable_plugin(plugin_name, False, gid, uid)
    if stat:
        await session.send("关闭成功！")
    else:
        await session.send("关闭失败,出现未知错误")


@on_command("全局关闭插件")
async def disable_plugin(session):
    """关闭插件

    具体是设置插件sv的is_enable属性

    Args:
        session: bot封装的信息
    """
    stat = await svm.check_permission("plugin_manager", session.event, SUPERUSER)
    if not stat[0]:
        if stat[3]:
            await session.finish(stat[3])
        else:
            await session.finish(
                f"你没有足够权限使用此插件,要求权限{perm[stat[2]]},你的权限:{perm[stat[1]]}"
            )
    plugin_name = session.current_arg.strip()
    plugin_name = [x for x, y in svm.sv_list.items() if plugin_name in y.plugin_name]
    if not plugin_name:
        session.finish("未找到插件名字！请重新输入")
    else:
        plugin_name = plugin_name[0]
        stat = await svm.switch_plugin_global(plugin_name, False)
    if stat:
        await session.send("关闭成功！")
    else:
        await session.send("关闭失败,出现未知错误")


@on_command("全局开启插件")
async def enable_plugin(session):
    """开启插件

    具体是设置插件sv的is_enable属性

    Args:
        session: bot封装的信息
    """
    stat = await svm.check_permission("plugin_manager", session.event, SUPERUSER)
    if not stat[0]:
        if stat[3]:
            await session.finish(stat[3])
        else:
            await session.finish(
                f"你没有足够权限使用此插件,要求权限{perm[stat[2]]},你的权限:{perm[stat[1]]}"
            )
    plugin_name = session.current_arg.strip()
    plugin_name = [x for x, y in svm.sv_list.items() if plugin_name in y.plugin_name]
    if not plugin_name:
        session.finish("未找到插件名字！请重新输入")
    else:
        plugin_name = plugin_name[0]
        stat = await svm.switch_plugin_global(plugin_name, True)
    if stat:
        await session.send("开启成功！")
    else:
        await session.send("开启失败,出现未知错误")
