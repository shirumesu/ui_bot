import os
import random
import re
import aiohttp
from aiohttp_proxy import ProxyConnector
import string
from io import BytesIO
from bs4 import BeautifulSoup
from nonebot import MessageSegment
import httpx
from aiohttp import FormData
from retrying import retry
import config


@retry
async def dl_src(url) -> BytesIO:
    """获取发送的等待被搜索图片

    Args:
        url ([type]): 该图片的链接

    Raises:
        RuntimeError: 触发retry多次尝试下载

    Returns:
        BytesIO: 图片内容
    """
    async with httpx.AsyncClient(proxies=config.proxies, timeout=15) as s:
        res = await s.get(url)
        if res.status_code != 200:
            raise RuntimeError

    return BytesIO(res.content)


@retry
async def get_search(content) -> str:
    """上传图片搜索

    Args:
        content (BytesIO): 图片的bytes

    Raises:
        RuntimeError: 用于触发retry

    Returns:
        str: 返回页面的源码(request.text)
    """
    url = 'https://upload.e-hentai.org/image_lookup.php'
    if config.proxies['http']:
        conn = ProxyConnector(config.proxies['http'])
    else:
        conn = None
    data = FormData()
    data.add_field(name='sfile', value=content,
                   content_type='image/jpeg', filename='0.jpg')
    data.add_field(name='f_sfile', value='search')
    data.add_field(name='fs_similar', value='on')
    async with aiohttp.ClientSession(connector=conn) as s:
        async with s.post(url, data=data) as res:
            if res.status != 200:
                raise RuntimeError
            html = await res.text()
    return html


@retry
async def parser(html: str) -> list:
    """解析页面

    Args:
        html (str): 返回页面的源码

    Returns:
        list: 最先的3个搜图结果(不满3个则返回所有,没有结果则返回str)
    """
    if 'No hits found' in html:
        return '没有找到符合的本子!'
    soup = BeautifulSoup(html, 'lxml').find_all(
        'table', class_='itg gltc')[0].contents
    all_list = []
    for index, item in enumerate(soup):
        if index == 0:
            continue
        elif index > 3:
            break
        imdata = {
            'type': item.find('div', class_=re.compile(r'cn ct\d')).string,
            'title': item.find('div', class_='glink').string,
            'link': item.find('td', class_='gl3c glname').contents[0].attrs['href'],
            'page_count': item.find('td', class_='gl4c glhide').contents[1].string,
            'im_seq': ''
        }
        imdata['im_seq'] = await dl_image(imdata['link'])
        all_list.append(imdata)
    return all_list


@retry
async def dl_image(url: str) -> str(MessageSegment):
    """访问作品链接获取封面

    Args:
        url (str): 作品的链接地址

    Raises:
        RuntimeError: 触发retry
        RuntimeError: 触发retry

    Returns:
        str(MessageSegment): 字符串类型的图片CQ码
    """
    async with httpx.AsyncClient(proxies=config.proxies) as s:
        res = await s.get(url)
        if res.status_code != 200:
            raise RuntimeError
        soup = BeautifulSoup(res.text, 'lxml')
        url = soup.select('#gd1 > div')
        url = re.findall(r'url\((.*?)\)', url[0].attrs['style'])[0]
        res = await s.get(url)
        if res.status_code != 200:
            raise RuntimeError

    filename = ''.join(random.sample(
        string.ascii_letters + string.digits, 8)) + '.png'
    save_path = os.path.join(config.res, 'cacha', 'search_image', filename)
    with open(save_path, 'wb') as f:
        f.write(res.content)

    return str(MessageSegment.image(r'file:///' + save_path))
