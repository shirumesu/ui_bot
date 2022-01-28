from nonebot import CommandSession

from src.Services import uiPlugin
from src.plugins.setu_score.data_source import pic_score

sv_help = """表情制作 | 使用帮助
括号内的文字即为指令,小括号内为可选文字(是否必带请自行参照使用示例)
[色图评分 (图片)] -> 给色图打分！
    特别注意 -> 多张图片仅支持第一张
""".strip()
sv = uiPlugin(["setu_score", "给色图打分"], False, usage=sv_help)

scorer = pic_score()
assess_base = {
    500: "您完全不打算让弟弟休息会是吗?",
    400: "一般",
    300: "好色哦!",
    200: "什么垃圾",
    100: "您搁这倒垃圾呢?",
    0: "您还是发福瑞吧",
}


@sv.ui_command("色图评分", aliases=("色图打分",))
async def setu_score(session: CommandSession):
    image = session.get("image")
    res = await scorer.get_score(image[0])
    if res["status"]:
        score = res["result"]
        text = assess_base.get(round(score, -2))
        await session.finish(f"我的评价:{score}\n{text}")


@setu_score.args_parser
async def _(session: CommandSession):
    """指令解析器

    Args:
        session (CommandSession): bot封装的消息
    """

    if session.current_arg_images:
        session.state["image"] = session.current_arg_images
        return

    if session.current_arg_text:
        if session.current_arg_text.strip() == "done":
            await session.finish("会话已结束")

    if not session.current_arg_images:
        await session.pause("羽衣不会读心哦,要把图片发出来才行！")
