import ujson as json
from bs4 import BeautifulSoup
from soraha_utils import async_uiclient, logger


class Config:
    def __init__(self, proxy: dict = "", config_path: str = ""):

        if proxy:
            self.proxy = proxy
        else:
            self.proxy = {
                "http://": None,
                "https://": None,
            }

        self.config_path = config_path

        self.load()

    def dump(self) -> None:
        for i in self.config.values():
            i["name"] = list(set(i["name"]))
        with open(self.config_path, "w", encoding="utf_8") as f:
            json.dump(self.config, f, ensure_ascii=False, indent=4)

    def load(self):
        try:
            with open(self.config_path, "r", encoding="utf_8") as f:
                self.config = json.load(f)
        except Exception as e:
            self.config = {}
            logger.error(f"读取角色信息出现错误: {e}")
            with open(self.config_path, "w", encoding="utf_8") as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)


class Spider(Config):
    def __init__(self, proxy: dict = {}, config_path: str = ""):
        super().__init__(proxy, config_path)

    async def get_info(self) -> list:
        """
        自动爬取`碧蓝航线wiki-舰船定位筛选`页面,从中获取每个舰娘的信息

        Returns:
            list -> info中没有出现的, 被爬取的新舰船的名字
        """

        new_list = []
        async with async_uiclient(proxy=self.proxy) as cl:
            res = await cl.uiget(
                "https://wiki.biligame.com/blhx/%E8%88%B0%E5%A8%98%E5%AE%9A%E4%BD%8D%E7%AD%9B%E9%80%89"
            )
            soup = BeautifulSoup(res.text, "lxml")
            tb = soup.find_all("tr", attrs={"class": "divsort"})
            for i in tb:
                char = {
                    "name": "",
                    "game": {
                        "skill": [],
                    },
                    "info": {},
                }

                try:
                    char["name"] = [
                        i.contents[3].contents[3].contents[1].attrs["title"].strip()
                    ]
                except KeyError as e:
                    char["name"] = [
                        i.contents[3]
                        .contents[1]
                        .contents[0]
                        .attrs["data-cardurl"]
                        .strip()
                    ]

                if i.contents[1].text.strip() in self.config:
                    logger.info(
                        f"角色已存在, 跳过: [ {i.contents[1].text.strip()} ] {char['name']}"
                    )
                    continue
                logger.info(f"正在爬取: [ {i.contents[1].text.strip()} ] {char['name']}")

                try:
                    res = await cl.uiget(
                        "https://wiki.biligame.com/"
                        + i.contents[3].contents[3].contents[1].attrs["href"]
                    )
                except KeyError as e:
                    res = await cl.uiget(
                        "https://wiki.biligame.com/"
                        + i.contents[3].contents[3].contents[2].attrs["href"]
                    )

                soup1 = BeautifulSoup(res.text, "lxml")
                t = soup1.find_all("div", {"class": "wikibox-biginside"})

                skill = t[0].contents[1].contents[15].contents[1]

                # 头像
                char["game"]["image"] = (
                    t[0]
                    .contents[1]
                    .contents[1]
                    .contents[1]
                    .contents[2]
                    .contents[1]
                    .contents[0]
                    .attrs["srcset"]
                )

                # 类型
                char["game"]["type"] = (
                    t[0]
                    .contents[1]
                    .contents[1]
                    .contents[1]
                    .contents[2]
                    .contents[9]
                    .text.strip()
                )
                # 稀有度
                char["game"]["rarity"] = (
                    t[0]
                    .contents[1]
                    .contents[1]
                    .contents[1]
                    .contents[4]
                    .contents[3]
                    .text.strip()
                )
                # 阵营
                char["game"]["camp"] = (
                    t[0]
                    .contents[1]
                    .contents[1]
                    .contents[1]
                    .contents[4]
                    .contents[7]
                    .text.strip()
                )
                # 建造时间
                char["game"]["buildtime"] = (
                    t[0]
                    .contents[1]
                    .contents[1]
                    .contents[1]
                    .contents[6]
                    .contents[3]
                    .text.strip()
                )

                # 身份
                char["info"]["status"] = (
                    t[0]
                    .contents[3]
                    .contents[1]
                    .contents[1]
                    .contents[8]
                    .contents[3]
                    .text.strip()
                )
                # 性格
                char["info"]["temp"] = (
                    t[0]
                    .contents[3]
                    .contents[1]
                    .contents[1]
                    .contents[10]
                    .contents[3]
                    .text.strip()
                )
                # 关键词
                char["info"]["keyword"] = (
                    t[0]
                    .contents[3]
                    .contents[1]
                    .contents[1]
                    .contents[12]
                    .contents[3]
                    .text.strip()
                )
                # 持有物
                char["info"]["hold"] = (
                    t[0]
                    .contents[3]
                    .contents[1]
                    .contents[1]
                    .contents[14]
                    .contents[3]
                    .text.strip()
                )
                # 发色
                char["info"]["hair_color"] = (
                    t[0]
                    .contents[3]
                    .contents[1]
                    .contents[1]
                    .contents[16]
                    .contents[3]
                    .text.strip()
                )
                # 瞳色
                char["info"]["pupil_color"] = (
                    t[0]
                    .contents[3]
                    .contents[1]
                    .contents[1]
                    .contents[18]
                    .contents[3]
                    .text.strip()
                )
                # CV
                try:
                    char["info"]["cv"] = (
                        t[0]
                        .contents[3]
                        .contents[1]
                        .contents[1]
                        .contents[24]
                        .contents[1]
                        .contents[0]
                        .strip()
                    )
                except TypeError as e:
                    char["info"]["cv"] = (
                        t[0]
                        .contents[3]
                        .contents[1]
                        .contents[1]
                        .contents[24]
                        .contents[1]
                        .contents[0]
                        .text.strip()
                    )
                # 画师
                try:
                    char["info"]["illu"] = (
                        t[0]
                        .contents[3]
                        .contents[1]
                        .contents[1]
                        .contents[28]
                        .contents[1]
                        .contents[0]
                        .strip()
                    )
                except TypeError as e:
                    if (
                        t[0]
                        .contents[3]
                        .contents[1]
                        .contents[1]
                        .contents[28]
                        .contents[1]
                        .contents[0]
                        .text
                        == "+"
                    ):
                        char["info"]["illu"] = ""

                # 技能
                for index, value in enumerate(skill.contents):
                    if (
                        value == "\n"
                        or index == 0
                        or ("style" in value.attrs and value["style"] == "display:none")
                    ):
                        continue
                    char["game"]["skill"].append(value.contents[1].text.strip())

                self.config[i.contents[1].text.strip()]["game"]["image"] = (
                    t[0]
                    .contents[1]
                    .contents[1]
                    .contents[1]
                    .contents[2]
                    .contents[1]
                    .contents[0]
                    .attrs["srcset"]
                    .split(" ")[0]
                    .strip()
                )

                self.dump()
                new_list.append(i.contents[1].text.strip())
                logger.info("成功！")
        if new_list:
            await self.nickname()
        return new_list

    async def nickname(self) -> None:
        """
        自动爬取重樱和谐名页面, 更新名字
        """
        async with async_uiclient(proxy=self.proxy) as cl:
            res = await cl.uiget(
                "https://wiki.biligame.com/blhx/%E9%87%8D%E6%A8%B1%E8%88%B9%E5%90%8D%E7%A7%B0%E5%AF%B9%E7%85%A7%E8%A1%A8"
            )
            soup = BeautifulSoup(res.text, "lxml")

        tb = soup.find_all("tr", {"class": "Flour"})
        for i in tb:
            name = i.contents[3].text.strip()
            nickname = i.contents[1].contents[0].contents[0].text.strip()
            for x in self.config.values():
                if name in x["name"] and nickname not in x["name"]:
                    x["name"].append(nickname)
                    logger.info(f"成功更新 {name} 的反和谐名: {nickname}")
                    self.dump()
