from nonebot import CommandSession

from .datasource import get_text, update_photo, send_qiangdubang
from src.Services import uiPlugin

sv_help = """碧蓝航线wiki | 使用帮助
括号内的文字即为指令,小括号内为可选文字(是否必带请自行参照使用示例)
[blhxwiki (舰娘/装备)] -> 拿数据
    支持装备/舰娘,但要求全名,自定义词典正在咕咕叫
[更新图片] -> 更新缓存图片
[强度榜] -> 舰娘强度榜
"""
sv = uiPlugin(
    ["blhxwiki", "碧蓝航线wiki"],
    False,
    usage=sv_help,
    private_use=True,
    use_source_folder=True,
)
command_list = {"强度榜": send_qiangdubang, "更新图片": update_photo}


@sv.ui_command(
    "blhxwiki",
    aliases=["碧蓝航线wiki", "碧蓝wiki", "blhx维基", "blhx百科"],
    ignore_superuser=True,
)
async def blhxwiki(session: CommandSession):
    """blhxwiki的主函数

    Args:
        session (CommandSession): bot封装的消息
    """
    await session.send("正在尝试获取……")
    cmd = session.current_arg_text.strip()
    if cmd in command_list:
        await command_list[cmd](session)
    info = await get_text(cmd)
    await session.finish(info)
