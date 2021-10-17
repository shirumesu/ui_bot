from nonebot import CommandSession

from src.Services import uiPlugin, uiPlugin_Master


sv_help = """使用帮助 |使用帮助
括号内的文字即为指令,小括号内为可选文字(是否必带请自行参照使用示例)
[查看所有插件] -> 查看所有可用的插件
[使用帮助 (插件名)] -> 获取插件的使用帮助
    特别注意:
        插件名并非必带,不带插件名就会发这个使用帮助
        插件名可以是中文也可以是括号内的英文
        如果是第一次使用,可以发送详细使用帮助获取超级完整的使用帮助(包含所有插件)
备注:
    某些插件需要bot管理员才能开启插件,这些插件大多包含r18内容,想开启请使用联系主人详细说明(我可不想突然bot没了)
    目前可以被管理员控制的插件:
    1. 群空调
    2. blhxwiki
    3. 切噜语翻译
    4. 表情制作
    5. pixiv
    6. 插件管理
    7. 自定义回复
    8. 订阅rss
    9. 订阅推特
    10. 订阅pixiv
    三个订阅都放出来了,希望别乱订阅r18,确保群没有内鬼
    11. 俄罗斯轮盘
    12. 使用帮助(是的 你甚至可以关闭使用帮助)
    仅限超级用户开关的插件:
    1. 色图(严重r18)
题外话:
    诶…真的有人连使用帮助怎么用都要使用帮助吗？这也太好笑了吧
    诶？！先辈？原来需要的人就是你啊…诶……？开玩笑的吧,好好笑
    噗…别再逗羽衣笑了啦……噗…gu……
    不过话说回来啊,你真的不会吗？诶？真的？没在开玩笑？诶……噗…(捂嘴)
""".strip()
all_help = """详细使用帮助
咕了
""".strip()
sv = uiPlugin(["usage", "使用帮助"], False, usage=sv_help)
svm = uiPlugin_Master()


@sv.ui_command("使用帮助", aliases=("帮助", "help"))
async def usage(session: CommandSession):
    """发送使用帮助

    如果没有接收到，发送sv_help
    收到了则对应发送usage

    Args:
        session: bot封装的信息
    """
    com = session.current_arg_text.strip()
    if not com:
        msg = sv_help
    else:
        plugin = svm.match_plugin((com,) if isinstance(com, str) else com)
        if not plugin:
            msg = "没有找到该插件,可以发送使用帮助获取使用帮助"
        else:
            msg = plugin.usage
    await session.send(msg)


@sv.ui_command("详细使用帮助")
async def usage_all(session: CommandSession):
    """同上

    发送all_help
    本意为给第一次使用稽器人想知道全部功能的人使用

    Args:
        session: bot封装的信息
    """
    await session.send(all_help)
