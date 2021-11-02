import ujson
from pathlib import Path
from typing import Union
from os import path
from bs4 import BeautifulSoup

from nonebot import CommandSession, MessageSegment

import config
from soraha_utils import async_uiclient, logger


async def get_text(name: str):
    page_url = "https://wiki.biligame.com/blhx/" + name
    try:
        return await jianniang(page_url)
    except Exception as e:
        logger.debug(f"请求blhxwiki发生错误: {e}")
        try:
            return name + "\n" + await zhuangbei(page_url)
        except Exception as e:
            logger.debug(f"请求blhxwiki发生错误: {e}")
            try:
                return await fuzzy_search(name)
            except Exception as e:
                logger.debug(f"请求blhxwiki发生错误: {e}")
                return "没有找到你想要的"


async def jianniang(url: str):
    async with async_uiclient(proxy=config.proxies_for_all) as client:
        res = await client.uiget(url)
    soup = BeautifulSoup(res.text, "lxml")
    chara_info = soup.find_all("table", {"class": "wikitable sv-general"})[0].contents[
        1
    ]
    jianduikeji = soup.find_all("table", {"class": "wikitable sv-category"})[
        0
    ].contents[1]
    chara_attr = soup.find_all("table", {"class": "wikitable sv-performance"})[
        0
    ].contents[1]
    arms_info = soup.find_all("table", {"class": "wikitable sv-equipment"})[0].contents[
        1
    ]
    skills_info = soup.find_all("table", {"class": "wikitable sv-skill"})[0].contents[1]
    info = {
        "name": chara_info.contents[0].text.strip(),
        "rarity": chara_info.contents[4].contents[3].text.strip(),
        "build_time": chara_info.contents[6]
        .text.replace("\n", "")
        .replace("建造时间", "建造时间: "),
        "normal_drop": chara_info.contents[8].text.strip(),
        "special_drop": chara_info.contents[10].text.strip(),
        "fleet_get": jianduikeji.contents[4].contents[3].text.strip().replace("\n", ""),
        "fleet_get_extra": jianduikeji.contents[4].contents[7].text.strip(),
        "fleet_full": jianduikeji.contents[6]
        .contents[3]
        .text.strip()
        .replace("\n", ""),
        "fleet_full_extra": jianduikeji.contents[6].contents[5].text.strip(),
        "fleet_lv120": jianduikeji.contents[8]
        .contents[3]
        .text.strip()
        .replace("\n", ""),
        "fleet_lv120_extra": jianduikeji.contents[8].contents[5].text.strip(),
        "naijiu": chara_attr.contents[6].contents[3].text.strip(),
        "zhuangjia": chara_attr.contents[6].contents[7].text.strip(),
        "zhuangtian": chara_attr.contents[6].contents[11].text.strip(),
        "paoji": chara_attr.contents[8].contents[3].text.strip(),
        "leiji": chara_attr.contents[8].contents[7].text.strip(),
        "jidong": chara_attr.contents[8].contents[11].text.strip(),
        "fangkong": chara_attr.contents[10].contents[3].text.strip(),
        "hangkong": chara_attr.contents[10].contents[7].text.strip(),
        "xiaohao": chara_attr.contents[10].contents[11].text.strip(),
        "fanqian": chara_attr.contents[12].contents[3].text.strip(),
        "xinyun": chara_attr.contents[14].contents[3].text.strip(),
        "hangsu": chara_attr.contents[16].contents[3].text.strip(),
        "arm1_type": arms_info.contents[4].contents[3].text.strip(),
        "arm1_effi": arms_info.contents[4].contents[5].text.strip(),
        "arm2_type": arms_info.contents[6].contents[3].text.strip(),
        "arm2_effi": arms_info.contents[6].contents[5].text.strip(),
        "arm3_type": arms_info.contents[8].contents[3].text.strip(),
        "arm3_effi": arms_info.contents[8].contents[5].text.strip(),
        "skills": {},
    }
    for index, value in enumerate(skills_info.contents):
        if value == "\n" or index == 0 or not value.text.strip():
            continue
        info["skills"][value.contents[1].text.strip()] = value.contents[3].text.strip()
    text = (
        f"{info['name']}\n"
        f"======角色基本信息======\n"
        f"稀有度: {info['rarity']}\n"
        f"{info['build_time']}\n"
        f"======舰队科技======\n"
        f"获得: {info['fleet_get']}({info['fleet_get_extra']})\n"
        f"满星: {info['fleet_full']}({info['fleet_full_extra']})\n"
        f"lv120: {info['fleet_lv120']}({info['fleet_lv120_extra']})\n"
        f"======属性======\n"
        f"耐久: {info['naijiu']}\n"
        f"装甲: {info['zhuangjia']}\n"
        f"装填: {info['zhuangtian']}\n"
        f"炮击: {info['paoji']}\n"
        f"雷击: {info['leiji']}\n"
        f"机动: {info['jidong']}\n"
        f"防空: {info['fangkong']}\n"
        f"航空: {info['hangkong']}\n"
        f"消耗: {info['xiaohao']}\n"
        f"反潜: {info['fanqian']}\n"
        f"幸运: {info['xinyun']}\n"
        f"航速: {info['hangsu']}\n"
        f"======武器效率======\n"
        f"{info['arm1_type']}: {info['arm1_effi']}\n"
        f"{info['arm2_type']}: {info['arm2_effi']}\n"
        f"{info['arm3_type']}: {info['arm3_effi']}\n"
        f"======技能======\n"
    )
    for skill_name, descript in info["skills"].items():
        text += f"{skill_name}: {descript}\n"
    text += url
    return text.strip()


async def zhuangbei(url: str):
    async def zhuangbei_info(items, times=0) -> str:
        """狗一样的递归,为了防止以后自己看不懂下面说一下这函数在干嘛
        1. 判断是否为bs4独有的迷惑'\n',是则返回空字符串
        2.判断是否为wikitable class
            2.0:
                2.0.1: try是否为原来的equip数据,
                2.0.2: 如果是已经迭代过的equip,那么直接就是items.attrs['class'][0]
            2.1 是,迭代元素
                2.1.1: 判断是否为bs4独有的迷惑'\n',是则continue
                2.1.2: 判断是否为首次,是则加个冒号在后面等后续数据
                2.1.3: 不是首次的话那么就在原来的text中加入后续数据
            2.2 否,为equip
                2.2.1 迭代
        好 我写了一轮还是啥都不懂。
        干巴爹！未来的我一定能看懂的吧,捏~
        Args:
            items: items,wiki页面的ul(class:equip)
            times (int, optional): 递归次数,用于调整缩进. Defaults to 0.
        Returns:
            str: wikitable的text或是equip的text
        """
        if items == "\n":
            return ""
        if "适用舰种" in items.text:
            return ""
        tab = "  "
        point = "·"
        try:
            i_type = items.contents[1].attrs["class"][0]
        except:
            i_type = items.attrs["class"][0]
        if i_type == "wikitable":
            first_times = True
            info_text = ""
            for item in items.contents[1].contents[1].contents:
                if item == "\n":
                    continue
                if first_times:
                    info_text += item.text.strip().replace("\n", ": ")
                    first_times = False
                else:
                    info_text += f": {item.text.strip()}\n"
            if times != 0:
                return tab * times + point + info_text + "\n"
            else:
                return info_text + "\n"
        if i_type == "equip":
            text = ""
            for item in items.contents:
                text += await zhuangbei_info(item, times + 1)
            return text

    async with async_uiclient(proxy=config.proxies_for_all) as client:
        res = await client.uiget(url)
        soup = BeautifulSoup(res.text, "lxml")
        info = soup.find_all("ul", {"class": "equip"})
        info = info[0].contents[4:]
        text = ""
        for i in info:
            text += await zhuangbei_info(i)
        try:
            texts = soup.select(
                "#mw-content-text > div > div.row > div:nth-child(2) > div > div > p:nth-child(2)"
            )
            if not texts:
                texts = soup.select(
                    "#mw-content-text > div > div.row > div:nth-child(2) > div > div > div"
                )
            if texts[0].text.strip() == "备注":
                pass
            else:
                text += texts[0].text.replace("备注", "备注: ").strip()
        except:
            pass
        text = text.strip() + "\n" + url
        return text


async def fuzzy_search(name: str) -> Union[str, dict]:
    async with async_uiclient(proxy=config.proxies_for_all) as client:
        res = await client.uiget(
            f"https://searchwiki.biligame.com/blhx/index.php?search={name}&fulltext=1"
        )
    soup = BeautifulSoup(res.text, "lxml")
    if "找不到和查询相匹配的结果。" in soup.text:
        return "没有找到你想要的！"
    else:
        fuzzy = soup.select(
            "#mw-content-text > div.searchresults > ul > li:nth-child(1) > div.mw-search-result-heading > a"
        )
        return f"你是不是在找:{fuzzy[0].text.strip()}\n暂时只支持查询角色与装备"


async def update_info() -> dict:
    async with async_uiclient(proxy=config.proxies_for_all) as clent:
        res = await clent.uiget(
            "https://wiki.biligame.com/blhx/%E8%88%B0%E5%A8%98%E5%AE%9A%E4%BD%8D%E7%AD%9B%E9%80%89"
        )
        soup = BeautifulSoup(res.text, "lxml")
        try:
            p = Path("./info.json").open("r", encoding="utf-8")
            info = ujson.load(p)
        except:
            info = {}
        change = 0
        js = soup.find_all("div", {"class": "cpr_btn1"})
        for i in js:
            name = i.attrs["data-card"]
            if "改" in name:
                logger.debug(f"发现改造舰娘: {name},跳过")
                continue
            if name in info:
                continue
            info[name] = []
            change += 1
        logger.info(f"成功更新{len(info)}个舰娘信息,其中新增{change}个舰娘")
        p = Path("./info.json").open("w", encoding="utf-8")
        ujson.dump(info, p, ensure_ascii=False, indent=4)
    return info


async def update_photo(session: CommandSession):
    async with async_uiclient(proxy=config.proxies_for_all) as client:
        res = await client.uiget(
            f"https://wiki.biligame.com/blhx/PVE%E7%94%A8%E8%88%B0%E8%88%B9%E7%BB%BC%E5%90%88%E6%80%A7%E8%83%BD%E5%BC%BA%E5%BA%A6%E6%A6%9C"
        )
        soup = BeautifulSoup(res.text, "lxml")
        js = soup.find_all("div", {"class": "floatnone"})
        image_list = [x.contents[0].contents[0].attrs["src"] for x in js]
        name_list = []
        for index, i in enumerate(image_list):
            res = await client.uiget(i)
            name_list.append(f"./强度榜_{index}.png")
            with open(f"./res/source/blhxwiki/强度榜_{index}.png", "wb") as f:
                f.write(res.content)
    await session.finish("更新成功！")


async def send_qiangdubang(session: CommandSession):
    msg = []
    for i in range(0, 5):
        image_path = path.join(config.res, "source", "blhxwiki", f"强度榜_{i}.png")
        if not path.exists(image_path):
            await session.finish("没有找到图片缓存！请使用`blhxwiki 更新图片`来更新各种图片")
        msg.append(str(MessageSegment.image(f"file:///{image_path}")))
    await session.finish("".join(msg))
