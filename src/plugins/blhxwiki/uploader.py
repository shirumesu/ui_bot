import os

from bs4 import BeautifulSoup
from nonebot import MessageSegment

from config import proxies_for_all, res
from soraha_utils import async_uiclient, logger


class RANK_IMG:
    def __init__(self) -> None:
        self.path = os.path.join(res, "source", "blhxwiki")
        self.RP = {
            "认知觉醒榜": {
                "selector": [
                    "#mw-content-text > div > dl:nth-child(14) > dd:nth-child(1) > a > img",
                    "#mw-content-text > div > dl:nth-child(14) > dd:nth-child(2) > a > img",
                ]
            },
            "装备一图榜": {
                "selector": ["#mw-content-text > div > dl:nth-child(17) > dd > a > img"]
            },
            "萌新推荐榜": {
                "selector": [
                    "#mw-content-text > div > ul:nth-child(20) > li:nth-child(1) > div > div.thumb > div > a > img",
                    "#mw-content-text > div > ul:nth-child(20) > li:nth-child(2) > div > div.thumb > div > a > img",
                ]
            },
            "兑换推荐榜": {
                "selector": ["#mw-content-text > div > dl:nth-child(23) > dd > a > img"]
            },
            "研发推荐榜": {
                "selector": ["#mw-content-text > div > dl:nth-child(26) > dd > a > img"]
            },
            "改造推荐榜": {
                "selector": ["#mw-content-text > div > dl:nth-child(29) > dd > a > img"]
            },
            "跨队推荐榜": {
                "selector": ["#mw-content-text > div > dl:nth-child(32) > dd > a > img"]
            },
            "打捞表": {
                "selector": [
                    "#mw-content-text > div > ul:nth-child(35) > li:nth-child(1) > div > div.thumb > div > a > img",
                    "#mw-content-text > div > ul:nth-child(35) > li:nth-child(2) > div > div.thumb > div > a > img",
                ]
            },
        }

    async def get_ph(
        self,
        url: str = "https://wiki.biligame.com/blhx/%E4%BA%95%E5%8F%B7%E7%A2%A7%E8%93%9D%E6%A6%9C%E5%90%88%E9%9B%86",
        selector: str = None,
        p_name: str = None,
    ):
        if not selector and p_name:
            selector = self.RP[p_name]["selector"]
        try:
            async with async_uiclient(proxy=proxies_for_all) as cl:
                res = await cl.uiget(url)
                soup = BeautifulSoup(res.text, "lxml")
                im_msg = []
                for index, sc in enumerate(selector):
                    ph = soup.select(sc)
                    ph_res = await cl.uiget(ph[0].attrs["src"])
                    with open(
                        os.path.join(self.path, p_name + f"{index}.jpg"), "wb"
                    ) as f:
                        f.write(ph_res.content)
                    im_msg.append(
                        MessageSegment.image(
                            r"file:///"
                            + os.path.join(self.path, p_name + f"{index}.jpg")
                        )
                    )
            return im_msg

        except Exception as e:
            logger.warning(f"获取{p_name}失败!错误:{repr(e)}")
            im_msg = []
            for index, sc in enumerate(selector):
                p = os.path.join(self.path, p_name + f"{index}.jpg")
                if os.path.exists(p):
                    im_msg.append(MessageSegment.image("file:///" + p))
            if im_msg:
                return im_msg
            else:
                return "无法获取图片，本地未发现离线图片"

    def get_p_name(self, p_name: str):
        return False if self.RP.get(p_name) is None else True
