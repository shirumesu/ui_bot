from aiocqhttp.exceptions import Error
import httpx
import time
import asyncio
from retrying import retry

from nonebot import MessageSegment

import config
from src.plugins.pixiv import utils
from src.ui_exception import Pixiv_api_Connect_Error


@retry()
async def get_rank(mode: str, num: int) -> list[dict]:
    """请求pixiv榜单的函数

    Args:
        mode (str): 日榜daily/周榜weekly/月榜monthly
        num (int): 数量(1-50)

    Returns:
        list[dict]: 一个包含图片标题与id,排名,画师名称与id,原图链接以及tags的列表,请求失败的返回请求失败字符串
    """
    url = 'https://www.pixiv.net/ranking.php'
    param = {
        'mode': mode,
        'p': 1,
        'format': 'json'
    }
    async with httpx.AsyncClient(proxies=config.proxies, params=param, timeout=25) as s:
        res = await s.get(url)
        if res.status_code != 200:
            raise Pixiv_api_Connect_Error
    js = res.json()
    im_data = []
    for index, x in enumerate(js['contents']):
        if index < num:
            im_data.append({
                'rank': x['rank'],
                'date': x['date'],
                'title': x['title'],
                'pid': x['illust_id'],
                'user_name': x['user_name'],
                'user_id': x['user_id'],
                'tags': '，'.join(x['tags']),
                'url': x['url'].replace('i.pximg.net/c/240x480/img-master', 'i.pixiv.cat/img-original').replace('_master1200', ''),
                'seq': ''
            })
        else:
            break

    coros = [utils.dl_image(x['url']) for x in im_data]
    res = await asyncio.gather(*coros, return_exceptions=True)
    for result, item in zip(res, im_data):
        if isinstance(result, Exception):
            item['seq'] = '请求失败'
        else:
            item['seq'] = str(MessageSegment.image(r'file:///' + result))
    return im_data


@retry()
async def get_image(pid: str) -> dict:
    """获取单个pid的图片全图(包括p2p3等)

    Args:
        pid (str): 该图片的pid

    Returns:
        dict: 包含图片信息,例如画师id,图片标题,原图链接等的字典
    """
    header = {
        'accept-language': 'zh-CN,zh-HK;q=0.9,zh;q=0.8,en;q=0.7'
    }
    async with httpx.AsyncClient(proxies=config.proxies, headers=header, timeout=25) as s:
        res = await s.get('https://www.pixiv.net/ajax/illust/' + pid)
        if '该作品已被删除，或作品ID不存在。' in res.text:
            return None
        elif res.status_code != 200:
            raise RuntimeError
    js = res.json()['body']
    count = int(js['pageCount'])
    title = js['title']
    tags = '，'.join([f"{x['tag']}({x['translation']['en']})" for x in js['tags']['tags']
                    if 'translation' in x] + [f"{x['tag']}" for x in js['tags']['tags'] if 'translation' not in x])
    user_name = js['userName']
    user_id = js['userId']
    date = js['createDate'][:-6]
    date = time.strptime(date, r"%Y-%m-%dT%H:%M:%S")
    date = time.strftime(r'%Y-%m-%d  %H:%M:%S', date)
    url = [js['urls']['original'].replace('i.pximg.net', 'i.pixiv.cat')]
    if count != 1:
        for i in range(1, count):
            urlp = url[0].replace('_p0', f'_p{i}')
            url.append(urlp)
    coros = [utils.dl_image(x) for x in url]
    res = await asyncio.gather(*coros, return_exceptions=True)
    seq_list = []
    for i in res:
        if isinstance(res, (Error, Exception)):
            seq_list.append('图片获取失败')
            continue
        path = MessageSegment.image(r'file:///' + i)
        seq_list.append(str(path))
    data = {
        'title': title,
        'illust_id': pid,
        'date': date,
        'user_id': user_id,
        'user_name': user_name,
        'tags': tags,
        'url': url,
        'image_seq': seq_list
    }
    return data


@ retry()
async def check_illust_list(uid: str) -> dict:
    """检查单个用户的画作list

    Args:
        uid (str): 画师uid

    Returns:
        dict: 包含图片id以及漫画id的字典
    """
    url = f'https://www.pixiv.net/ajax/user/{uid}/profile/top?lang=zh'
    async with httpx.AsyncClient(proxies=config.proxies, timeout=25) as s:
        res = await s.get(url)
        try:
            js = res.json()
            if js['error']:
                return js['message']
        except:
            raise RuntimeError
        if res.status_code != 200:
            await asyncio.sleep(5)
            raise RuntimeError
    js = res.json()['body']
    if js['illusts'] and js['manga']:
        illust_id = [int(x) for x in js['illusts'].keys()]
        manga_id = [int(x) for x in js['manga'].keys()]
    else:
        if js['manga']:
            illust_id = []
            manga_id = [int(x) for x in js['manga'].keys()]
        if js['illusts']:
            illust_id = [int(x) for x in js['illusts'].keys()]
            manga_id = []
    return {
        'name': js['illusts'][str(illust_id[0])]['userName'],
        'illust_id': illust_id,
        'manga_id': manga_id
    }


@ retry()
async def get_pick_up(uid: str) -> list[dict]:
    """获取画师封面的pick_up(精选)图片

    Args:
        uid (str): 画师uid

    Returns:
        list[dict]: 图片的详细信息
    """
    url = f'https://www.pixiv.net/ajax/user/{uid}/profile/all?lang=zh'
    async with httpx.AsyncClient(proxies=config.proxies, timeout=25) as s:
        res = await s.get(url)
        if res.status_code != 200:
            raise RuntimeError
    js = res.json()['body']['pickup']
    if not js or (js[0]['type'] == 'fanbox' and len(js) == 1):
        js = res.json()['body']['illusts']
        illust_id = [x for x in js.keys()]
        if len(illust_id) > 3:
            illust_id = illust_id[:3]
    else:
        illust_id = [x['id'] for x in js if x['type'] == 'illust']
    coros = [get_image(x) for x in illust_id]
    res = await asyncio.gather(*coros, return_exceptions=True)
    pick_up_data = []
    for i in res:
        if isinstance(i, Exception):
            continue
        pick_up_data.append(i)
    return pick_up_data
