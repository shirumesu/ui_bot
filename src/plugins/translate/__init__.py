from nonebot import on_command, CommandSession, MessageSegment

from src.plugins.translate import baidu, embed
from src.Services import Service, Service_Master, GROUP_ADMIN


sv_help = """翻译漫画 | 使用帮助
括号内的文字即为指令,小括号内为可选文字(是否必带请自行参照使用示例)
[翻译漫画 (图片)] -> 翻译漫画,**处理模式为竖排,横版请使用翻译图片**
    参数详解:
        图片 -> 支持多张,请包含在一个信息内,具体可以参照使用示例
    特别注意:
        多张图片 -> 由于担心风控问题,会逐张发送,因此可能有刷屏问题
        额度问题 -> 使用百度ocr进行翻译,高精度的额度一天为50张,标准模式一天500张,优先使用高精度,总额度一天550张,但是标准模式识别率极差,可以说是完全没翻译过
        翻译精度 -> 横版文字可以有效翻译,支持多种语言,竖排则有极大的准确度问题,基本只能意会,需要一定的日语能力配合翻译结果来看(当然你n1直接啃就完了)
    使用示例:
        (→后为羽衣的回复)
        翻译漫画
            ->需要翻译什么图片呢？
        (图片*n|图片)
            ->(翻译结果)
    使用示例其二：
        翻译漫画 (图片*n|图片)
            -> (翻译结果)
[翻译图片 (图片)] -> 翻译图片/漫画,可以为竖排的
    同上,但横版图片ocr结果一般优良一些=翻译质量更高
""".strip()

sv = Service(['translate', '翻译漫画'], sv_help, use_folder=True,
             use_cacha_folder=True, permission_change=GROUP_ADMIN)


@on_command('翻译漫画', patterns=r'^翻译漫画')
async def translate_manga(session: CommandSession):
    """翻译漫画的主函数

    Args:
        session (CommandSession): bot封装的信息
    """
    stat = await Service_Master().check_permission('translate', session.event)
    if not stat[0]:
        await session.finish(stat[3])

    urls = session.get('image')

    seq = []
    for i in urls:
        url = i
        words_data, path = await baidu.process(url, vertical=True)
        path = await embed.process_manga(words_data, path)
        seq = MessageSegment.image('file:///' + path)
        await session.send(seq)


@on_command('翻译图片', patterns=r'^翻译图片')
async def translate_photo(session: CommandSession):
    """翻译图片的主函数

    Args:
        session (CommandSession): bot封装的信息
    """
    stat = await Service_Master().check_permission('translate', session.event)
    if not stat[0]:
        await session.finish(stat[3])

    urls = session.get('image')

    seq = []
    for i in urls:
        url = i
        words_data, path = await baidu.process(url, vertical=False)
        path = await embed.process_manga(words_data, path)
        seq = MessageSegment.image('file:///' + path)
        await session.send(seq)


@translate_photo.args_parser
async def _(session: CommandSession):

    if session.current_arg_images:
        session.state["image"] = session.current_arg_images
        return

    if session.current_arg_text:
        if session.current_arg_text.strip() == "done":
            await session.finish("会话已结束")

    if not session.current_arg_images:
        await session.pause("要翻译的漫画是？\n可以发送\"done\"结束")


@translate_manga.args_parser
async def _(session: CommandSession):

    if session.current_arg_images:
        session.state["image"] = session.current_arg_images
        return

    if session.current_arg_text:
        if session.current_arg_text.strip() == "done":
            await session.finish("会话已结束")

    if not session.current_arg_images:
        await session.pause("要翻译的漫画是？\n可以发送\"done\"结束")
