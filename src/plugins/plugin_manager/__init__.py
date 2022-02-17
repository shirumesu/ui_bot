from nonebot import get_bot
from nonebot.command import CommandSession

from config import bot_name
from src.Services import uiPlugin, uiPlugin_Master, SUPERUSER, GROUP_ADMIN


bot = get_bot()
sv_help = f"""插件管理器 | 使用帮助
括号内的文字即为指令,小括号内为可选文字(是否必带请自行参照使用示例)
**请不要关闭此插件或是将插件放入黑名单 否则需要改配置文件解除黑名单**
[查看插件列表] -> 获取所有插件,包括未启用的
    特别注意:
        由于存在介乎于功能与插件之间的插件,并非所有插件都会显示
        {bot_name}的管理员可以透过私聊使用此功能获取完整的插件列表
[插件管理 (管理类型) (插件名)] -> 对某插件操控
    管理类型:
        1.全局开启
        2.全局关闭
        3.拉黑本群
        4.本群白名单
        5.允许私聊
        6.禁止私聊
        7.拉黑用户
        8.用户白名单
    插件名：
        插件的中文名或是英文都行
    示例:
        插件管理 全局开启 色图
[全功能开启/全功能禁止] -> 对该群关闭所有插件
    特别注意:
        使用权限: 仅为superuser
"""
sv = uiPlugin(
    ["plugin_manager", "插件管理器"],
    False,
    usage=sv_help,
    perm_use=GROUP_ADMIN,
    perm_manager=SUPERUSER,
)
svm = uiPlugin_Master()


@sv.ui_command("查看插件列表", aliases=("查看所有插件"))
async def plugin_list(session: CommandSession):
    """发送所有插件列表

    具体请参照上方的sv_help 会更加详细

    Args:
        session: bot封装的信息
    """
    gid = session.event.group_id if session.event.detail_type == "group" else 0
    plugins = svm.match_plugin()
    enable_plugins = []
    disable_plugins = []
    for plugin in plugins:
        enable_plugins.append(f"{plugin.name_cn}({plugin.name_en})") if str(
            gid
        ) in plugin.enable_group else disable_plugins.append(
            f"{plugin.name_cn}({plugin.name_en})"
        )
    msg = "=====可以发送使用帮助获取使用帮助=====\n=====正在使用的插件！=====\n"
    msg += "\n".join(enable_plugins)
    msg += "\n=====没有使用的插件!=====\n"
    msg += "\n".join(disable_plugins)
    await session.send(msg)


@sv.ui_command("注册群", plugin_manager=True)
async def regis_grouper(session):
    if session.event.detail_type != "group":
        await session.finish("仅支持群！")
    gid = session.event.group_id
    group_type = session.current_arg.strip()
    msg = svm.regis_group(gid, group_type)
    await session.finish(f"以下插件已成功开启:\n" + "\n".join(msg))


@sv.ui_command("插件管理", plugin_manager=True)
async def load_plugin(session):
    """开启插件

    Args:
        session: bot封装的信息
    """
    type_table = {
        "全局开启": ["enable", True],
        "全局关闭": ["enable", False],
        "拉黑本群": ["group", False],
        "本群白名单": ["group", True],
        "允许私聊": ["disable_private", True],
        "禁止私聊": ["disable_private", False],
        "拉黑用户": ["private", False],
        "用户白名单": ["private", True],
    }
    uid = session.event.user_id
    gid = session.event.group_id if session.event.detail_type == "group" else -1
    switch_type = type_table[session.current_arg.strip().split()[0]]
    plugin_name = session.current_arg.strip().split()[1]
    plugins = svm.match_plugin(plugin_name)
    if not plugins:
        await session.finish("未找到插件名字！请重新输入")
    if switch_type[0] == "enable":
        msg = svm.switch_all(switch_type[1], plugin_name)
    else:
        msg = svm.block_all(switch_type[0], uid, gid, switch_type[1], plugin_name)
    msg = "\n".join([f"{x}: {y}" for x, y in msg.items()])
    await session.send(msg)


@sv.ui_command("全功能禁止", aliases=("全功能关闭",), plugin_manager=True)
async def shut_all(session: CommandSession):
    if session.event.detail_type != "group":
        await session.finish("仅支持在群聊使用！")
    msg = svm.block_all("group", session.event.user_id, session.event.group_id, False)
    msg = (
        "成功！以下插件已更改: \n"
        "\n".join([f"{plugin}: {text}" for plugin, text in msg.items()])
        + "(已经订阅的p站,推特会继续推送,想禁止请取消订阅/使用`闭嘴`命令)"
    )
    await session.send(msg)


@sv.ui_command("全功能开启", aliases=("全功能启用",))
async def enable_all(session: CommandSession):
    if session.event.detail_type != "group":
        await session.finish("仅支持在群聊使用！")
    msg = svm.block_all("group", session.event.user_id, session.event.group_id, True)
    msg = (
        "成功！以下插件已更改: \n"
        "\n".join([f"{plugin}: {text}" for plugin, text in msg.items()])
        + "(已经订阅的p站,推特会继续推送,想禁止请取消订阅/使用`闭嘴`命令)"
    )
    await session.send(msg)
