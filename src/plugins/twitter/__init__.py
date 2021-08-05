import traceback
import nonebot
import tweepy
import os
import ujson
import asyncio
import httpx
from loguru import logger
from retrying import retry

from nonebot import on_command, CommandSession, MessageSegment, get_bot, scheduler

import config
from src.plugins.twitter.translate import baidu_translate as translate
from src.plugins.twitter.parser import sendmsg as ps_sendmsg
from src.Services import Service, Service_Master, GROUP_ADMIN

sv_help = """推特订阅 | 使用帮助
括号内的文字即为指令,小括号内为可选文字(是否必带请自行参照使用示例)
插件的权限问题:
    -> 由于推特上各种乱七八糟的加上存在r18内容
    -> 将会禁止除管理/群主/超级用户外的人订阅/修改或是取消订阅
[订阅推特 (推特id)] -> 订阅推特用户
    参数详解:
        推特id有两种,一种是名称,另一种是网址上的/@xxxxx的xxxxx,这里需要的是后者
    特别注意:
        订阅问题:
            -> 推特分为四种：发推/回复/转发/引用(转发+回复)
            -> 可以分别设置是否推送此类信息,为了防止刷屏,会默认关闭回复
            -> ↑尤其是a和b开始在推特不停回复交流的时候↑
    使用示例:
        订阅推特 ywwuyi
            -> 订阅成功
[设置订阅 (推特id)] -> 上方的特别注意中提到的,设置推送
    参数详解:
        这边推特id可以任一,拿碧蓝来说:
        -> アズールレーン公式
        -> azurlane_staff
        都是允许的
    特别注意:
        设置订阅后会要求你回复,请参照使用示例
        如果全关闭,将会询问你是否要取消订阅。
    使用示例:
        (箭头的信息为羽衣的回复)
        设置订阅 ywwuyi
        -> 目前的订阅状态是:
           1.发推 √
           2.回复 ×
           3.转发 √
           4.引用 ×
           请回复数字,将会反转设置,多个数字请用空格隔开
        1 2 4
        -> 设置成功,目前状态:
           1.发推 ×
           2.回复 √
           3.转发 √
           4.引用 √
    使用示例(其二):
        (箭头的信息为羽衣的回复)
        设置订阅 ywwuyi
        -> 目前的订阅状态是:
           1.发推 √
           2.回复 ×
           3.转发 √
           4.引用 ×
           请回复数字,将会反转设置,多个数字请用空格隔开
        1 3
        -> 将会关闭所有推送,是要取消订阅吗？(y/n)
        y
        -> 取消订阅成功
        n
        -> 设置成功,目前状态:
           1.发推 ×
           2.回复 ×
           3.转发 ×
           4.引用 ×
[取消推特订阅 (推特id)] -> 取消订阅某用户
    参数详解:
        id同上设置订阅,任一id即可
    使用示例:
        取消推特订阅 ywwuyi
        -> 取消成功
[查看推特订阅] -> 查看本群/私聊中所有的推特订阅
""".strip()
sv = Service(['twitter', '推特订阅'], sv_help, use_cacha_folder=True,
             permission_change=GROUP_ADMIN, permission_use=GROUP_ADMIN, priv_use=False)


bot = get_bot()

using = False

# tweepy api封装
auth = tweepy.OAuthHandler(config.API_key_for_Twitter,
                           config.API_secret_key_for_Twitter)
auth.set_access_token(config.Access_token_for_Twitter,
                      config.Access_token_secret_for_Twitter)
api = tweepy.API(auth, proxy=config.proxy, timeout=15)


subcribe_path = os.path.join(
    os.getcwd(), 'src', 'plugins', 'twitter', 'subcribe.json')
try:
    with open(subcribe_path, 'r', encoding='utf-8') as f:
        subcribe = ujson.load(f)
except FileNotFoundError:
    subcribe = {}
    with open(subcribe_path, 'w', encoding='utf-8') as f:
        ujson.dump(subcribe, f, ensure_ascii=False, indent=4)


@on_command('订阅推特')
async def subcribe_twitter(session: CommandSession):
    """订阅推特的主函数

    Args:
        session (CommandSession): bot封装的信息
    """
    stat = await Service_Master().check_permission('twitter', session.event)
    if not stat[0]:
        await session.finish(stat[3])
    tw_id = session.current_arg_text.strip()
    if not tw_id:
        await session.finish('羽衣不知道你要订阅谁哦')

    if session.event.detail_type == 'group':
        gid = session.event.group_id
        uid = None
    else:
        gid = None
        uid = session.event['user_id']
    try:
        user_info = await get_user(tw_id)
    except Exception:
        logger.error(f'请求推特用户id{tw_id}失败')
        await session.finish('获取该用户失败,请检查是否存在该id')

    try:
        res = await get_api(user_info['id'], 1000000000000000000)
        user_info['last_id'] = res[0]['id']
    except:
        user_info['last_id'] = 1000000000000000000

    if gid:
        if tw_id in subcribe:
            if str(gid) in subcribe[tw_id]['subcribe_group']:
                await session.finish('已经订阅过该用户了')
        else:
            subcribe[tw_id] = {
                'name': user_info['name'],
                'last_id': user_info['last_id'],
                'subcribe_group': {},
                'subcribe_user': {}
            }
        subcribe[tw_id]['subcribe_group'][str(gid)] = {
            'send': True,
            'reply': False,
            'retweet': True,
            'quote': True
        }
    else:
        if tw_id in subcribe:
            if str(uid) in subcribe[tw_id]['subcribe_user']:
                await session.finish('已经订阅过该用户了')
        else:
            subcribe[tw_id] = {
                'name': user_info['id'],
                'last_id': user_info['last_id'],
                'subcribe_group': {},
                'subcribe_user': {}
            }
        subcribe[tw_id]['subcribe_user'][str(uid)] = {
            'send': True,
            'reply': False,
            'retweet': True,
            'quote': True
        }
    with open(subcribe_path, 'w', encoding='utf-8') as f:
        ujson.dump(subcribe, f, ensure_ascii=False, indent=4)
    await session.finish(f"订阅成功!\n"
                         f"用户名称: {user_info['name']}\n"
                         f"用户简介: {user_info['description']}\n"
                         f"用户推特主页: {user_info['url']}")


@retry(stop_max_attempt_number=5)
async def get_user(tw_id: str) -> dict:
    """获取推特用户的信息

    Args:
        tw_id (str): 该用户的推特id

    Returns:
        dict: 用户信息
    """
    res = api.get_user(screen_name=tw_id)
    js = res._json
    data = {
        'id': js['screen_name'],
        'name': js['name'],
        'description': js['description'],
        'url': 'https://twitter.com/' + js['screen_name']
    }
    return data


@retry(stop_max_attempt_number=5)
async def get_api(user_id: str, tweet_id: int = 1000000000000000000) -> dict:
    """获取用户发送的推特

   Args:
        user_id(str): 用户推特的id
        tweet_id: 获取从since_id开始(之后)的推文

    Returns:
        dict: api传回的用户新推特的字典
    """
    tweet = []
    res = api.user_timeline(user_id, since_id=tweet_id, tweet_mode="extended")
    res = [x for x in res if x.id > tweet_id]
    if not res:
        return
    for tt in res:
        tweet.append(tt._json)
    return tweet


@on_command('设置订阅')
async def set_subcribe_states(session: CommandSession):
    """设置订阅的主函数

    Args:
        session (CommandSession): bot封装的信息
    """
    stat = await Service_Master().check_permission('twitter', session.event)
    if not stat[0]:
        await session.finish(stat[3])
    tw_id = session.current_arg_text.strip()
    if not tw_id:
        await session.finish('羽衣不知道你要设置谁的推送设定哦')

    if session.event.detail_type == 'group':
        gid = session.event.group_id
        uid = None
    else:
        gid = None
        uid = session.event['user_id']

    user_info = None
    user_id = None
    if gid:
        for x, y in subcribe.items():
            if tw_id == x or tw_id == y['name']:
                if str(gid) in y['subcribe_group']:
                    user_info = y['subcribe_group'][str(gid)]
                    user_id = x
                    break
    else:
        for x, y in subcribe.items():
            if tw_id == x or tw_id == y['name']:
                if str(uid) in y['subcribe_user']:
                    user_info = y['subcribe_user'][str(uid)]
                    user_id = x
                    break

    if not user_info:
        await session.finish('没有找到该用户!可能原因:\n还没有订阅过该用户！请先订阅\n输入有误,请使用[查看推特订阅]查看目标用户id')

    await session.apause('目前的订阅状态是:\n'
                         f"1.发推 {'√' if user_info['send'] else '×'}\n"
                         f"2.回复 {'√' if user_info['reply'] else '×'}\n"
                         f"3.转发 {'√' if user_info['retweet'] else '×'}\n"
                         f"4.引用 {'√' if user_info['quote'] else '×'}\n"
                         '请回复数字, 将会反转设置, 多个数字请用空格隔开')
    states = session.current_arg_text.split(' ')
    for i in states:
        if i == '1':
            user_info['send'] = not user_info['send']
        elif i == '2':
            user_info['reply'] = not user_info['reply']
        elif i == '3':
            user_info['retweet'] = not user_info['retweet']
        elif i == '4':
            user_info['quote'] = not user_info['quote']
        else:
            await session.finish(f'输入错误！请输入1，2，3，4的数字并用空格隔开,具体可发送help 推特订阅查看使用示例,最后请重新使用设置订阅 {tw_id}进行设定')
    if not (user_info['send'] or user_info['reply'] or user_info['retweet'] or user_info['quote']):
        await session.apause('将会关闭所有推送,是要取消订阅吗?(y/n)')
        if session.current_arg_text == 'y':
            await delect_subcribe(session)
        elif session.current_arg_text == 'n':
            if gid:
                subcribe[user_id]['subcribe_group'][str(gid)] = user_info
            else:
                subcribe[user_id]['subcribe_user'][str(uid)] = user_info
            with open(subcribe_path, 'w', encoding='utf-8') as f:
                ujson.dump(subcribe, f, ensure_ascii=False, indent=4)
            await session.finish('设置成功,目前状态:\n'
                                 f"1.发推 {'√' if user_info['send'] else '×'}\n"
                                 f"2.回复 {'√' if user_info['reply'] else '×'}\n"
                                 f"3.转发 {'√' if user_info['retweet'] else '×'}\n"
                                 f"4.引用 {'√' if user_info['quote'] else '×'}")
        else:
            if gid:
                subcribe[user_id]['subcribe_group'][str(gid)] = user_info
            else:
                subcribe[user_id]['subcribe_user'][str(uid)] = user_info
            with open(subcribe_path, 'w', encoding='utf-8') as f:
                ujson.dump(subcribe, f, ensure_ascii=False, indent=4)
            await session.finish('错误输入,默认为n,设置成功,目前状态:\n'
                                 f"1.发推 {'√' if user_info['send'] else '×'}\n"
                                 f"2.回复 {'√' if user_info['reply'] else '×'}\n"
                                 f"3.转发 {'√' if user_info['retweet'] else '×'}\n"
                                 f"4.引用 {'√' if user_info['quote'] else '×'}")
    else:
        if gid:
            subcribe[user_id]['subcribe_group'][str(gid)] = user_info
        else:
            subcribe[user_id]['subcribe_user'][str(uid)] = user_info
        with open(subcribe_path, 'w', encoding='utf-8') as f:
            ujson.dump(subcribe, f, ensure_ascii=False, indent=4)
        await session.finish('设置成功,目前状态:\n'
                             f"1.发推 {'√' if user_info['send'] else '×'}\n"
                             f"2.回复 {'√' if user_info['reply'] else '×'}\n"
                             f"3.转发 {'√' if user_info['retweet'] else '×'}\n"
                             f"4.引用 {'√' if user_info['quote'] else '×'}")


@on_command('取消推特订阅')
async def delect_subcribe(session: CommandSession):
    """取消推特订阅的主函数

    Args:
        session (CommandSession): bot封装的信息
    """
    stat = await Service_Master().check_permission('twitter', session.event)
    if not stat[0]:
        await session.finish(stat[3])
    tw_id = session.current_arg_text.strip()
    if not tw_id:
        await session.finish('羽衣不知道你要设置谁的推送设定哦')

    if session.event.detail_type == 'group':
        gid = session.event.group_id
        uid = None
    else:
        gid = None
        uid = session.event['user_id']

    found = False
    if gid:
        for x, y in subcribe.items():
            if tw_id == x or tw_id == y['name']:
                if str(gid) in y['subcribe_group']:
                    user_info = y
                    user_id = x
                    del subcribe[x]['subcribe_group'][str(gid)]
                    found = True
                    break
    else:
        for x, y in subcribe.items():
            if tw_id == x or tw_id == y['name']:
                if str(uid) in y['subcribe_user']:
                    user_info = y
                    user_id = x
                    del subcribe[x]['subcribe_user'][str(uid)]
                    found = True
                    break

    if not found:
        await session.finish('没有找到该用户!可能原因:\n还没有订阅过该用户！请先订阅\n输入有误,请使用[查看推特订阅]查看目标用户id')
    elif not subcribe[x]['subcribe_group'] and not subcribe[x]['subcribe_user']:
        del subcribe[x]
    else:
        with open(subcribe_path, 'w', encoding='utf-8') as f:
            ujson.dump(subcribe, f, ensure_ascii=False, indent=4)
        await session.finish('删除成功! 订阅用户信息:\n'
                             f'用户id: {user_id}\n'
                             f"用户名称: {user_info['name']}\n"
                             f"用户主页: {'https://twitter.com/' + user_id}")


@on_command('查看推特订阅', aliases=('查看所有推特订阅',))
async def get_all_subcribe(session: CommandSession):
    """查看所有推特订阅的主函数

    Args:
        session (CommandSession): bot封装的消息
    """
    stat = await Service_Master().check_permission('twitter', session.event)
    if not stat[0]:
        await session.finish(stat[3])

    if session.event.detail_type == 'group':
        gid = session.event.group_id
        uid = None
    else:
        gid = None
        uid = session.event['user_id']

    msg = []
    if gid:
        all_subc = [f"{y['name']}(id:{x})" for x, y in subcribe.items(
        ) if str(gid) in y['subcribe_group']]
        if not all_subc:
            await session.finish('本群没有订阅任何用户!')
    else:
        all_subc = [f"{y['name']}(id:{x})" for x, y in subcribe.items(
        ) if str(uid) in y['subcribe_user']]
        if not all_subc:
            await session.finish('你还没有订阅任何用户!')

    msg = '\n'.join(all_subc)
    await session.finish(f'总共订阅了{len(all_subc)}个用户:\n'
                         f"{msg}")


@retry(stop_max_attempt_number=5)
async def get_states(status_id: str) -> dict:
    """获取推文详细信息

    当a回复b时,api不返回b推文,此函数用于额外获取b的推文

    Args:
        status_id (str): 推文id

    Returns:
        dict: 封装好的推文信息
    """
    res = api.get_status(status_id, tweet_mode='extended')
    js = res._json
    res = await ps_sendmsg(js)
    data = {
        'name': res['senderid'],
        'text': res['text'],
        'seq': res['seq'],
        'isvideo': res['isvideo'],
        'reply_china': False,
        'lang': 'zh',
        'translate_result': res['translate_result']
    }
    if js['lang'] != 'zh' and js['lang'] != 'und':
        data['reply_china'] = True
        data['lang'] = js['lang']
    return data


@retry(stop_max_attempt_number=5)
async def dl_image(urls: list) -> MessageSegment:
    """下载推特上的图片,封装为CQ码返回

    Args:
        urls (list): 图片链接列表

    Returns:
        MessageSegment: CQ码
    """
    seq = []
    for url in urls:
        async with httpx.AsyncClient(proxies=config.proxies, timeout=15) as s:
            res = await s.get(url)
            if res.status_code != 200:
                raise RuntimeError
        path = os.path.join(config.res, 'cacha', 'twitter', url[-10:])
        with open(path, 'wb') as f:
            f.write(res.content)
        seq.append(MessageSegment.image(r'file:///' + path))
    return seq


async def sendmsg(msg: dict) -> dict:
    """将tweepy返回的api结果重新整理为需要的信息

    Args:
        msg (dict): tweepy返回的api result

    Returns:
        dict: 封装好的各种信息
    """
    data = {
        "senderid": msg["user"]["name"],
        "text": "",
        "have_img": False,
        "imgurl": [],
        "urls_old": [],
        "urls_new": [],
        "isvideo": False,
        "isreply": False,
        "replyuser": None,
        "replyseq": "",
        "replytext": "",
        "isRT": False,
        "RTuser": None,
        "RTtext": "",
        "isquote": False,
        "quoteuser": None,
        "quotetext": "",
        "quote_url_old": [],
        "quote_url_new": [],
        "quote_in_img": False,
        "quote_in_video": False,
        "quote_media_url": [],
        "lastid": msg["id"],
        "lang": msg["lang"],
        "replylang": "zh",
        "quotelang": "zh",
        "RTlang": "zh",
        "translate_result": "翻译错误",
        "reply_translate_result": "翻译错误",
        "quote_translate_result": "翻译错误",
        "no_china": False,
        "reply_in_not_china": False,
        "quote_in_not_china": False,
        "is_tweet": False
    }
    # 回复
    if msg["in_reply_to_status_id"] != None:
        data["isreply"] = True
        user_name = await get_states(msg['in_reply_to_status_id'])
        try:
            if user_name == "访问失败":
                data["replyuser"] = msg["in_reply_to_screen_name"]
            else:
                data["replyuser"] = user_name["name"]
                data["replyseq"] = user_name["seq"]
                data["replytext"] = user_name["text"]
                data["reply_in_not_china"] = user_name["reply_china"]
                data["replylang"] = user_name["lang"]
                data["isvideo"] = user_name["isvideo"]
                if user_name["lang"] != "zh":
                    data["reply_translate_result"] = user_name["translate_result"]
        except:
            pass
        data["text"] = msg["full_text"]
        try:
            if msg["entities"]["urls"]["media"]:
                if msg["entities"]["urls"]["media"]["type"] == "photo":
                    data["imgurl"].append(
                        msg["entities"]["media"][0]["media_url"])
                    data["have_img"] = True
                else:
                    data["isvideo"] = True
        except:
            pass
        try:
            for i in msg["entities"]["urls"]:
                data["urls_old"].append(i["url"])
                data["urls_new"].append(i["expanded_url"])
        except:
            pass
        try:
            if msg["extended_entities"]:
                for i in msg["extended_entities"]["media"]:
                    if i["type"] == "photo":
                        # data["imgurl"].append(i["media_url"])
                        data["imgurl"].append(i["media_url"])
                        data["have_img"] = True
                    else:
                        data["isvideo"] = True
        except:
            pass

    # 转推
    elif "retweeted_status" in msg:
        data["isRT"] = True
        data["RTlang"] = msg["retweeted_status"]["lang"]
        try:
            data["RTtext"] = msg["retweeted_status"]["full_text"]
        except:
            pass
        # data["RTuser"] = msg["full_text"][4:].split(":", 1)[0]
        data["RTuser"] = msg["retweeted_status"]["user"]["name"]
        try:
            if msg["retweeted_status"]["entities"]["urls"]["media"]:
                if msg["retweeted_status"]["entities"]["urls"]["media"][
                        "type"] == "photo":
                    data["imgurl"].append(msg["retweeted_status"]["entities"]
                                          ["media"][0]["media_url"])
                    data["have_img"] = True
                else:
                    data["isvideo"] = True
        except:
            pass
        try:
            for i in msg["retweeted_status"]["entities"]["urls"]:
                data["urls_old"].append(i["url"])
                data["urls_new"].append(i["expanded_url"])
        except:
            pass
        try:
            if msg["retweeted_status"]["extended_entities"]:
                for i in msg["retweeted_status"]["extended_entities"]["media"]:
                    if i["type"] == "photo":
                        data["imgurl"].append(i["media_url"])
                        data["have_img"] = True
                    else:
                        data["isvideo"] = True
        except:
            pass

    # 引用推文
    elif msg["is_quote_status"] == True:
        data["isquote"] = True
        data["senderid"] = msg["user"]["name"]
        try:
            data["quotetext"] = msg["quoted_status"]["full_text"]
            data["quoteuser"] = msg["quoted_status"]["user"]["name"]
            data["quotelang"] = msg["quoted_status"]["lang"]
        except:
            data['quotetext'] = '这条推文不可用。获取失败,可能原因:\n1.推文是私密推文\n2.推文刚好被删除了'
            data['quotelang'] = 'zh'
            try:
                data['quoteuser'] = msg['quoted_status_permalink']['expanded'].rsplit(
                    '/')[2]
            except:
                data['quoteuser'] = '未知'
        try:
            data["text"] = msg["full_text"]
        except:
            pass
        try:
            for i in msg["entities"]["urls"]:
                data["urls_old"].append(i["url"])
                data["urls_new"].append(i["expanded_url"])
        except:
            pass
        try:
            if msg["entities"]["urls"]["media"]:
                if msg["entities"]["urls"]["media"]["type"] == "photo":
                    data["imgurl"].append(
                        msg["entities"]["media"][0]["media_url"])
                    data["have_img"] = True
                else:
                    data["isvideo"] = True
        except:
            pass
        try:
            if msg["extended_entities"]:
                for i in msg["extended_entities"]["media"]:
                    if i["type"] == "photo":
                        data["imgurl"].append(i["media_url"])
                        data["have_img"] = True
                    else:
                        data["isvideo"] = True
        except:
            pass
        try:
            if msg["quoted_status"]["entities"]["urls"]["media"]:
                if msg["quoted_status"]["entities"]["urls"]["media"][
                        "type"] == "photo":
                    data["quote_media_url"].append(
                        msg["quoted_status"]["entities"]["media"][0]
                        ["media_url"])
                    data["quote_in_img"] = True
                else:
                    data["quote_in_video"] = True
        except:
            pass
        try:
            if msg["quoted_status"]["extended_entities"]:
                for i in msg["quoted_status"]["extended_entities"]["media"]:
                    if i["type"] == "photo":
                        data["quote_media_url"].append(i["media_url"])
                        data["quote_in_img"] = True
                    else:
                        data["quote_in_video"] = True
        except:
            pass
        try:
            for i in msg["quoted_status"]["entities"]["urls"]:
                data["quote_url_old"].append(i["url"])
                data["quote_url_new"].append(i["expanded_url"])
        except:
            pass

    # 发推
    else:
        try:
            data["text"] = msg["full_text"]
        except:
            pass
        try:
            if msg["entities"]["urls"]["media"]:
                if msg["entities"]["urls"]["media"]["type"] == "photo":
                    data["imgurl"].append(
                        msg["entities"]["media"][0]["media_url"])
                    data["have_img"] = True
                else:
                    data["isvideo"] = True
        except:
            pass
        try:
            if msg["extended_entities"]:
                for i in msg["extended_entities"]["media"]:
                    if i["type"] == "photo":
                        data["imgurl"].append(i["media_url"])
                        data["have_img"] = True
                    else:
                        data["isvideo"] = True
        except:
            pass
        try:
            for i in msg["entities"]["urls"]:
                data["urls_old"].append(i["url"])
                data["urls_new"].append(i["expanded_url"])
        except:
            pass

    # 去掉多余链接
    if data["isquote"] == True:
        data["text"] = data["text"][:-23]
    if data["text"] != None:
        if (data["isvideo"] == True or data["have_img"] == True and data["text"][-23:-10] == "https://t.co/") == True:
            data["text"] = data["text"][:-23]
    if data["RTtext"] != None:
        if (data["isvideo"] == True or data["have_img"] == True and data["RTtext"][-23:-10] == "https://t.co/") == True:
            data["RTtext"] = data["RTtext"][:-23]
    if data["quotetext"] != None:
        if (data["quote_in_video"] == True or data["quote_in_img"] == True and data["quotetext"][-23:-10] == "https://t.co/") == True:
            data["quotetext"] = data["quotetext"][:-23]

    # 替换链接
    try:
        i = 0
        for old in data["urls_old"]:
            data["text"] = data["text"].replace(old, data["urls_new"][i])
            i = i + 1
    except:
        pass
    try:
        i = 0
        for old in data["urls_old"]:
            data["RTtext"] = data["RTtext"].replace(old, data["urls_new"][i])
            i = i + 1
    except:
        pass
    try:
        i = 0
        for old in data["quote_url_old"]:
            data["quotetext"] = data["quotetext"].replace(
                old, data["quote_url_new"][i])
            i = i + 1
    except:
        pass

    # 去掉多余的@user/reply_link
    if data["isreply"] == True:
        try:
            data["text"] = data["text"].rsplit("https://t.co", 1)[0].strip()
        except:
            pass
        try:
            if f"@{msg['in_reply_to_screen_name']} " in data["text"]:
                data["text"] = data["text"].rsplit(
                    f"@{msg['in_reply_to_screen_name']} ", 1)[1]
        except:
            pass

    # 翻译
    if data["lang"] != "zh":
        data["no_china"] = True
        if data['text'] != "":
            try:
                data["translate_result"] = await translate(data['text'])
            except:
                pass
        elif data["isRT"] == True and data["RTtext"] != "":
            try:
                data["translate_result"] = await translate(data['RTtext'])
            except:
                pass
    if data["quotelang"] != "zh" and data["isquote"] == True and data["text"] != "":
        data["quote_in_not_china"] = True
        data["quote_translate_result"] = await translate(data['quotetext'])

    if data["isreply"] != True and data["isRT"] != True and data["isquote"] != True:
        data["is_tweet"] = True

    if data["text"] == "" and data["lang"] == "und":
        data["lang"] = "zh"
    if data["text"] == "" and data["RTlang"] == "und":
        data["RTlang"] = "zh"
    if data["text"] == "" and data["replylang"] == "und":
        data["replylang"] = "zh"
    if data["text"] == "" and data["quotelang"] == "und":
        data["quotelang"] = "zh"
    return data


async def check_user_update(data: dict) -> bool:
    """检查单独一个用户的推特,并自动推送

    Args:
        data (dict): subcribe中该用户的信息

    Returns:
        bool: 是否检查成功
    """
    for x, y in data.items():
        ndata = y
        ndata['id'] = x
    data = ndata
    try:
        res = await get_api(data['id'], data['last_id'])
    except:
        logger.error(f"检查{data['name']}(id:{data['id']})推特时发生错误")
        return [data['id'], data['last_id']]
    if not res:
        return [data['id'], data['last_id']]
    logger.info(f"获取到{data['name']}(id:{data['id']})的最新推文{len(res)}条")
    msg_id = []
    for msg in res:
        para = await sendmsg(msg)
        seq = await dl_image(para['imgurl']) if para['imgurl'] else ['']
        quote_seq = await dl_image(para['quote_media_url']) if para['quote_media_url'] else ['']
        msg_id.append(int(para['lastid']))
        link_for_tweet = 'https://twitter.com/' + \
            data['id'] + '/status/' + str(para['lastid'])

        # 推特更新的各种情况
        fatui_text = (f"{para['senderid']}推特更新\n{link_for_tweet}"
                      '\n================\n'
                      f"{para['senderid']}发送了推文:\n\n{para['text']}" +
                      ''.join([str(x) for x in seq if x]))
        is_RT_text = (f"{para['senderid']}推特更新\n{link_for_tweet}"
                      '\n================\n'
                      f"{para['senderid']}转发了{para['RTuser']}的推文:\n\n{para['RTtext']}" +
                      ''.join([str(x) for x in seq if x]))
        try:
            reply_text = (f"{para['senderid']}推特更新\n{link_for_tweet}"
                          '\n================\n'
                          f"{para['senderid']}回复了{para['replyuser']}的推文:"
                          f"\n======{para['replyuser']}的推文======\n"
                          f"{para['replytext']}" +
                          "".join([str(x) for x in para['replyseq']]) +
                          f"\n======{para['senderid']}的回复======\n"
                          f"{para['text']}" +
                          ''.join([str(x) for x in seq if x]))
        except:
            reply_text = (f"{para['senderid']}推特更新\n{link_for_tweet}"
                          '\n================\n'
                          f"{para['senderid']}回复了{para['replyuser']}的推文"
                          f"\n======{para['senderid']}的回复======\n{para['text']}" +
                          ''.join([str(x) for x in seq if x]))
        quote_text = (f"{para['senderid']}推特更新\n{link_for_tweet}"
                      '\n================\n'
                      f"{para['senderid']}引用了{para['quoteuser']}的推文:"
                      '\n======被引用推文======\n'
                      f"{para['quotetext']}" + "".join("%s" % a for a in quote_seq) +
                      f"\n======{para['senderid']}的回复======\n"
                      f"{para['text']}" +
                      ''.join([str(x) for x in seq if x]))
        not_china = f"\n======以下是翻译======\n{para['translate_result']}"
        not_china_reply_1 = f"\n======{para['replyuser']}推文的翻译======\n{para['reply_translate_result']}"
        not_china_reply_2 = f"\n======{para['senderid']}回复的翻译======\n{para['translate_result']}"
        not_china_quote_1 = f"\n======{para['quoteuser']}被引用推文的翻译======\n{para['quote_translate_result']}"
        not_china_quote_2 = f"\n======{para['senderid']}回复的翻译======\n{para['translate_result']}"
        is_video = f"\n================\n该推文可能有视频/gif,请点击链接查看"

        for group_id, group_status in data['subcribe_group'].items():
            # 发推
            if para["is_tweet"] == True and group_status['send']:
                if para["lang"] == "zh":
                    if para["isvideo"] == False:
                        await bot.send_group_msg(group_id=group_id, message=fatui_text)
                    else:
                        await bot.send_group_msg(group_id=group_id, message=fatui_text + is_video)
                else:
                    if para["isvideo"] == False:
                        await bot.send_group_msg(group_id=group_id, message=fatui_text + not_china)
                    else:
                        await bot.send_group_msg(group_id=group_id, message=fatui_text + not_china + is_video)
            # 回复
            elif para["isreply"] == True and group_status['reply']:
                if para["lang"] == "zh" and para["replylang"] == "zh":
                    if para["isvideo"] == False:
                        await bot.send_group_msg(group_id=group_id, message=reply_text)
                    else:
                        await bot.send_group_msg(group_id=group_id, message=reply_text + is_video)
                elif para["lang"] != "zh" and para["replylang"] == "zh":
                    if para["isvideo"] == False:
                        await bot.send_group_msg(group_id=group_id, message=reply_text + not_china_reply_1)
                    else:
                        await bot.send_group_msg(group_id=group_id, message=reply_text + not_china_reply_1 +
                                                 is_video)
                elif para["lang"] == "zh" and para["replylang"] != "zh":
                    if para["isvideo"] == False:
                        await bot.send_group_msg(group_id=group_id, message=reply_text + not_china_reply_2)
                    else:
                        await bot.send_group_msg(group_id=group_id, message=reply_text + not_china_reply_2 +
                                                 is_video)
                else:
                    if para["isvideo"] == False:
                        await bot.send_group_msg(group_id=group_id, message=reply_text + not_china_reply_1 +
                                                 not_china_reply_2)
                    else:
                        await bot.send_group_msg(group_id=group_id, message=reply_text + not_china_reply_1 +
                                                 not_china_reply_2 + is_video)
            # 转推
            elif para["isRT"] == True and group_status['retweet']:
                if para["RTlang"] == "zh":
                    if para["isvideo"] == False:
                        await bot.send_group_msg(group_id=group_id, message=is_RT_text)
                    else:
                        await bot.send_group_msg(group_id=group_id, message=is_RT_text + is_video)
                else:
                    if para["isvideo"] == False:
                        await bot.send_group_msg(group_id=group_id, message=is_RT_text + not_china)
                    else:
                        await bot.send_group_msg(group_id=group_id, message=is_RT_text + not_china + is_video)
            # 引用
            elif para["isquote"] == True and group_status['quote']:
                if para["lang"] == "zh" and para["quotelang"] == "zh":
                    if para["isvideo"] == False:
                        await bot.send_group_msg(group_id=group_id, message=quote_text)
                    else:
                        await bot.send_group_msg(group_id=group_id, message=quote_text + is_video)
                elif para["lang"] != "zh" and para["quotelang"] == "zh":
                    if para["isvideo"] == False:
                        await bot.send_group_msg(group_id=group_id, message=quote_text + not_china_quote_1)
                    else:
                        await bot.send_group_msg(group_id=group_id, message=quote_text + not_china_quote_1 +
                                                 is_video)
                elif para["lang"] == "zh" and para["quotelang"] != "zh":
                    if para["isvideo"] == False:
                        await bot.send_group_msg(group_id=group_id, message=quote_text + not_china_quote_2)
                    else:
                        await bot.send_group_msg(group_id=group_id, message=quote_text + not_china_quote_2 +
                                                 is_video)
                else:
                    if para["isvideo"] == False:
                        await bot.send_group_msg(group_id=group_id, message=quote_text + not_china_quote_1 +
                                                 not_china_quote_2)
                    else:
                        await bot.send_group_msg(group_id=group_id, message=quote_text + not_china_quote_1 +
                                                 not_china_quote_2 + is_video)
        for user_id, user_status in data['subcribe_user'].items():
            # 发推
            if para["is_tweet"] == True and user_status['send']:
                if para["lang"] == "zh":
                    if para["isvideo"] == False:
                        await bot.send_private_msg(user_id=user_id, message=fatui_text)
                    else:
                        await bot.send_private_msg(user_id=user_id, message=fatui_text + is_video)
                else:
                    if para["isvideo"] == False:
                        await bot.send_private_msg(user_id=user_id, message=fatui_text + not_china)
                    else:
                        await bot.send_private_msg(user_id=user_id, message=fatui_text + not_china + is_video)
            # 回复
            elif para["isreply"] == True and user_status['reply']:
                if para["lang"] == "zh" and para["replylang"] == "zh":
                    if para["isvideo"] == False:
                        await bot.send_private_msg(user_id=user_id, message=reply_text)
                    else:
                        await bot.send_private_msg(user_id=user_id, message=reply_text + is_video)
                elif para["lang"] != "zh" and para["replylang"] == "zh":
                    if para["isvideo"] == False:
                        await bot.send_private_msg(user_id=user_id, message=reply_text + not_china_reply_1)
                    else:
                        await bot.send_private_msg(user_id=user_id, message=reply_text + not_china_reply_1 +
                                                   is_video)
                elif para["lang"] == "zh" and para["replylang"] != "zh":
                    if para["isvideo"] == False:
                        await bot.send_private_msg(user_id=user_id, message=reply_text + not_china_reply_2)
                    else:
                        await bot.send_private_msg(user_id=user_id, message=reply_text + not_china_reply_2 +
                                                   is_video)
                else:
                    if para["isvideo"] == False:
                        await bot.send_private_msg(user_id=user_id, message=reply_text + not_china_reply_1 +
                                                   not_china_reply_2)
                    else:
                        await bot.send_private_msg(user_id=user_id, message=reply_text + not_china_reply_1 +
                                                   not_china_reply_2 + is_video)
            # 转推
            elif para["isRT"] == True and user_status['retweet']:
                if para["RTlang"] == "zh":
                    if para["isvideo"] == False:
                        await bot.send_private_msg(user_id=user_id, message=is_RT_text)
                    else:
                        await bot.send_private_msg(user_id=user_id, message=is_RT_text + is_video)
                else:
                    if para["isvideo"] == False:
                        await bot.send_private_msg(user_id=user_id, message=is_RT_text + not_china)
                    else:
                        await bot.send_private_msg(user_id=user_id, message=is_RT_text + not_china + is_video)
            # 引用
            elif para["isquote"] == True and user_status['quote']:
                if para["lang"] == "zh" and para["quotelang"] == "zh":
                    if para["isvideo"] == False:
                        await bot.send_private_msg(user_id=user_id, message=quote_text)
                    else:
                        await bot.send_private_msg(user_id=user_id, message=quote_text + is_video)
                elif para["lang"] != "zh" and para["quotelang"] == "zh":
                    if para["isvideo"] == False:
                        await bot.send_private_msg(user_id=user_id, message=quote_text + not_china_quote_1)
                    else:
                        await bot.send_private_msg(user_id=user_id, message=quote_text + not_china_quote_1 +
                                                   is_video)
                elif para["lang"] == "zh" and para["quotelang"] != "zh":
                    if para["isvideo"] == False:
                        await bot.send_private_msg(user_id=user_id, message=quote_text + not_china_quote_2)
                    else:
                        await bot.send_private_msg(user_id=user_id, message=quote_text + not_china_quote_2 +
                                                   is_video)
                else:
                    if para["isvideo"] == False:
                        await bot.send_private_msg(user_id=user_id, message=quote_text + not_china_quote_1 +
                                                   not_china_quote_2)
                    else:
                        await bot.send_private_msg(user_id=user_id, message=quote_text + not_china_quote_1 +
                                                   not_china_quote_2 + is_video)
    return [data['id'], max(msg_id)]


@scheduler.scheduled_job(
    'interval',
    minutes=1,
    # seconds=10,
)
async def check_multi_update():
    """定时任务: 检查推特的更新"""
    global using
    if not using:
        using = True
        logger.info('检查推特更新')
        try:
            coro = []
            for x, y in subcribe.items():
                coro.append(check_user_update({x: y}))
            res = await asyncio.gather(*coro, return_exceptions=True)
            for i in res:
                try:
                    if isinstance(i[1], int):
                        subcribe[i[0]]['last_id'] = i[1]
                except Exception:
                    try:
                        logger.error(f"获取{subcribe[i[0]]['name']}(id:{subcribe[i[0]]['id']})失败,自动跳过推文")
                    except:
                        continue
                del subcribe[i[0]]['id']
            success = [x for x in res if isinstance(x, list)]
            logger.info(
                f'检查结束,成功{len(success)}次,失败{len(subcribe) - len(success)}次')
        except:
            logger.error('检查时发生错误:' + traceback.format_exc())
        finally:
            with open(subcribe_path, 'w', encoding='utf-8') as f:
                ujson.dump(subcribe, f, ensure_ascii=False, indent=4)
            using = False
