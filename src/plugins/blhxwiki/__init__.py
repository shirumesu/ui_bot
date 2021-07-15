from concurrent.futures.thread import ThreadPoolExecutor

from nonebot import on_command, CommandSession, get_bot

from src.plugins.blhxwiki.datasource import driver
from src.Services import Service, Service_Master, GROUP_ADMIN


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
sv = Service(
    ["blhxwiki", "碧蓝航线wiki"], sv_help, True, True, permission_change=GROUP_ADMIN
)

web = driver()
bot = get_bot()
executor = ThreadPoolExecutor(15)


@on_command("blhxwiki搜索", aliases=["碧蓝航线wiki搜索", "碧蓝wiki搜索", "blhx维基搜索", "blhx百科搜索"])
async def blhxwiki_search(session: CommandSession):
    """blhxwiki搜索的主函数

    Args:
        session (CommandSession): bot封装的消息
    """
    stat = await Service_Master().check_permission("blhxwiki", session.event)
    if not stat[0]:
        await session.finish(stat[3])

    if not session.current_arg_text:
        await session.finish("你要搜索的东西都没有怎么搜啊!")

    await session.send("正在尝试获取……")

    url = f"https://searchwiki.biligame.com/blhx/index.php?search={session.current_arg_text.strip()}&go=前往"
    res = await bot.loop.run_in_executor(executor, web.get_pac, url)
    if isinstance(res, str):
        await session.finish(f"发生错误:{res}\nwiki网页:{url}")
    else:
        await session.send(res)
        await session.finish(f"防止图片太长风控发不出,额外将网页发出来: {url}")


@on_command("blhxwiki", aliases=["碧蓝航线wiki", "碧蓝wiki", "blhx维基", "blhx百科"])
async def blhxwiki(session: CommandSession):
    """blhxwiki的主函数

    Args:
        session (CommandSession): bot封装的消息
    """
    stat = await Service_Master().check_permission("blhxwiki", session.event)
    if not stat[0]:
        await session.finish(stat[3])

    await session.send("正在尝试获取……")
    url = "https://wiki.biligame.com/blhx/"
    if not session.current_arg_text:
        await session.finish(f"wiki首页: {url}")
    url = url + session.current_arg_text.strip()
    res = await bot.loop.run_in_executor(executor, web.get_pac, url)
    if isinstance(res, str):
        await session.finish(f"发生错误:{res}\nwiki网页:{url}")
    else:
        await session.send(res)
        await session.finish(f"防止图片太长风控发不出,额外将网页发出来: {url}")
