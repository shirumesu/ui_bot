import ujson
import os
from nonebot import message_preprocessor, get_bot, CommandSession

from src.ui_exception import Shut_Up_Error
from src.Services import uiPlugin_Master
from soraha_utils import logger, async_uio


sv = uiPlugin_Master.get_plugins("bot_manager")

bot = get_bot()
st_path = os.path.join(os.getcwd(), "src", "plugins", "bot_manager", "shutup.json")
try:
    with open(st_path, "r", encoding="utf-8") as f:
        SHUTUP = ujson.load(f)
except FileNotFoundError:
    SHUTUP = {}
    with open(st_path, "w", encoding="utf-8") as f:
        ujson.dump(SHUTUP, f, ensure_ascii=False, indent=4)


@sv.ui_command("闭嘴")
async def shut_up(session: CommandSession) -> None:

    gid = str(session.event.group_id)

    SHUTUP[gid] = [True, 0]
    await async_uio.save_file(
        "json",
        obj=SHUTUP,
        save_path=os.path.join(
            os.getcwd(), "src", "plugins", "bot_manager", "shutup.json"
        ),
    )

    logger.debug(SHUTUP)
    await session.send("……那我走了哦…呜呜")


@sv.ui_command("说话")
async def speak(session: CommandSession) -> None:
    gid = str(session.event.group_id)
    SHUTUP[gid] = [False, 0]
    await async_uio.save_file(
        "json",
        obj=SHUTUP,
        save_path=os.path.join(
            os.getcwd(), "src", "plugins", "bot_manager", "shutup.json"
        ),
    )
    logger.debug(SHUTUP)
    await session.finish("好耶！")


@message_preprocessor
async def Shut_Up(Bot, Event, Plutin_manager):
    if Event.raw_message == "说话":
        return
    elif str(Event.group_id) in SHUTUP and SHUTUP[str(Event.group_id)][0]:
        SHUTUP[str(Event.group_id)][1] += 1
        raise Shut_Up_Error(f"bot在群({Event.group_id})被禁止说话了！可以使用`说话`来让bot开启响应！")
