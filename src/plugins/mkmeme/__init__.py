import os
from loguru import logger

from nonebot import on_command, MessageSegment, CommandSession

import config
from src.plugins.mkmeme import gosen_choen, luxun_say, jupai
from src.Services import Service, Service_Master, GROUP_ADMIN


meme_path = os.path.join(config.res, 'source', 'mkmeme')

sv_help = f"""表情制作 | 使用帮助
括号内的文字即为指令,小括号内为可选文字(是否必带请自行参照使用示例)
[表情制作] -> 制作表情(机器人会一句句询问的,回复即可)
    特别注意 -> 如果回复中出错,随时可以发送'结束'关闭制作,如果输入了不合法的回复会立刻关闭,需要重新使用该功能
    关闭问题 -> 在任何询问的时候单独输入'0'关闭,否则会一直问下去
    模板 -> 如果需要什么都没有模板,可以全部空回复,这样就不会有任何文字帖上去
表情示例:
1. 我想要5000兆日元
{MessageSegment.image(r'file:///' + os.path.join(meme_path,'gosen_choen','sample.png'))}
2. 鲁迅说
{MessageSegment.image(r'file:///' + os.path.join(meme_path,'luxun_say','sample.png'))}
3. 举牌
{MessageSegment.image(r'file:///' + os.path.join(meme_path,'jupai','sample.png'))}
""".strip()

sv = Service(['mkmeme', '表情制作'], sv_help, True, True, GROUP_ADMIN)


meme_list = {
    '1': '我想要5000兆日元',
    '2': '鲁迅说',
    '3': '举牌'
}

meme_help = f"""要制作的表情是？(回复数字或后面的文字即可)(输入0代表结束制作(直接结束询问,否则会一直问下去))
1. 我想要5000兆日元
2. 鲁迅说
3. 举牌
**为了防止刷屏以及避免风控,表情示例请查看使用帮助**
回复示例(下列两者任一):
    -> 1
    -> 我想要5000兆日元
""".strip()


@on_command('表情制作', aliases=('制作表情',))
async def mkmeme(session: CommandSession):
    """制作表情的主函数

    Args:
        session(CommandSession): bot封装的信息
    """
    stat = await Service_Master().check_permission('mkmeme', session.event)
    if not stat[0]:
        await session.finish(stat[3])

    await session.apause(meme_help)
    meme_number = session.current_arg_text.strip()
    if meme_number == '0':
        await session.finish('已结束制作')
    elif meme_number == '表情示例':
        await session.finish(sv_help)
    _meme_list = [x for x in meme_list.keys()] + \
        [x for x in meme_list.values()]
    if meme_number not in _meme_list:
        await session.finish('没有找到表情!请重新使用本功能制作')
    elif meme_number not in [x for x in meme_list.keys()]:
        meme_number = [x for x, y in meme_list.items() if meme_number == y][0]

    if meme_number == '1':
        # 我想要五千兆日元
        word_list = await process_gosen_choen(session)
        if not word_list:
            path = await gosen_choen.genImage()
        else:
            path = await gosen_choen.genImage(word_list[0], word_list[1])
        path = r'file:///' + path
        await session.finish(MessageSegment.image(path))

    elif meme_number == '2':
        # 鲁迅说
        word_list = await process_luxun_say(session)
        path = await luxun_say.process_pic(word_list[0], word_list[1])
        path = r'file:///' + path
        await session.finish(MessageSegment.image(path))

    elif meme_number == '3':
        # 举牌
        text = await process_jupai(session)
        path = await jupai.img(text)
        path = r'file:///' + path
        await session.finish(MessageSegment.image(path))


async def process_luxun_say(session: CommandSession) -> list[str, str]:
    """'鲁迅说'的处理函数,获取内容以及书名

    Args:
        session (CommandSession): bot的封装信息,传过来继续询问

    Returns:
        list[str,str]: 包含内容以及书名的列表
    """
    word_list = []

    await session.apause('请输入需要生成的内容(少于25个字)\n(输入0代表结束制作(直接结束询问,否则会一直问下去))')
    content = session.current_arg_text.strip()
    if content == '0':
        await session.finish('已结束制作')
    if len(content) >= 30:
        await session.finish('兄啊,这怎么写的下啊(半恼)')
    word_list.append(content)

    await session.apause('请输入书名(会在最后变成——鲁迅《(书名)》,输入0代表不需要书名)(7个字以内)')
    bookname = session.current_arg_text.strip()
    if len(bookname) >= 7:
        await session.finish('兄啊,这怎么写的下啊(半恼)')
    elif bookname == '0':
        bookname = None
    word_list.append(bookname)

    return word_list


async def process_gosen_choen(session: CommandSession) -> list[str, str]:
    """我好想要五千兆日元的处理函数,获取上下句

    Args:
        session (CommandSession): bot封装的信息,传过来继续询问

    Returns:
        list[str, str]: 包含上下句的列表
    """
    word_list = []

    await session.apause('请输入需要生成的上句(为了表情美观,空格等可以尽量去掉)(下句会在下一次询问中获取)\n(输入0代表结束制作(直接结束询问,否则会一直问下去))')
    upper = session.current_arg_text.strip()
    if upper == '0':
        await session.finish('已结束制作')
    if len(upper) >= 20:
        await session.finish('兄啊,这怎么写的下啊(半恼)')
    word_list.append(upper)

    await session.apause('请输入需要生成的下句(为了表情美观,空格等可以尽量去掉)\n(输入0代表结束制作(直接结束询问,否则会一直问下去))')
    downer = session.current_arg_text.strip()
    if downer == '0':
        await session.finish('已结束制作')
    if len(downer) >= 20:
        await session.finish('兄啊,这怎么写的下啊(半恼)')
    word_list.append(downer)

    return word_list


async def process_jupai(session: CommandSession) -> str:
    """举牌表情的获取函数

    Args:
        session (CommandSession): bot封装的消息，传过来询问

    Returns:
        str: 需要写入的句子
    """
    await session.apause('请输入需要生成的内容(少于25个字)\n(输入0代表结束制作(直接结束询问,否则会一直问下去))')
    text = session.current_arg_text.strip()
    if text == '0':
        await session.finish('已结束制作')
    if len(text) >= 30:
        await session.finish('兄啊,这怎么写的下啊(半恼)')

    return text
