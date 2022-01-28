import os
import json
from typing import Union
from bs4 import BeautifulSoup

import config
from soraha_utils import async_uiclient, async_uio, logger


class updater:
    def __init__(self) -> None:
        try:
            with open("./src/plugins/blhxwiki/image_list.json", "w") as f:
                self.dicts = json.load(f)
        except:
            self.dicts = {"强度榜": [], "一图榜": [], "秒伤榜": []}

    async def get_image(self, name: str) -> Union[bool, int]:
        if name not in self.dicts:
            return False
        else:
            return self.dicts[name]

    async def update_allinfo(self) -> None:
        PVE = await self.update_PVE()
        ZB = await self.update_zhuangbei()
        JP = await self.update_xiaosheng()
        with open("./src/plugins/blhxwiki/image_list.json", "w") as f:
            json.dump(self.dicts, f, ensure_ascii=False, indent=4)
        return (
            f"更新成功！\n"
            f"强度榜成功更新{PVE}张图\n"
            f"装备一图榜成功更新{ZB}张图！\n"
            f"装备秒伤榜成功更新{JP}张图！"
            f"可以使用blhxwiki (强度榜|一图榜|秒伤榜)查询！"
        )

    async def update_xiaosheng(self) -> None:
        soup = await self.get_page(
            "https://wiki.biligame.com/blhx/%E5%85%A8%E6%AD%A6%E5%99%A8%E5%AF%B9%E6%8A%A4%E7%94%B2%E8%A1%A5%E6%AD%A3%E4%B8%80%E8%A7%88"
        )
        js = soup.find_all("a", {"class": "image"})
        image_list = [x.contents[0].attrs["src"] for x in js]
        success = 0
        for index, i in enumerate(image_list):
            save_path = os.path.join(
                config.res, "source", "blhxwiki", f"装备秒伤榜_{index}.png"
            )
            try:
                self.dicts["秒伤榜"][index] = save_path
            except IndexError:
                self.dicts["秒伤榜"].append(save_path)
            await async_uio.save_file(
                type="url_image",
                save_path=f"./res/source/blhxwiki/装备秒伤榜_{index}.png",
                url=i,
                proxy=config.proxies_for_all,
            )
            success += 1
        return success

    async def get_page(self, url: str) -> BeautifulSoup:
        async with async_uiclient(proxy=config.proxies_for_all) as client:
            res = await client.uiget(url)
            soup = BeautifulSoup(res.text, "lxml")
        return soup

    async def update_zhuangbei(self):
        soup = await self.get_page(
            "https://wiki.biligame.com/blhx/%E8%A3%85%E5%A4%87%E4%B8%80%E5%9B%BE%E6%A6%9C"
        )
        res = soup.select("#mw-content-text > div > div.noresize > img")
        save_path = os.path.join(config.res, "source", "blhxwiki", f"一图榜.png")
        try:
            self.dicts["一图榜"][0] = save_path
        except IndexError:
            self.dicts["一图榜"].append(save_path)
        await async_uio.save_file(
            type="url_image",
            save_path=save_path,
            url=res[0].attrs["src"],
            proxy=config.proxies_for_all,
        )
        return 1

    async def update_PVE(self):
        """更新强度榜的函数

        Args:
            session (CommandSession): 发消息！
        """
        soup = await self.get_page(
            "https://wiki.biligame.com/blhx/PVE%E7%94%A8%E8%88%B0%E8%88%B9%E7%BB%BC%E5%90%88%E6%80%A7%E8%83%BD%E5%BC%BA%E5%BA%A6%E6%A6%9C"
        )
        js = soup.find_all("div", {"class": "floatnone"})
        image_list = [x.contents[0].contents[0].attrs["src"] for x in js]
        success = 0
        for index, i in enumerate(image_list):
            save_path = os.path.join(
                config.res, "source", "blhxwiki", f"强度榜_{index}.png"
            )
            try:
                self.dicts["强度榜"][index] = save_path
            except IndexError:
                self.dicts["强度榜"].append(save_path)
            await async_uio.save_file(
                type="url_image",
                save_path=f"./res/source/blhxwiki/强度榜_{index}.png",
                url=i,
                proxy=config.proxies_for_all,
            )
            success += 1
        return success
