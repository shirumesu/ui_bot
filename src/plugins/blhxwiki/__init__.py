from nonebot import CommandSession, MessageSegment, command

from .datasource import get_text, update_photo, send_qiangdubang
from .uploader import updater
from src.Services import uiPlugin

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
"""
sv = uiPlugin(
    ["blhxwiki", "碧蓝航线wiki"],
    False,
    usage=sv_help,
    private_use=True,
    use_source_folder=True,
)
updater = updater()


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
