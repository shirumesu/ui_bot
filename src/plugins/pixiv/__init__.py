import asyncio
import os
import re
import ujson
from loguru import logger

from nonebot import on_command, CommandSession, get_bot, scheduler

from src.Services import Service, Service_Master, GROUP_ADMIN, SUPERUSER
from src.plugins.pixiv import pixiv, pixivison
from src.ui_exception import Pixiv_api_Connect_Error


sv_help = """pixiv相关 | 使用帮助
括号内的文字即为指令,小括号内为可选文字(是否必带请自行参照使用示例)
前言: 所有功能获取的图片均为原图,由于qq的一些机制可能会没有下载原图选项,但确实是原图,请放心保存库哒赛！
[pixiv日榜 (数量)] -> 获取今日pixiv日榜
    参数详解:
        数量 -> 默认20张,可选范围为1-50,超出数量将不会响应
    特别注意:
        风控 -> 经过测试,请尽量维持在30张附近,否则很容易发不出来
        请求时间 -> 已经使用了异步的方式请求了,但榜单上本身就是好图,可能随时十几mb,请求时间依旧不算乐观(但如果太长时间发不出来那么请当做风控被吞了)
        榜单细分 -> 目前暂没有打算额外再细分男性榜,女性榜,原创榜等
        数量 -> 出现请求错误时会自动放弃请求图片,但是会有文字描述,如果
    使用示例:
        pixiv日榜
        -> (20张)
        pixiv日榜 50
        -> (50张)
        pixiv日榜 999
        -> (20张)
[pixiv周榜 (数量)] -> 同上
[pixiv月榜 (数量)] -> 同上
[pixivison (pid)] -> 获取pixivison
    参数详解:
        -> pid为pixivison的id,‘https://www.pixivision.net/zh/a/6375’中,id为6375
    使用示例:
        pixivison 6375
        -> (标题/封面/内页图片(略缩图)/文字等信息)
[订阅pixivison] -> 订阅pixivison
    特别注意:
        更新 -> 每天下午1:30会检查一次,更新会推送到所有订阅了的群中
[取消pixivison订阅] -> 不多解释了
[pixiv画师 (pid)] -> 获取pixiv画师封面的精选栏目中的图片
    参数详解:
        pid -> 画师pid,不多做说明
    特别注意:
        没有pickup -> 不是所有画师封面都有精选(可能要自己设置而他们没有吧),这种情况下会返回该画师最新的3张话(不满三张则所有)
    使用示例:
        pixiv画师 114514
[pixiv作品 (pid)] -> 获取pixiv作品(如果有多张会全部获取)
    参数详解:
        pid -> 懂得都懂
    特别注意:
        格式 -> 目前暂不支持获取gif动图
    使用示例:
        pixiv作品 123456
[订阅pixiv (pid)] -> 订阅pixiv画师
    参数详解:
        pid -> 不会真有人看到这里还没懂吧
    特别注意:
        更新 -> 每天中午12:50会检查一次
        分群 -> 各群/私聊独立分开订阅
        限额 -> 为了减少过高请求,当订阅量总数达到500时,将关闭私聊订阅,群聊不受影响(计划中···)
    使用示例:
        订阅pixiv
        -> 订阅成功 / 订阅失败(未找到pid)
[取消pixiv订阅 pid] -> 字面意思,都是老使用方法了,不再多做解释(**特别提醒**取消订阅可以使用查看pixiv订阅中的中文昵称,不一定需要id(虽然不太推荐就是了))
[查看pixiv订阅] -> 查看本群/私聊订阅的所有pixiv用户
[检查pixiv] -> 主动检查一次pixiv(超级用户限定指令)
[检查pixivison] -> 主动检查一次pixivison(同样超级用户限定)
**请不要频繁使用以上两个更新,而是等待每天的自动更新,谁也不知道请求多了pixiv有什么样的反爬手段**
======== Q & A =============
Q. Pixivison是什么?
A.官方解释:pixivision是将以漫画，小说，音乐为主的由创意而生的作品以及御宅文化向全世界推广的,每天都不会无聊的创作系媒体。
个人通俗解释:有人整理各种专题(例如打伞美少女,吸血鬼帅哥,穿雨衣,蛋糕甜食)等主题的推荐分享,以及一些采访等,几乎可等同于每天都能刷到的‘xxx插画推荐,快点进来看看吧’ 
"""
sv = Service(['pixiv', 'pixiv相关'], sv_help,
             use_cacha_folder=True, permission_change=GROUP_ADMIN)


bot = get_bot()

subcribe_path = os.path.join(
    os.getcwd(), 'src', 'plugins', 'pixiv', 'subcribe.json')
try:
    with open(subcribe_path, 'r', encoding='utf-8') as f:
        subcribe = ujson.load(f)
except FileNotFoundError:
    subcribe = {'pixiv': {}, 'pixivison': {
        'group': [], 'user': [], 'cacha': []}}
    with open(subcribe_path, 'w', encoding='utf-8') as f:
        ujson.dump(subcribe, f, ensure_ascii=False, indent=4)


check_subscribe = True
using_pixiv = False


@on_command('p站日榜', patterns=r'^pixiv[日周月]榜 ([1-5]\d?)$')
async def pixiv_rank(session: CommandSession):
    """获取pixiv日榜的主函数,同时处理日月周榜

    Args:
        session (CommandSession): bot封装的信息
    """
    stat = await Service_Master().check_permission('pixiv', session.event)
    if not stat[0]:
        await session.finish(stat[3])

    if '日' in session.current_arg_text.strip():
        mode = 'daily'
    elif '月' in session.current_arg_text.strip():
        mode = 'weekly'
    else:
        mode = 'monthly'

    num = [int(x) for x in re.findall(
        r'\d+', session.current_arg_text.strip())][0]

    try:
        im_data = await pixiv.get_rank(mode, num)
    except Pixiv_api_Connect_Error:
        await session.finish('Pixiv返回结果有误,可能原因:\n1.网太差,连接超时了\n2.pixiv反爬机制更新无法访问\n如果多次出现此错误请联系主人')
    msg = ''
    for i in im_data:
        msg += (f"{i['seq']}\n"
                f"图片上传日期:{i['date']}\n"
                f"图片标题:{i['title']}(id:{i['pid']})\n"
                f"画师名字:{i['user_name']}(id:{i['user_id']})\n"
                f"原图链接:{i['url']}\n"
                f"标签:{i['tags']}\n\n")
    await session.finish(msg.strip())


@on_command('pixivison')
async def pixivison_page(session: CommandSession):
    """获取pixivison单页的函数

    Args:
        session (CommandSession): bot封装的信息
    """
    stat = await Service_Master().check_permission('pixiv', session.event)
    if not stat[0]:
        await session.finish(stat[3])

    vision_id = session.current_arg_text.strip()
    if not re.match(r'\d+', vision_id):
        await session.finish('你的输入看上去有问题！请重新输入id,不知道pixivison的id是什么的话请查看使用帮助')

    url = 'https://www.pixivision.net/zh/a/' + vision_id
    vison_header, vison_data = await pixivison.get_page_pixivison(url)
    if not vison_header and not vison_data:
        await session.finish('你输入的id无效！请查看id是否存在(并非输入错误,但该id没有对应任何文章)')

    vison_msg = ''
    for i in vison_data:
        vison_msg += (f"画作标题: {i['image_name']}(id: {i['image_id']})\n"
                      f"画师名: {i['user_name']}(id: {i['user_id']})\n"
                      f"{i['vison_seq']}\n")
    msg = (f"标题: {vison_header['title']}\n"
           f"{vison_header['seq']}\n"
           f"{vison_header['desc']}\n\n"
           f"{''.join(vison_msg)}").strip()
    await session.send(msg)


@on_command('订阅pixivison')
async def subc_pixivison(session: CommandSession):
    """订阅pixivison的主函数

    Args:
        session (CommandSession): bot封装的信息
    """
    stat = await Service_Master().check_permission('pixiv', session.event)
    if not stat[0]:
        await session.finish(stat[3])

    if session.event.detail_type == 'group':
        gid = str(session.event.group_id)
        if gid in subcribe['pixivison']['group']:
            await session.finish('本群已经订阅了pixivison！')
        subcribe['pixivison']['group'].append(gid)
    else:
        uid = str(session.event.user_id)
        if uid in subcribe['pixivison']['user']:
            await session.finish('你已经订阅了pixivison了!')
        subcribe['pixivison']['user'].append(uid)

    with open(subcribe_path, 'w', encoding='utf-8') as f:
        ujson.dump(subcribe, f, ensure_ascii=False, indent=4)
    await session.finish('订阅成功！')


@on_command('取消pixivison订阅')
async def remove_pixivison(session: CommandSession):
    """取消pixivison的主函数

    Args:
        session (CommandSession): bot封装的信息
    """
    stat = await Service_Master().check_permission('pixiv', session.event)
    if not stat[0]:
        await session.finish(stat[3])

    if session.event.detail_type == 'group':
        gid = str(session.event.group_id)
        if gid not in subcribe['pixivison']['group']:
            await session.finish('本群还没有订阅过pixivison！')
        subcribe['pixivison']['group'].remove(gid)
    else:
        uid = str(session.event.user_id)
        if uid not in subcribe['pixivison']['user']:
            await session.finish('你还没有订阅过pixivison!')
        subcribe['pixivison']['user'].remove(uid)

    with open(subcribe_path, 'w', encoding='utf-8') as f:
        ujson.dump(subcribe, f, ensure_ascii=False, indent=4)
    await session.finish('取消成功！')


@on_command('pixiv作品')
async def pixiv_illuster(session: CommandSession):
    """获取pixiv作品的主函数

    Args:
        session (CommandSession): bot封装的信息
    """
    stat = await Service_Master().check_permission('pixiv', session.event)
    if not stat[0]:
        await session.finish(stat[3])

    pid = session.current_arg_text.strip()
    if not pid:
        await session.finish('你忘记输入作品id了！')

    try:
        data = await pixiv.get_image(pid)
    except RuntimeError:
        await session.finish('请求失败')
    except:
        await session.finish('未知原因导致请求错误(可能是网速太慢了.jpg')
    if not data:
        await session.finish('你输入的id不存在!作品可能已被删除或是你的输入有误！\n(p站上似乎有不少盗图的,一张图可能有好几个id,都被删除了,最后只有一个是真的原画师发的)')

    im_msg = ''
    for x, y in zip(data['url'], data['image_seq']):
        im_msg += f"原图链接: {x}\n{y}\n"
    msg = (f"图片标题: {data['title']}(id: {pid})\n"
           f"画师名字: {data['user_name']}(id: {data['user_id']})\n"
           f"上传日期: {data['date']}\n"
           f"标签: {data['tags']}\n{im_msg.strip()}")
    await session.finish(msg)


@on_command('pixiv画师')
async def pixiv_illuster(session: CommandSession):
    """获取pixiv画师的pickup的主函数

    Args:
        session (CommandSession): bot封装的信息
    """
    stat = await Service_Master().check_permission('pixiv', session.event)
    if not stat[0]:
        await session.finish(stat[3])

    pid = session.current_arg_text.strip()
    if not pid:
        await session.finish('你忘记输入画师id了！')

    try:
        res = await pixiv.get_pick_up(pid)
    except:
        await session.finish('发生错误,无法获取画师精选')

    msg = f"画师名字: {res[0]['user_name']}(id: {res[0]['user_id']})\n"
    im_msg = ''

    for i in res:
        for x, y in zip(i['url'], i['image_seq']):
            im_msg += f"原图链接: {x}\n{y}\n"
        msg += (f"图片标题: {i['title']}(id: {i['illust_id']})\n"
                f"上传日期: {i['date']}\n"
                f"标签: {i['tags']}\n"
                f"{im_msg}")
        im_msg = ''

    await session.finish(msg)


@on_command('订阅pixiv')
async def subc_illuster(session: CommandSession):
    """订阅pixiv的主函数

    Args:
        session (CommandSession): bot封装的信息
    """
    stat = await Service_Master().check_permission('pixiv', session.event)
    if not stat[0]:
        await session.finish(stat[3])

    pid = session.current_arg_text.strip()
    if not pid:
        await session.finish('你忘记输入画师id了！')

    if session.event.detail_type == 'group':
        gid = str(session.event.group_id)
        if pid in subcribe['pixiv'] and int(gid) in subcribe['pixiv'][pid]['group']:
            await session.finish('本群已经订阅过该画师了！')
    else:
        uid = str(session.event.user_id)
        if pid in subcribe['pixiv'] and int(uid) in subcribe['pixiv'][pid]['user']:
            await session.finish('你已经订阅过该画师了！')

    try:
        res = await pixiv.check_illust_list(pid)
    except:
        await session.finish('请求失败,可能是网太差了！')
    if isinstance(res, str):
        await session.finish('发生错误！请检查你的输入是否正确(或是羽衣的问题？)\napi返回错误信息:' + res)

    if session.event.detail_type == 'group':
        if pid in subcribe['pixiv']:
            subcribe['pixiv'][pid]['group'].append(session.event.group_id)
        else:
            subcribe['pixiv'][pid] = {
                'name': res['name'],
                'group': [session.event.group_id],
                'user': [],
                'illust_cacha': max(res['illust_id']) if res['illust_id'] else [],
                'manga_cacha': max(res['manga_id']) if res['manga_id'] else []
            }
    else:
        if pid in subcribe['pixiv']:
            subcribe['pixiv'][pid]['user'].append(session.event.user_id)
        else:
            subcribe['pixiv'][pid] = {
                'name': '',
                'group': [],
                'user': [session.event.user_id],
                'illust_cacha': max(res['illust_id']),
                'manga_cacha': max(res['manga_id']),
            }

    with open(subcribe_path, 'w', encoding='utf-8') as f:
        ujson.dump(subcribe, f, ensure_ascii=False, indent=4)

    await session.finish('订阅成功！')


@on_command('取消pixiv订阅')
async def del_illuster(session: CommandSession):
    """取消pixiv订阅的主函数

    Args:
        session (CommandSession): bot封装的信息
    """
    stat = await Service_Master().check_permission('pixiv', session.event)
    if not stat[0]:
        await session.finish(stat[3])

    pid = session.current_arg_text.strip()

    if session.event.detail_type == 'group':
        gid = str(session.event.group_id)
        if pid not in subcribe['pixiv'] or int(gid) not in subcribe['pixiv'][pid]['group']:
            pid = [x for x, y in subcribe['pixiv'].items() if y['name']
                   == pid][0]
            if not pid:
                await session.finish('本群还没有订阅过该画师！')
        if pid in subcribe['pixiv']:
            subcribe['pixiv'][pid]['group'].remove(int(gid))
    else:
        uid = str(session.event.user_id)
        if pid not in subcribe['pixiv'] or int(uid) not in subcribe['pixiv'][uid]['user']:
            pid = [x for x, y in subcribe['pixiv'].items() if y['name']
                   == pid][0]
            if not pid:
                await session.finish('你还没有订阅过该画师！')
        if pid in subcribe['pixiv']:
            subcribe['pixiv'][pid]['user'].remove(int(uid))

    if not subcribe['pixiv'][pid]['group'] and not subcribe['pixiv'][pid]['user']:
        del subcribe['pixiv'][pid]

    with open(subcribe_path, 'w', encoding='utf-8') as f:
        ujson.dump(subcribe, f, ensure_ascii=False, indent=4)
    await session.finish('取消成功！')


@on_command('查看pixiv订阅')
async def check_subcribe_pixiv_list(session: CommandSession):
    stat = await Service_Master().check_permission('pixiv', session.event)
    if not stat[0]:
        await session.finish(stat[3])

    if session.event.detail_type == 'group':
        gid = str(session.event.group_id)
        illuster_list = [[x, y] for x, y in subcribe['pixiv'].items(
        ) if 'group' in y and int(gid) in y['group']]
        msg = f'本群一共订阅了{len(illuster_list)}个画师:\n'

    else:
        uid = str(session.event.user_id)
        illuster_list = [[x, y] for x, y in subcribe['pixiv'].items(
        ) if 'user' in y and int(uid) in y['user']]
        msg = f'你一共订阅了{len(illuster_list)}个画师:\n'

    for i in illuster_list:
        msg += f"{i[1]['name']}(id: {i[0]})\n"

    await session.finish(msg)


@on_command('检查pixivison')
async def _(session: CommandSession):
    stat = await Service_Master().check_permission('pixiv', session.event, SUPERUSER)
    if not stat[0]:
        await session.finish(stat[3])

    await sche_check_pixivison()


@on_command('检查pixiv')
async def _check(session: CommandSession):
    stat = await Service_Master().check_permission('pixiv', session.event, SUPERUSER)
    if not stat[0]:
        await session.finish(stat[3])

    await sche_check_pixiv()


@scheduler.scheduled_job(
    'cron',
    hour=13,
    minute=30
)
async def sche_check_pixivison():
    logger.info('开始检查pixivison更新')
    if not subcribe['pixivison']['group'] and not subcribe['pixivison']['user']:
        await pixivison.update_cacha(subcribe, subcribe_path)
        logger.info('没有发现任何订阅信息,检查结束')
        return
    subcribes, new_list = await pixivison.update_cacha(subcribe, subcribe_path)
    for vison_item in new_list:
        msg = (f"检查到pixivison更新\n"
               f"标题: {vison_item['vison_title']}\n"
               f"更新日期: {vison_item['vison_date']}\n"
               f"推荐类型: {vison_item['type']}\n"
               f"标签: {vison_item['tags']}\n"
               f"文章链接: https://www.pixivision.net{vison_item['vison_url']}\n"
               f"{vison_item['vison_seq']}\n"
               f"感兴趣的话可以发送pixivison (id)获取该页面哦,不知道id是什么请查看使用帮助(发送‘使用帮助 pixiv相关’)")
        for gid in subcribe['pixivison']['group']:
            await bot.send_group_msg(group_id=gid, message=msg)
        for uid in subcribe['pixivison']['user']:
            await bot.send_private_msg(user_id=uid, message=msg)
    logger.info('检查结束')


@scheduler.scheduled_job(
    'cron',
    hour=12,
    minute=50
)
async def sche_check_pixiv():
    logger.info('开始检查pixiv画师更新')
    if not subcribe['pixivison']['group'] and not subcribe['pixivison']['user']:
        logger.info('没有发现任何订阅信息,检查结束')
        return
    pid = [pixiv.check_illust_list(x) for x in subcribe['pixiv'].keys()]
    res = await asyncio.gather(*pid, return_exceptions=True)
    for illust_list, illuster in zip(res, subcribe['pixiv'].values()):
        if isinstance(illust_list, Exception):
            continue
        new_illust_list = [int(x) for x in illust_list['illust_id'] if int(
            x) > illuster['illust_cacha']]
        new_manga_list = [int(x) for x in illust_list['manga_id'] if int(
            x) > illuster['manga_cacha']]
        if not new_illust_list and not new_manga_list:
            continue
        new_list = new_illust_list + new_manga_list
        coros = [pixiv.get_image(str(x)) for x in new_list]
        res = await asyncio.gather(*coros, return_exceptions=True)
        for index, i in enumerate(res):
            if isinstance(i, Exception):
                for gid in illuster['group']:
                    await bot.send_group_msg(group_id=gid, message=f"检测到{illuster['name']}(id: {i['user_id']})更新\n图片获取失败,id: {new_list[index]}")
                    logger.error(
                        f"检查{illuster['name']}(id: {i['user_id']})的更新失败:{str(i)}")
                continue
            im_data = ''
            for x, y in zip(i['url'], i['image_seq']):
                im_data += f'原图链接: {x}\n{y}\n'
            msg = (f"检测到{illuster['name']}(id: {i['user_id']})更新\n"
                   f"标题: {i['title']}(id: {i['illust_id']})\n"
                   f"标签: {i['tags']}\n"
                   f"{im_data}")
            for gid in illuster['group']:
                await bot.send_group_msg(group_id=gid, message=msg)
            for uid in illuster['user']:
                await bot.send_private_msg(user_id=uid, message=msg)
        illuster['illust_cacha'] = max(new_illust_list)
        illuster['manga_cacha'] = max(new_manga_list)
    with open(subcribe_path, 'w', encoding='utf-8') as f:
        ujson.dump(subcribe, f, ensure_ascii=False, indent=4)
    logger.info('检查完毕')
