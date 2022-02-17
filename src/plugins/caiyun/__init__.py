import re

from nonebot import CommandSession

from soraha_utils import logger

import config
from src.plugins.caiyun.cy_ai import Caiyun
from src.Services import uiPlugin


sv_help = """彩云续写 | 使用帮助
括号内的文字即为指令,小括号内为可选文字(是否必带请自行参照使用示例)
[彩云续写 文本] -> 尝试调用彩云ai进行续写
    设置标题:
        如果需要设置标题, 请输入 《这是标题》这是正文 例如:
        彩云续写 《我是标题》今天也很可爱!
    特别注意:
        之后会有如分支选择等操作, 请根据说明使用
    分支:
        [选择分支 数字] -> 选择一个分支, 然后继续续写
        [结束续写] -> 结束续写
"""
help_text = """============
请输入一个分支的数字(1 2或3)来继续续写, 或是输入`结束续写`来结束
请尽量选择没有进入死循环的分支(因为彩云是笨比)

**请不要疯狂的续写下去……我也不知道会怎么样, 当然这只是建议**
"""
sv = uiPlugin(["caiyun", "彩云续写"], False, usage=sv_help)


@sv.ui_command("彩云续写", privileged=False)
async def caiyun_ai(session: CommandSession) -> None:
    text = re.search(r"《?(.*)》?(.*)", session.current_arg_text.strip())
    title = text.group(1)
    content = text.group(2)
    if not content:
        title = ""
        content = text.group(1)
    cy = Caiyun(uid=config.caiyun_token, title=title, content=[content])
    await session.send("正在续写中……(如果太久没发可能是风控了, 毕竟文章很长)")
    await cy.xuxie()
    while True:
        try:
            t = "".join(cy.content)
            x = re.search(r"[,，。.、？！?!]?(.*)$", t).group(1)
            ans = await session.aget(
                prompt=(
                    f"防刷屏,前文用……省略, 只显示最后一句\n"
                    f"分支1: 防刷屏, 前略……{x}{cy.temp_content[0]}\n\n"
                    f"分支2: 防刷屏, 前略……{x}{cy.temp_content[1]}\n\n"
                    f"分支3: 防刷屏, 前略……{x}{cy.temp_content[2]}\n"
                    f"{help_text}"
                ),
                arg_filters=[str.strip],
            )
            if ans == "1" or ans == "2" or ans == "3":
                await cy.select(int(ans))
            else:
                await session.send("由于错误的输入或是输入了结束续写, 续写已结束")
                break
            await cy.xuxie()

        except RuntimeError as e:
            logger.error(e)
            await session.finish(e)
    text = "".join(cy.content) + cy.temp_content[0]
    await session.finish("以下是你所有续写的总汇(默认加上了最后的分支1):\n" + text)


async def get_text(caiyun: Caiyun) -> str:
    return caiyun.temp_content[0]
