import re
import ujson
import httpx
import asyncio
from hashlib import md5
from typing import Tuple
from loguru import logger
from retrying import retry
from bs4 import BeautifulSoup

from nonebot import MessageSegment

import config
from src.plugins.pixiv import utils


@retry
async def get_pixivion_index(return_photo: bool = True) -> list[dict]:
    """获取pixivison的首页,爬取标题,链接,信息和日期等

    Args:
        mode(bool): 用于检查是否需要返回图片(由于图片可能获取失败,等于并不固定,可能导致缓存md5加密对不上)

    Returns:
        list[dict]: [description]
    """
    # 请求部分
    headers = {
        'accept-language': 'zh-CN,zh-HK;q=0.9,zh;q=0.8,en;q=0.7'
    }
    url = 'https://www.pixivision.net/zh/'
    async with httpx.AsyncClient(proxies=config.proxies, headers=headers, timeout=25) as s:
        res = await s.get(url)
        if res.status_code != 200:
            raise RuntimeError

    soup = BeautifulSoup(res.text, 'lxml')
    sec = soup.find_all('article', class_='_article-card spotlight')
    types, urls, thums, titles, tags, dates = [], [], [], [], [], []

    # 解析部分
    # 类型 sec[0].contents[0].text
    # 文章链接 item.contents[0].contents[0].attrs['href']
    # 图片 item.contents[0].contents[0].contents[0].attrs['style']
    # 标题 item.contents[0].next_sibling.string
    # tags item.contents[0].next_sibling.next_sibling.contents[0].contents[x].text  # x为index索引,可能存在多个tags,下面使用len加range获取
    # 日期 item.contents[0].next_sibling.next_sibling.contents[1].string
    for item in sec:
        types.append(item.contents[0].text)
        urls.append(item.contents[0].contents[0].attrs['href'])
        thums.append(item.contents[0].contents[0].contents[0].attrs['style'])
        titles.append(item.contents[0].next_sibling.string)
        tags.append([item.contents[0].next_sibling.next_sibling.contents[0].contents[x].text for x in range(
            len(item.contents[0].next_sibling.next_sibling.contents[0].contents))])
        dates.append(
            item.contents[0].next_sibling.next_sibling.contents[1].string)

    # banner有额外一格置顶了,在这里额外获取一次
    sec = soup.find_all('article', class_='_article-eyecatch-card spotlight')
    types.append(sec[0].contents[0].text)
    urls.append(sec[0].contents[0].contents[0].contents[0].attrs['href'])
    thums.append(
        sec[0].contents[0].contents[0].contents[0].contents[0].attrs['style'])
    titles.append(
        sec[0].contents[0].contents[1].contents[0].contents[0].string)
    tags.append([sec[0].contents[0].contents[1].contents[0].contents[1].contents[x].string for x in range(
        len(sec[0].contents[0].contents[1].contents[0].contents[1]))])
    dates.append(
        sec[0].contents[0].contents[1].contents[0].next_sibling.contents[0].string)

    # url为:'background-image:  url(https://i.pximg.net/c/w1200_q80_a2_g1_u1_cr0:0.068:1:0.814/img-master/img/2020/05/23/20/50/24/81794812_p0_master1200.jpg)'
    # 因此使用正则库额外匹配
    # 目前发现除了传统i.pximg.net/xxx/img-master/img/xxxx外 还存在'https://i.pximg.net/imgaz/upload/xxxxxx/xxxx.jpg'的格式
    image_url = []
    for i in thums:
        url = re.findall(r'(/img/[\d\/_\w]*\.(?:png|jpg))', i)
        if url:
            url = 'https://i.pixiv.cat/img-original' + \
                url[0].replace('_master1200', '')
        else:
            try:
                url = re.findall(r'(https://i.pximg.net/imgaz/upload[\/\d\.\w]*)',
                                 i)[0].replace('i.pximg.net', 'i.pixiv.cat')
            except Exception:
                url = '无法获取'
        if url:
            image_url.append(url)

    # 封装字典
    vison_data = []
    for vison_type, url, title, tag, date, image_link in zip(types, urls, titles, tags, dates, image_url):
        vison_data.append({
            'type': vison_type,
            'vison_url': url,
            'vison_title': title,
            'tags': '，'.join(tag),
            'vison_date': date,
            'vison_seq': image_link
        })

    # 下载封面原图
    if return_photo:
        coros = [utils.dl_image(x) for x in image_url]
        thum = await asyncio.gather(*coros, return_exceptions=True)
        for index, res in enumerate(thum):
            if isinstance(res, Exception):
                continue
            else:
                res = MessageSegment.image(r'file:///' + res)
                vison_data[index]['vison_seq'] = str(res)

    return vison_data


@retry()
async def get_page_pixivison(url: str) -> Tuple[dict, dict]:
    """获取单个pixivison的详细页信息

    Args:
        url (str): 该页url

    Returns:
        Tuple[dict,dict]: 第一个字典为header,包含标题内文介绍等,第二个字典为正文,包括图片画师等
    """

    # 请求部分,headers作用为指定获取中文页面
    headers = {
        'accept-language': 'zh-CN,zh-HK;q=0.9,zh;q=0.8,en;q=0.7'
    }
    async with httpx.AsyncClient(proxies=config.proxies, headers=headers, timeout=25) as s:
        res = await s.get(url)
        if 'お探しのページが見つかりませんでした' in res.text:
            return 0, 0
        elif res.status_code != 200:
            raise RuntimeError

    soup = BeautifulSoup(res.text, 'lxml')
    # Header部分的解析,包含封面,标题,短文描述
    article = soup.find('article', class_='am__article-body-container')
    article_title = article.contents[0].contents[1].string
    article_description = article.contents[0].contents[1].next_sibling.text
    banner_url = article.contents[0].contents[4].contents[0].contents[0].attrs['src']
    vison_header = {
        'title': article_title,
        'desc': article_description,
        'banner': banner_url,
        'seq': ''
    }
    try:
        url = 'https://i.pixiv.cat' + \
            re.findall(r'(/img-master/img/.*)',
                       banner_url)[0].replace('_master1200', '')
        path = await utils.dl_image(banner_url)
        path = str(MessageSegment.image(r'file:///' + path))
        vison_header['seq'] = path
    except:
        vison_header['seq'] = '封面获取失败'

    # 正文部分解析,包含画作标题,画作链接,画师名字,画作id,画师id
    vison = soup.find('div', class_='am__body').find_all(
        'div', class_='am__work')
    titles, image_urls, image_ids, user_names, user_ids = [], [], [], [], []
    for item in vison:
        titles.append(
            item.contents[0].contents[0].contents[0].contents[0].next_element.contents[0].string)
        try:
            image_url = item.contents[0].next_sibling.contents[0].previous_element.contents[
                0].contents[0].contents[0].contents[1].attrs['src']
        except:
            try:
                image_url = item.contents[0].next_sibling.contents[
                    0].previous_element.contents[0].contents[0].contents[0].attrs['src']
            except:
                try:
                    image_url = item.contents[1].contents[0].contents[0].contents[0].attrs['src']
                except:
                    try:
                        image_url = item.contents[1].contents[0].contents[0].contents[0].contents[0].attrs['src']
                    except:
                        try:
                            image_url = re.findall(
                                r'(https://i.pximg.net/c/768x1200_80/img-master/img/[\d\/_\w].(?:jpg|png))', str(item))
                        except:
                            image_url = '无法获取原图链接'
        image_url = image_url.replace(
            'i.pximg.net/c/768x1200_80/img-master', 'i.pixiv.cat/img-original').replace('_master1200', '')
        image_urls.append(image_url)
        image_ids.append(re.findall(
            r'(\d+)', item.contents[0].contents[0].contents[0].contents[0].next_element.contents[0].contents[0].attrs['href'])[0])
        user_names.append(
            item.contents[0].contents[0].contents[0].contents[0].next_element.contents[0].next_sibling.contents[1].string)
        user_ids.append(re.findall(
            r'(\d+)', item.contents[0].contents[0].contents[0].contents[0].next_element.contents[0].next_sibling.contents[1].attrs['href'])[0])

    # 封装data
    vison_data = []
    for title, image_url, image_id, user_name, user_id in zip(titles, image_urls, image_ids, user_names, user_ids):
        vison_data.append({
            'image_name': title,
            'image_url': image_url,
            'image_id': image_id,
            'user_name': user_name,
            'user_id': user_id,
            'vison_seq': ''
        })

    # 下载原图
    coros = [utils.dl_image(x) for x in image_urls]
    thum = await asyncio.gather(*coros, return_exceptions=True)
    for index, res in enumerate(thum):
        if isinstance(res, Exception):
            vison_data[index]['vison_seq'] = vison_data[index]['image_url']
        else:
            res = MessageSegment.image(r'file:///' + res)
            vison_data[index]['vison_seq'] = str(res)

    return vison_header, vison_data


async def update_cacha(subcribe: dict, path: str) -> Tuple[dict, dict]:
    """更新pixivison缓存

    更新方法为将get_pixivion_index返回的字典整个md5加密变为缓存id

    Args:
        subcribe (dict): 订阅字典
        path (str): 字典保存的路径

    Returns:
        Tuple[dict,dict]: 返回两个字典,前者为更新完毕的subcribe,后者为没有在缓存中的新data
    """
    logger.info('正在尝试更新pixivison缓存')
    vison_index = await get_pixivion_index(False)
    md5_list = [md5(str(x).encode('utf-8')).hexdigest() for x in vison_index]

    new_list = [x for x, y in zip(
        vison_index, md5_list) if y not in subcribe['pixivison']['cacha']]

    subcribe['pixivison']['cacha'] = md5_list

    with open(path, 'w', encoding='utf-8') as f:
        ujson.dump(subcribe, f, ensure_ascii=False, indent=4)

    logger.info(f'pixivison缓存更新完毕,发现{len(new_list)}个未被缓存的新条目')

    if new_list:
        coros = [utils.dl_image(x['vison_seq']) for x in new_list]
        res = await asyncio.gather(*coros, return_exceptions=True)
        for index, res in enumerate(res):
            if isinstance(res, Exception):
                continue
            else:
                res = MessageSegment.image(r'file:///' + res)
                new_list[index]['vison_seq'] = res

    return subcribe, new_list
