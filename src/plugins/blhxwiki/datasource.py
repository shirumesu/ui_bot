from typing import Union
import lxml
from bs4 import BeautifulSoup
from nonebot.command import CommandSession
import config
from soraha_utils import async_uiclient, logger, retry


async def get_page(name: str):
    page_url = "https://wiki.biligame.com/blhx/" + name
    async with async_uiclient(proxy=config.proxies_for_all) as client:
        res = await client.uiget(page_url)
    return await parser_charater_page(res.text)


async def get_result(session: CommandSession, name: str) -> Union[str, dict]:
    try:
        res = await get_page(name)
        if not res:
            raise IndexError
        return res
    except:
        res = await fuzzy_search(name)
        if not res:
            await session.finish("没有找到你想要的！")
        else:
            await session.finish(f"你是不是在找:{res}\n暂时只支持查询角色")


@retry(logger=logger)
async def parser_charater_page(res: str) -> dict:
    soup = BeautifulSoup(res, "lxml")
    try:
        chara_info = soup.find_all("table", {"class": "wikitable sv-general"})[
            0
        ].contents[1]
    except IndexError:
        raise
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
    charas_info = {
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
        charas_info["skills"][value.contents[1].text.strip()] = value.contents[
            3
        ].text.strip()
    return charas_info


@retry()
async def fuzzy_search(name):
    async with async_uiclient(proxy=config.proxies_for_all) as client:
        res = await client.uiget(
            f"https://searchwiki.biligame.com/blhx/index.php?search={name}&fulltext=1"
        )

    soup = BeautifulSoup(res.text, "lxml")
    if "找不到和查询相匹配的结果。" in soup.text:
        return
    else:
        fuzzy = soup.select(
            "#mw-content-text > div.searchresults > ul > li:nth-child(1) > div.mw-search-result-heading > a"
        )
        return fuzzy[0].text.strip()
