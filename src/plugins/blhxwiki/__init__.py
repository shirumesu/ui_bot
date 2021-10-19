from nonebot import CommandSession
from .datasource import get_page, get_result

import config
from src.Services import uiPlugin

sv_help = """碧蓝航线wiki | 使用帮助
括号内的文字即为指令,小括号内为可选文字(是否必带请自行参照使用示例)
[blhxwiki (舰娘/装备)] -> 拿数据
    目前仅支持舰娘
    装备咕了
"""
sv = uiPlugin(["blhxwiki", "碧蓝航线wiki"], False, usage=sv_help, private_use=True)


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
    name = session.current_arg_text.strip()
    info = await get_result(session, name)
    text = (
        f"{info['name']}\n"
        f"======角色基本信息======\n"
        f"稀有度: {info['rarity']}\n"
        f"{info['build_time']}\n"
        f"======舰队科技======\n"
        f"获得: {info['fleet_get']}({info['fleet_get_extra']})\n"
        f"满星: {info['fleet_full']}({info['fleet_full_extra']})\n"
        f"lv120: {info['fleet_lv120']}({info['fleet_lv120_extra']})\n"
        f"======属性======\n"
        f"耐久: {info['naijiu']}\n"
        f"装甲: {info['zhuangjia']}\n"
        f"装填: {info['zhuangtian']}\n"
        f"炮击: {info['paoji']}\n"
        f"雷击: {info['leiji']}\n"
        f"机动: {info['jidong']}\n"
        f"防空: {info['fangkong']}\n"
        f"航空: {info['hangkong']}\n"
        f"消耗: {info['xiaohao']}\n"
        f"反潜: {info['fanqian']}\n"
        f"幸运: {info['xinyun']}\n"
        f"航速: {info['hangsu']}\n"
        f"======武器效率======\n"
        f"{info['arm1_type']}: {info['arm1_effi']}\n"
        f"{info['arm2_type']}: {info['arm2_effi']}\n"
        f"{info['arm3_type']}: {info['arm3_effi']}\n"
        f"======技能======\n"
    )
    for skill_name, descript in info["skills"].items():
        text += f"{skill_name}: {descript}\n"
    url = "https://wiki.biligame.com/blhx/" + name
    await session.finish(text + url)
