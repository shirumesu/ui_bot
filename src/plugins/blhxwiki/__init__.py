from nonebot import CommandSession
from .datasource import get_page, get_result

import config
from src.Services import uiPlugin

sv_help = """碧蓝航线wiki | 使用帮助
括号内的文字即为指令,小括号内为可选文字(是否必带请自行参照使用示例)
[blhxwiki] -> 查询blhx页面,会截图发出来
特别注意:
    1.直接发blhxwiki会发首页网址
    2.截图的是wiki.bilibili.com/blhx/xxxxxx,其中是你发的xxxxxx,
[blhxwiki搜索] -> 搜索页面,如果你是懒鬼且忘记了页面 可以使用搜索,获取搜索页面
使用示例:
    blhxwiki搜索 203
    >>> wiki搜索的网页截图(其中包含各种页面和标题,例如装备考究舰炮篇 （“德国双联装203毫米舰炮”章节），埃克塞特)
    这时候可以再使用blhx 查询 标题一般就对应网址了(当然记得去掉括号,例如上述203xxx章节)
blhxwiki常用网页:
1.pve小圣榜: 常用舰船理论综合输出与生存能力
↑ P.S.: 由于图表折叠了,其实只能点进网页看 ↑
2.弹幕性能: 全船全弹发射，专属弹幕，技能弹幕性能一览
3.武器榜单: 全武器对护甲补正一览
4.装备下位替代查询: 推荐装备下位替代
5.打捞表: 碧蓝航线全地图练级和图纸舰娘打捞推荐度详表
6.防空表: 防空输出比较（仅常用船只）
7.pve一图榜: PVE用舰船综合性能强度榜
8.重樱船名反和谐对照: 重樱船名称对照表
使用方法: blhxwiki 然后带上冒号后的字即可
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
