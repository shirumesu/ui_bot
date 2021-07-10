"""
此插件几乎完全照搬hoshino bot的切噜语插件
此处贴出链接
https://github.com/Ice-Cirno/HoshinoBot/blob/master/hoshino/modules/priconne/cherugo.py
感谢琪露诺佬的强强技术力

>>> 另外 有关切噜语：
https://bbs.nga.cn/read.php?tid=21636504&rand=167
"""
import re
from itertools import zip_longest

from nonebot import on_command, CommandSession
from nonebot.message import escape

from src.Services import GROUP_ADMIN, Service, Service_Master, perm


sv_help = """切噜语翻译 | 使用帮助
括号内的文字即为指令,小括号内为可选文字(是否必带请自行参照使用示例)
[切噜一下 翻译文本] -> 将人话翻译为切噜语(当然也可以是莫名其妙的文字)
[切噜~♪(翻译文本)] -> 将对人类而言为时过早的语言翻译为正常的人话
    特别注意:
        空格问题 -> 第一个指令是需要空格的,而第二个指令则不需要
题外话:
切噜～♪切噜切噜,切切噜啪,切噜噜噜!切拉唎咧，切拉拉噜,切噜噜巴噼?
切嘭!?切拉嘭,切拉嘭!切噜卟卟,切拉噜咧啰!切卟拉咧,切拉拉拉，切噜噜～♪☆！
切……切切切!?切拉唎卟,切唎唎?切拉唎啰,切拉唎啰啰啰?切啪拉啪……切噜，切噜噜噜……
哈?你突然在说什么呢学长…真差劲,我根本没想到你会说这样的话……等…住手!别!别过来!这里不行!
"""
sv = Service(["cheru", "切噜语翻译"], sv_help, permission_change=GROUP_ADMIN)

CHERU_SET = "切卟叮咧哔唎啪啰啵嘭噜噼巴拉蹦铃"
CHERU_DIC = {c: i for i, c in enumerate(CHERU_SET)}
ENCODING = "gb18030"
rex_split = re.compile(r"\b", re.U)
rex_word = re.compile(r"^\w+$", re.U)
rex_cheru_word: re.Pattern = re.compile(rf"切[{CHERU_SET}]+", re.U)


def grouper(iterable, n, fillvalue=None):
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)


def word2cheru(w: str) -> str:
    c = ["切"]
    for b in w.encode(ENCODING):
        c.append(CHERU_SET[b & 0xF])
        c.append(CHERU_SET[(b >> 4) & 0xF])
    return "".join(c)


def cheru2word(c: str) -> str:
    if not c[0] == "切" or len(c) < 2:
        return c
    b = []
    for b1, b2 in grouper(c[1:], 2, "切"):
        x = CHERU_DIC.get(b2, 0)
        x = x << 4 | CHERU_DIC.get(b1, 0)
        b.append(x)
    return bytes(b).decode(ENCODING, "replace")


def str2cheru(s: str) -> str:
    c = []
    for w in rex_split.split(s):
        if rex_word.search(w):
            w = word2cheru(w)
        c.append(w)
    return "".join(c)


def cheru2str(c: str) -> str:
    return rex_cheru_word.sub(lambda w: cheru2word(w.group()), c)


@on_command("切噜一下")
async def cherulize(session: CommandSession):
    stat = await Service_Master().check_permission("cheru", session.event)
    if not stat[0]:
        if stat[3]:
            await session.finish(stat[3])
        else:
            await session.finish(
                f"你没有足够权限使用此插件,要求权限{perm[stat[2]]},你的权限:{perm[stat[1]]}"
            )
    s = session.current_arg_text
    if len(s) > 500:
        await session.finish("切、切噜太长切不动勒切噜噜...", at_sender=True)
    await session.finish("切噜～♪" + str2cheru(s))


@on_command("切噜～♪", patterns=r"^切噜～♪*")
async def decherulize(session: CommandSession):
    stat = await Service_Master().check_permission("cheru", session.event)
    if not stat[0]:
        if stat[3]:
            await session.finish(stat[3])
        else:
            await session.finish(
                f"你没有足够权限使用此插件,要求权限{perm[stat[2]]},你的权限:{perm[stat[1]]}"
            )
    s = session.current_arg_text[4:]
    if len(s) > 1501:
        await session.finish("切、切噜太长切不动勒切噜噜...", at_sender=True)
    cheru = escape(cheru2str(s))
    s = (s[:3] + "..." + s[-3:]) if len(s) > 10 else s
    msg = "\n" + s + "的切噜噜是：\n" + cheru
    await session.finish(msg, at_sender=True)
