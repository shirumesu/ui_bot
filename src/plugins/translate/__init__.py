from nonebot import CommandSession, MessageSegment
import os
from src.plugins.translate import baidu, embed
from src.ui_exception import baidu_ocr_get_Error
from uuid import uuid4
from src.Services import uiPlugin

import config
from soraha_utils import async_uio

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
sv = uiPlugin(
    ["translate", "翻译漫画"],
    False,
    usage=sv_help,
    use_source_folder=True,
    use_cache_folder=True,
)


@sv.ui_command("翻译漫画", patterns=r"^翻译漫画")
async def translate_manga(session: CommandSession):
    """翻译漫画的主函数

    Args:
        session (CommandSession): bot封装的信息
    """
    urls = session.get("image")

    seq = []
    for i in urls:
        save_path = os.path.join(
            config.res, "cacha", "translate", str(uuid4())[-12:] + ".png"
        )
        await async_uio.save_file(
            type="url_image", url=i, proxy=config.proxies_for_all, save_path=save_path
        )
        path = await baidu.process_manga(save_path)
        seq = MessageSegment.image("file:///" + path)
        await session.send(seq)


@sv.ui_command("翻译图片", patterns=r"^翻译图片")
async def translate_photo(session: CommandSession):
    """翻译图片的主函数

    Args:
        session (CommandSession): bot封装的信息
    """

    urls = session.get("image")

    seq = []
    for i in urls:
        url = i
        try:
            words_data, path = await baidu.process(url, vertical=False)
        except baidu_ocr_get_Error:
            await session.finish("请求翻译api时发生错误,翻译失败")

        seq = MessageSegment.image("file:///" + path)
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
        await session.pause('要翻译的漫画是？\n可以发送"done"结束')


@translate_manga.args_parser
async def _(session: CommandSession):

    if session.current_arg_images:
        session.state["image"] = session.current_arg_images
        return

    if session.current_arg_text:
        if session.current_arg_text.strip() == "done":
            await session.finish("会话已结束")

    if not session.current_arg_images:
        await session.pause('要翻译的漫画是？\n可以发送"done"结束')
