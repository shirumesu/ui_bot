import os
import json
from random import randint
from asyncio import sleep

from nonebot import on_command, CommandSession, get_bot

from src.Services import uiPlugin


sv_help = """俄罗斯轮盘 | 使用帮助
括号内的文字即为指令,小括号内为可选文字(是否必带请自行参照使用示例)
[俄罗斯轮盘/开枪/俄罗斯转盘] -> 开启一场游戏或是开枪
    特别注意:
        指令问题 -> 这里三个指令其实是没有分别的
    使用示例:
        俄罗斯轮盘 -> 开启一场游戏或是开枪
        俄罗斯转盘 -> 开启一场游戏或是开枪
        开枪 -> 开启一场游戏或是开枪
"""
sv = uiPlugin(["russian", "俄罗斯轮盘"], False, usage=sv_help)
bot = get_bot()
fd = os.path.dirname(__file__)

try:
    with open(os.path.join(fd, "rsdata.json"), "r+") as f:
        data = json.load(f)
except Exception:
    data = {}
try:
    with open(os.path.join(fd, "rsplayer.json"), "r+") as f:
        player = json.load(f)
except:
    player = {}


def save(data, file):
    with open(file, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


# main part
@sv.ui_command("rs", aliases=("俄罗斯轮盘", "俄罗斯转盘", "开枪"))
async def spin(session: CommandSession):
    """俄罗斯轮盘游戏,同时执行开枪/开启游戏

    Args:
        session (CommandSession): bot封装的信息
    """
    user = str(session.ctx["user_id"])
    group = session.ctx["group_id"]
    if group not in player:
        player[group] = {}
    if user not in player[group]:
        player[group][user] = {}
        if session.ctx.sender["card"] is not None:
            player[group][user]["nickname"] = session.ctx.sender["card"]
        else:
            player[group][user]["nickname"] = session.ctx.sender["nickname"]
        player[group][user]["win"] = 0
        player[group][user]["death"] = 0
    if group not in data:
        data[group] = {}
        data[group]["curnum"] = 0
        data[group]["next"] = 1
    if data[group]["curnum"] <= 0:
        msg = "欢迎参与紧张刺激的俄罗斯轮盘活动，请输入要填入的子弹数目(最多6颗)"
        bullet = int(session.get("bullet", prompt=msg))
        if bullet < 1 or bullet > 6:
            session.finish("数目不正确，请重新开始.")
        else:
            data[group]["curnum"] = bullet
            data[group]["next"] = randint(0, 6 - data[group]["curnum"])
            await session.send("装填完毕")
    else:
        if data[group]["next"] == 0:
            await session.send("很不幸，你死了......")
            # await bot.set_group_ban(group_id=group, user_id=int(user), duration=60)
            player[group][user]["death"] += 1
            data[group]["curnum"] -= 1
            data[group]["next"] = randint(0, 6 - data[group]["curnum"])
            if data[group]["curnum"] <= 0:
                await session.send("感谢各位的参与，来看一下游戏结算吧:")
                await sleep(1)
                msg = ""
                for i in player[group].values():
                    msg += "%s:  胜利: %s   死亡: %s\n" % (
                        i["nickname"],
                        i["win"],
                        i["death"],
                    )
                player[group] = {}
                data[group]["curnum"] = 0
                data[group]["next"] = 1
                player.clear()
                await session.send(msg)
            else:
                await session.send("欢迎下一位.还剩%d发" % data[group]["curnum"])
        else:
            data[group]["next"] -= 1
            msg = "你活了下来，下一位.还剩%d发" % data[group]["curnum"]
            player[group][user]["win"] += 1
            await session.send(msg)
    save(data, os.path.join(fd, "rsdata.json"))
    save(player, os.path.join(fd, "rsplayer.json"))
