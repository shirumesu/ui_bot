from nonebot import on_command, get_bot, CommandSession

from .airconutils import get_group_aircon, write_group_aircon, update_aircon, new_aircon, print_aircon
from src.Services import Service, Service_Master, GROUP_ADMIN, perm


sv_help = """群空调 | 使用帮助
括号内的文字即为指令,小括号内为可选文字(是否必带请自行参照使用示例)
[(开/关)空调] -> 开/关空调
[当前温度] -> 查看当前温度
[设置(环境)温度 (温度)] -> 设置空调温度或是环境温度
    使用示例:
        设置温度 60 -> 设置空调为60度
        设置环境温度 15000000 -> 将当前坐标转移到太阳核心
[设置风速 (档位)]
    参数详解：
        档位 -> 1~3
    使用示例:
        设置风速 1 -> 一档
[空调类型] -> 查看空调类型
[(升/降)级空调] -> 调整空调类型
    使用示例:
        升级空调
        降级空调
""".strip()
sv = Service(['aircon', '群空调'], sv_help,
             permission_change=GROUP_ADMIN, priv_use=False)

bot = get_bot()

ac_type_text = ["家用空调", "中央空调"]
AIRCON_HOME = 0
AIRCON_CENTRAL = 1

aircons = get_group_aircon(__file__)


async def check_status(gid: int, bot: bot, event: CommandSession, need_on: bool = True):
    """获取空调对象

    Args:
        gid (int): 群号
        bot (bot): bot对象
        event (CommandSession): bot封装的事件
        need_on (bool, optional): 空调是否需要开启. Defaults to True.

    Returns:
        aircons: 空调对象
    """

    if gid not in aircons:
        await event.send("空调还没装哦~发送“开空调”安装空调")
        return None

    aircon = aircons[gid]
    if need_on and not aircon["is_on"]:
        await event.send("💤你空调没开！")
        return None

    return aircon


async def check_range(bot: bot, event: CommandSession, low: int, high: int, errormsg: str, special: bool = None):
    """检查输入的数字是否有效

    Args:
        bot (bot): bot对象
        event (CommandSession): bot封装的信息
        low (int): 最低值
        high (int): 最高值
        errormsg (str): 错误时发送的信息
        special (bool, optional): 特别消息. Defaults to None.

    Returns:
        int: 如果有效,返回有效的数字,否则返回None
    """

    msg = event.current_arg_text.strip().split()

    if special is not None and msg[0] in special:
        return special[msg[0]]

    try:
        val = int(msg[0])
    except Exception:
        await event.send(f"⚠️输入有误！只能输入{low}至{high}的整数")
        return None

    if not low <= val <= high:
        await event.send(errormsg)
        return None

    return val


@on_command("开空调")
async def aircon_on(event: CommandSession):
    """开空调指令

    Args:
        event (CommandSession): bot封装的信息
    """
    stat = await Service_Master().check_permission('aircon', event.event)
    if not stat[0]:
        if stat[3]:
            await event.finish(stat[3])
        else:
            await event.finish(f'你没有足够权限使用此插件,要求权限{perm[stat[2]]},你的权限:{perm[stat[1]]}')

    if event.event.detail_type == 'group':
        gid = str(event.event['group_id'])
    else:
        await event.finish('群空调怎么私聊用啊(半恼)')

    if gid not in aircons:
        ginfo = await bot.get_group_info(group_id=gid)
        gcount = ginfo["member_count"]
        aircon = new_aircon(num_member=gcount)
        aircons[gid] = aircon
        await event.send("❄空调已安装~")
    else:
        aircon = aircons[gid]
        if aircon["is_on"]:
            await event.send("❄空调开着呢！")
            return

    update_aircon(aircon)
    aircon['is_on'] = True
    msg = print_aircon(aircon)
    write_group_aircon(__file__, aircons)
    await event.send("❄哔~空调已开\n" + msg)


@on_command("关空调")
async def aircon_off(event: CommandSession):
    """关空调指令

    Args:
        event (CommandSession): bot封装的信息
    """
    stat = await Service_Master().check_permission('aircon', event.event)
    if not stat[0]:
        if stat[3]:
            await event.finish(stat[3])
        else:
            await event.finish(f'你没有足够权限使用此插件,要求权限{perm[stat[2]]},你的权限:{perm[stat[1]]}')

    if event.event.detail_type == 'group':
        gid = str(event.event['group_id'])
    else:
        await event.finish('群空调怎么私聊用啊(半恼)')

    aircon = await check_status(gid, bot, event)
    if aircon is None:
        return

    update_aircon(aircon)
    aircon['is_on'] = False
    msg = print_aircon(aircon)
    write_group_aircon(__file__, aircons)
    await event.send('💤哔~空调已关\n' + msg)


@on_command("当前温度")
async def aircon_now(event: CommandSession):
    """查看当前温度

    Args:
        event (CommandSession): bot封装的信息
    """
    stat = await Service_Master().check_permission('aircon', event.event)
    if not stat[0]:
        if stat[3]:
            await event.finish(stat[3])
        else:
            await event.finish(f'你没有足够权限使用此插件,要求权限{perm[stat[2]]},你的权限:{perm[stat[1]]}')

    if event.event.detail_type == 'group':
        gid = str(event.event['group_id'])
    else:
        await event.finish('群空调怎么私聊用啊(半恼)')

    aircon = await check_status(gid, bot, event, need_on=False)
    if aircon is None:
        return

    aircon = aircons[gid]
    update_aircon(aircon)
    msg = print_aircon(aircon)
    write_group_aircon(__file__, aircons)

    if not aircon["is_on"]:
        msg = "💤空调未开启\n" + msg
    else:
        msg = "❄" + msg

    await event.send(msg)


@on_command("设置温度", aliases=("设定温度", ))
async def set_temp(event: CommandSession):
    """设置温度

    Args:
        event (CommandSession): bot封装的信息
    """
    stat = await Service_Master().check_permission('aircon', event.event)
    if not stat[0]:
        if stat[3]:
            await event.finish(stat[3])
        else:
            await event.finish(f'你没有足够权限使用此插件,要求权限{perm[stat[2]]},你的权限:{perm[stat[1]]}')

    if event.event.detail_type == 'group':
        gid = str(event.event['group_id'])
    else:
        await event.finish('群空调怎么私聊用啊(半恼)')

    aircon = await check_status(gid, bot, event)
    if aircon is None:
        return

    set_temp = await check_range(bot, event, -273, 999999,
                                 "只能设置-273-999999°C喔")
    if set_temp is None:
        return

    if set_temp == 114514:
        await event.send("这么臭的空调有什么装的必要吗")
        return

    update_aircon(aircon)
    aircon["set_temp"] = set_temp
    msg = print_aircon(aircon)
    write_group_aircon(__file__, aircons)
    await event.send("❄" + msg)


@on_command("设置风速", aliases=("设定风速", "设置风量", "设定风量"))
async def set_wind_rate(event: CommandSession):
    """设置空调风速

    Args:
        event (CommandSession): bot封装的信息
    """
    stat = await Service_Master().check_permission('aircon', event.event)
    if not stat[0]:
        if stat[3]:
            await event.finish(stat[3])
        else:
            await event.finish(f'你没有足够权限使用此插件,要求权限{perm[stat[2]]},你的权限:{perm[stat[1]]}')

    if event.event.detail_type == 'group':
        gid = str(event.event['group_id'])
    else:
        await event.finish('群空调怎么私聊用啊(半恼)')

    aircon = await check_status(gid, bot, event)
    if aircon is None:
        return

    if aircon["ac_type"] != AIRCON_HOME:
        await event.send("只有家用空调能调风量哦！")
        return

    wind_rate = await check_range(bot, event, 1, 3, "只能设置1/2/3档喔", {
        "低": 1,
        "中": 2,
        "高": 3
    })
    if wind_rate is None:
        return

    update_aircon(aircon)
    aircon["wind_rate"] = wind_rate - 1
    msg = print_aircon(aircon)
    write_group_aircon(__file__, aircons)
    await event.send("❄" + msg)


@on_command("设置环境温度", aliases=("设定环境温度"))
async def set_env_temp(event: CommandSession):
    """设置环境温度的指令

    Args:
        event (CommandSession): bot封装的信息
    """
    stat = await Service_Master().check_permission('aircon', event.event)
    if not stat[0]:
        if stat[3]:
            await event.finish(stat[3])
        else:
            await event.finish(f'你没有足够权限使用此插件,要求权限{perm[stat[2]]},你的权限:{perm[stat[1]]}')

    if event.event.detail_type == 'group':
        gid = str(event.event['group_id'])
    else:
        await event.finish('群空调怎么私聊用啊(半恼)')

    aircon = await check_status(gid, bot, event, need_on=False)
    if aircon is None:
        return

    env_temp = await check_range(bot, event, -273, 999999,
                                 "只能设置-273-999999°C喔")
    if env_temp is None:
        return

    if env_temp == 114514:
        await event.send("这么臭的空调有什么装的必要吗")
        return

    aircon = aircons[gid]
    update_aircon(aircon)
    aircon["env_temp"] = env_temp
    msg = print_aircon(aircon)
    write_group_aircon(__file__, aircons)

    if not aircon["is_on"]:
        msg = "💤空调未开启\n" + msg
    else:
        msg = "❄" + msg

    await event.send(msg)


@on_command("空调类型")
async def show_aircon_type(event: CommandSession):
    """查看空调类型

    Args:
        event (CommandSession): bot封装的信息
    """
    stat = await Service_Master().check_permission('aircon', event.event)
    if not stat[0]:
        if stat[3]:
            await event.finish(stat[3])
        else:
            await event.finish(f'你没有足够权限使用此插件,要求权限{perm[stat[2]]},你的权限:{perm[stat[1]]}')

    if event.event.detail_type == 'group':
        gid = str(event.event['group_id'])
    else:
        await event.finish('群空调怎么私聊用啊(半恼)')

    aircon = await check_status(gid, bot, event, need_on=False)
    if aircon is None:
        return

    aircon = aircons[gid]
    ac_type = aircon["ac_type"]

    msg = f"当前安装了{ac_type_text[ac_type]}哦~"
    await event.send(msg)


@on_command("升级空调", aliases=("空调升级", ))
async def upgrade_aircon(event: CommandSession):
    """升级空调

    Args:
        event (CommandSession): bot封装的信息
    """
    stat = await Service_Master().check_permission('aircon', event.event)
    if not stat[0]:
        if stat[3]:
            await event.finish(stat[3])
        else:
            await event.finish(f'你没有足够权限使用此插件,要求权限{perm[stat[2]]},你的权限:{perm[stat[1]]}')

    if event.event.detail_type == 'group':
        gid = str(event.event['group_id'])
    else:
        await event.finish('群空调怎么私聊用啊(半恼)')

    aircon = await check_status(gid, bot, event, need_on=False)
    if aircon is None:
        return

    aircon = aircons[gid]
    ac_type = aircon["ac_type"]
    if ac_type == len(ac_type_text) - 1:
        await event.send("已经是最高级的空调啦！")
        return

    update_aircon(aircon)
    ac_type += 1
    aircon["ac_type"] = ac_type
    msg = print_aircon(aircon)
    write_group_aircon(__file__, aircons)
    msg = f"❄已升级至{ac_type_text[ac_type]}~\n" + msg
    await event.send(msg)


@on_command("降级空调", aliases=("空调降级", ))
async def downgrade_aircon(event: CommandSession):
    """降级空调

    Args:
        event (CommandSession): bot封装的信息
    """
    stat = await Service_Master().check_permission('aircon', event.event)
    if not stat[0]:
        if stat[3]:
            await event.finish(stat[3])
        else:
            await event.finish(f'你没有足够权限使用此插件,要求权限{perm[stat[2]]},你的权限:{perm[stat[1]]}')

    if event.event.detail_type == 'group':
        gid = str(event.event['group_id'])
    else:
        await event.finish('群空调怎么私聊用啊(半恼)')

    aircon = await check_status(gid, bot, event, need_on=False)
    if aircon is None:
        return

    aircon = aircons[gid]
    ac_type = aircon["ac_type"]
    if ac_type == 0:
        await event.send("已经是最基础级别的空调啦！")
        return

    update_aircon(aircon)
    ac_type -= 1
    aircon["ac_type"] = ac_type
    msg = print_aircon(aircon)
    write_group_aircon(__file__, aircons)
    msg = f"❄已降级至{ac_type_text[ac_type]}~\n" + msg
    await event.send(msg)
