from nonebot import on_command, CommandSession

from . import monika
from src.Services import GROUP_ADMIN, Service, Service_Master


sv_help = """莫妮卡翻译 | 使用帮助
括号内的文字即为指令,小括号内为可选文字(是否必带请自行参照使用示例)
[莫妮卡乱码 翻译文本] -> 将任何文本乱码为justmonika
[莫妮卡翻译 翻译文本] -> 将莫妮卡乱码恢复人话
注意:
最后一个文字有概率会莫名丢失( 好吧 我太菜了
总之将就用(
题外话:
jÙṦᵵ𝕄𝓞𝕹ᴉᴋ𝕒jÙṦẗ𝕸ᴔℕᴉᴋẚjÙṦᵵ𝕞ᴔ𝔫ᴉʞᶐjÙṦᵵ𝕄𝔒𝔑ᵼⱩẚjÙṦᵵ𝕞œ𝔫ᴉⱪ𝕒
"""

sv = Service(["justmonika", "莫妮卡翻译"], sv_help, permission_change=GROUP_ADMIN)


_monika = monika.JustMonika()


@on_command("莫妮卡乱码")
async def monika_tran(session: CommandSession):
    stat = await Service_Master().check_permission("cheru", session.event)
    if not stat[0]:
        await session.finish(stat[3])

    text = session.current_arg_text.strip()
    if len(text) % 2:
        text = text + "<OOV>"
    await session.finish(_monika.encode(text))


@on_command("莫妮卡翻译")
async def monika_tran_2_word(session: CommandSession):
    stat = await Service_Master().check_permission("cheru", session.event)
    if not stat[0]:
        await session.finish(stat[3])

    text = session.current_arg_text.strip()
    fin_text = _monika.decode(text)
    if "<OOV>" in fin_text:
        fin_text = fin_text.replace("<OOV>", "")
    await session.finish(fin_text)
