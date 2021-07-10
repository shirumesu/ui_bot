import os
import re
import ujson
import random
from loguru import logger

from nonebot import on_command, CommandSession, message_preprocessor, get_bot

import config
from src.Services import Service, Service_Master, GROUP_ADMIN


sv_help = """自定义回复 | 使用帮助
括号内的文字即为指令,小括号内为可选文字(是否必带请自行参照使用示例)
特别注意:
    -> 请不要使用此功能做任何奇怪的事情,被发现将会立即加入黑名单
    -> 本功能群聊限定
[定义 (需要被回复的信息)] -> 自定义回复
    参数详解:
        需要被回复的信息 -> 目前可以定义图片/emoji/文本等(请不要定义分享这类东西,会有bug),需要回复的任何内容,具体请参照使用示例,和实际使用的指引
    特别注意:
        多个回复 -> 支持添加多个回复(请一个个来),具体请参照使用示例
        风控问题 -> 为了防止刷屏以及可能的风控问题,回复将会是50%概率回复而非遇到即回复
    使用示例:
        (箭头后的为羽衣的回复)
        定义 喂 三点几嚟
        -> 需要回复的信息是？(目前对于该消息会回复1.xxx 2.yyy)(如果有)
        饮茶先啦 做条毛啊做
        -> 定义成功
        喂 三点几嚟
        -> 饮茶先啦 做条毛啊做
        喂 三点几嚟 来饮茶先啦
        -> (仅检测完全匹配的定义,因此不会回复)
[查看所有定义] -> 查看本群的所有定义
[删除定义 (需要被回复的信息)] -> 本群/私聊删除某个定义
[禁用定义 (需要被回复的信息)] -> 某个定义整个删除(群管理员或以上限定)(会在所有群清理该定义,用于清理有问题的定义)
""".strip()

sv = Service(
    ["reply_msg", "自定义回复"], sv_help, permission_change=GROUP_ADMIN, priv_use=False
)


bot = get_bot()

config_path = os.path.join(os.getcwd(), "src", "plugins", "reply_msg", "config.json")
if os.path.exists(config_path):
    with open(config_path, "r", encoding="utf-8") as f:
        self_config = ujson.load(f)
else:
    with open(config_path, "w", encoding="utf-8") as f:
        self_config = {}
        ujson.dump(self_config, f, indent=4, ensure_ascii=False)


@on_command("定义")
async def reply_msg(session: CommandSession):
    """定义功能的主函数

    Args:
        session (CommandSession): bot封装的信息
    """
    stat = await Service_Master().check_permission("reply_msg", session.event)
    if not stat[0]:
        await session.finish(stat[3])
    reply_msg = session.current_arg.strip()
    if re.match(r"\[CQ:xml,data=<\?xml[\s\S]*]", reply_msg):
        await session.finish("定义分享会有bug,禁止定义(而且为什么要定义分享啊)")
    if len(reply_msg) >= 1000:
        await session.finish("这也太长了…羽衣记不住了切噜噜……")
    elif not reply_msg:
        await session.finish("不可以空输入哦")

    gid = str(session.event.group_id)
    if gid in self_config and reply_msg in self_config[gid]:
        now_reply = "\n".join(
            [f"{int(x)+1}.{y}" for x, y in enumerate(self_config[gid][reply_msg])]
        )
    else:
        now_reply = ""
    await session.apause("需要回复的信息是？" + now_reply)

    msg = session.current_arg.strip()
    if re.match(r"\[CQ:xml,data=<\?xml[\s\S]*]", reply_msg):
        await session.finish("定义分享会有bug,禁止定义(而且为什么要定义分享啊)")
    if len(msg) >= 1000:
        await session.finish("这也太长了…羽衣记不住了切噜噜……")
    elif not msg:
        await session.finish("不可以空输入哦")
    if gid not in self_config:
        self_config[gid] = {reply_msg: [msg]}
    elif reply_msg not in self_config[gid]:
        self_config[gid][reply_msg] = [msg]
    else:
        self_config[gid][reply_msg].append(msg)

    with open(config_path, "w", encoding="utf-8") as f:
        ujson.dump(self_config, f, ensure_ascii=False, indent=4)
    await session.finish("定义成功!")


@on_command("查看所有定义")
async def show_reply(session: CommandSession):
    """查看所有定义功能的主函数

    Args:
        session (CommandSession): bot封装的信息
    """
    stat = await Service_Master().check_permission("reply_msg", session.event)
    if not stat[0]:
        await session.finish(stat[3])
    gid = str(session.event.group_id)
    if gid not in self_config:
        await session.finish("本群还没有任何自定义回复")
    reply_msg = "\n".join([f"{x}: {','.join(y)}" for x, y in self_config[gid].items()])
    await session.finish(f"本群有以下订阅:\n" + reply_msg)


@on_command("删除定义")
async def del_reply(session: CommandSession):
    """删除定义的主函数

    Args:
        session (CommandSession): bot封装的信息
    """
    stat = await Service_Master().check_permission("reply_msg", session.event)
    if not stat[0]:
        await session.finish(stat[3])
    gid = str(session.event.group_id)
    msg = session.current_arg.strip()
    if not msg:
        await session.finish("不可以空输入哦")
    if gid not in self_config or msg not in self_config[gid]:
        await session.finish("没有找到该定义！")
    if len(self_config[gid][msg]) != 1:
        await session.apause("要删除的是哪一句?目前对于该定义有:\n" + "\n".join(self_config[gid][msg]))
        del_msg = session.current_arg.strip()
        if del_msg in self_config[gid][msg]:
            self_config[gid][msg].remove(del_msg)
        else:
            session.finish("没有找到该定义！")
    else:
        del self_config[gid][msg]
    with open(config_path, "w", encoding="utf-8") as f:
        ujson.dump(self_config, f, ensure_ascii=False, indent=4)
    await session.finish("删除成功！")


@on_command("禁用定义")
async def del_all_reply(session: CommandSession):
    stat = await Service_Master().check_permission(
        "reply_msg", session.event, GROUP_ADMIN
    )
    if not stat[0]:
        await session.finish(stat[3])
    msg = session.current_arg.strip()
    del_list = [str(gid) for gid in self_config if msg in self_config[str(gid)]]
    if del_list:
        for i in del_list:
            del self_config[i][msg]
        with open(config_path, "w", encoding="utf-8") as f:
            ujson.dump(self_config, f, ensure_ascii=False, indent=4)
    else:
        await session.finish("没有在任何群的定义中找到该定义！")
    await session.finish(f"清理成功！一共在{len(del_list)}个群中清理了该定义")


@message_preprocessor
async def search(Bot, event, plutin_manager):
    stat = await Service_Master().check_permission("reply_msg", event)
    if not stat[0]:
        return
    msg = event["raw_message"].strip()
    gid = event.group_id
    if str(gid) not in self_config or msg not in self_config[str(gid)]:
        return
    s = random.choice([True, False])
    if s:
        await bot.send_group_msg(
            group_id=gid, message=random.choice(self_config[str(gid)][msg])
        )
