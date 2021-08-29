from nonebot import message_preprocessor, get_bot, on_command, CommandSession

from src.Services import Service_Master
from src.ui_exception import Shut_Up_Error

bot = get_bot()
SHUTUP = {}


@on_command("闭嘴")
async def shut_up(session: CommandSession) -> None:
    stat = await Service_Master().check_permission("bot_manager", session.event)
    if not stat[0]:
        await session.finish(stat[3])

    gid = session.event.group_id

    SHUTUP[gid] = [True, 0]

    await session.finish("……那我走了哦…呜呜")


@on_command("说话")
async def speak(session: CommandSession) -> None:
    stat = await Service_Master().check_permission("bot_manager", session.event)
    if not stat[0]:
        await session.finish(stat[3])

    gid = session.event.group_id

    SHUTUP[gid] = [False, 0]

    await session.finish("好耶！")


@message_preprocessor
async def Shut_Up(Bot, Event, Plutin_manager):
    if (
        Event.group_id in SHUTUP
        and SHUTUP[Event.group_id][0]
        and SHUTUP[Event.group_id][1] < 3
    ):
        await bot.send(Event, "呜呜……就算你一直说我也没办法说话了啦,来试试对我说`说话`吧！")
    raise Shut_Up_Error(f"bot在群({Event.group_id})被禁止说话了！可以使用`说话`来让bot开启响应！")
