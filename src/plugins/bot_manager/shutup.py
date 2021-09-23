import ujson
import os
from loguru import logger
from nonebot import message_preprocessor, get_bot, on_command, CommandSession

from src.Services import Service_Master
from src.ui_exception import Shut_Up_Error

bot = get_bot()
st_path = os.path.join(os.getcwd(), "src", "plugins", "bot_manager", "shutup.json")
try:
    with open(st_path, "r", encoding="utf-8") as f:
        SHUTUP = ujson.load(f)
except FileNotFoundError:
    SHUTUP = {}
    with open(st_path, "w", encoding="utf-8") as f:
        ujson.dump(SHUTUP, f, ensure_ascii=False, indent=4)


@on_command("闭嘴")
async def shut_up(session: CommandSession) -> None:
    stat = await Service_Master().check_permission("bot_manager", session.event)
    if not stat[0]:
        await session.finish(stat[3])

    gid = str(session.event.group_id)

    SHUTUP[gid] = [True, 0]
    with open(st_path, "w", encoding="utf-8") as f:
        ujson.dump(SHUTUP, f, indent=4, ensure_ascii=False)
    logger.debug(SHUTUP)
    await session.finish("……那我走了哦…呜呜")


@on_command("说话")
async def speak(session: CommandSession, gid) -> None:
    stat = await Service_Master().check_permission("bot_manager", session)
    if not stat[0]:
        await bot.send(session, stat[3])

    SHUTUP[gid] = [False, 0]
    with open(st_path, "w", encoding="utf-8") as f:
        ujson.dump(SHUTUP, f, indent=4, ensure_ascii=False)
    logger.debug(SHUTUP)
    await bot.send(session, "好耶！")


@message_preprocessor
async def Shut_Up(Bot, Event, Plutin_manager):
    if Event.raw_message == "说话":
        await speak(Event, str(Event.group_id))
    elif str(Event.group_id) in SHUTUP and SHUTUP[str(Event.group_id)][0]:
        SHUTUP[str(Event.group_id)][1] += 1
        raise Shut_Up_Error(f"bot在群({Event.group_id})被禁止说话了！可以使用`说话`来让bot开启响应！")
