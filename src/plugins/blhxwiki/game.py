from io import BytesIO
import os
from PIL import Image
import random
import uuid
import config
from nonebot import CommandSession, MessageSegment
from asyncio import sleep
from soraha_utils import logger, async_uiclient

from typing import TypeVar, Union

Game = TypeVar("Game", bound="Game")


class Game_Master:
    def __init__(self, char_info) -> None:
        self.game = {}
        self.config = char_info

    async def start_game(self, session: CommandSession, Game_type) -> None:
        try:
            if not session.event.group_id:
                await session.finish("发生未知错误!或许你正在私聊玩游戏?请不要私聊使用!")
        except Exception as e:
            logger.error(f"猜舰娘游戏建立发生错误: {e}")
            await session.finish("发生未知错误!或许你正在私聊玩游戏?请不要私聊使用!")

        if await self.get_game(session.event.group_id):
            await session.finish("该群已经有游戏正在进行了!")

        if Game_type == "info":
            self.game[session.event.group_id] = Game(self.config, self)
            await self.game[session.event.group_id].guess_info(session)
        if Game_type == "avatar":
            self.game[session.event.group_id] = Game(self.config, self)
            await self.game[session.event.group_id].guess_avatar(session)

    def end_game(self, gid) -> None:
        del self.game[gid]

    async def get_game(self, gid) -> Union[Game, None]:
        return self.game[gid] if gid in self.game else None


class Game(Game_Master):
    def __init__(self, config, Game_Master) -> None:
        self.config = config
        self.GM = Game_Master
        self.ansing = False

    async def guess_avatar(self, session: CommandSession):
        self.char = random.choice(list(self.config.values()))
        self.image = self.char["game"]["image"]
        self.path_cropped = (
            os.path.join(config.res, "cacha", "blhxwiki", str(uuid.uuid4())) + ".png"
        )
        self.path_image = (
            os.path.join(config.res, "cacha", "blhxwiki", str(uuid.uuid4())) + ".png"
        )
        self.winner = ""

        for i in self.char["name"]:
            if i[-1] == "改":
                self.char["name"].append(i[:-1])
        self.ans = self.char["name"]

        async with async_uiclient(proxy=config.proxies_for_all) as cl:
            res = await cl.uiget(self.image)

        with open(self.path_image, "wb") as f:
            f.write(res.content)

            self.image_cv = Image.open(self.path_image)
            w, h = self.image_cv.size
            w = random.randint(0, w - 32)
            h = random.randint(0, h - 32)
            self.image_cv = self.image_cv.crop((w, h, w + 32, h + 32))

            self.image_cv.save(self.path_cropped)
        self.message_image = MessageSegment.image("file:///" + self.path_image)
        self.cropped_img = MessageSegment.image("file:///" + self.path_cropped)

        await session.send(
            "请猜猜图片中的舰娘是谁!(头像可能截的地方有点阴间导致辨识度低,如果是这样那 那我也没辙)\n"
            + self.cropped_img
            + "\n30秒后揭晓答案"
        )
        await sleep(30)
        if not self.winner:
            self.GM.end_game(session.event.group_id)
            await session.finish(
                f"真可惜！没人猜对！答案是{self.char['name'][0]}\n{self.message_image}"
            )

    async def bingo(self, text: str):
        text = text.strip()
        u_text = text.upper()
        d_text = text.lower()
        return (
            True
            if (text.strip() in self.ans or u_text in self.ans or d_text in self.ans)
            else False
        )

    async def guess_info(self, session: CommandSession):
        self.char = random.choice(list(self.config.values()))
        self.image = self.char["game"]["illust"]
        self.file_name = str(uuid.uuid4()) + ".png"
        self.path = os.path.join(config.res, "cacha", "blhxwiki", self.file_name)

        for i in self.char["name"]:
            if i[-1] == "改":
                self.char["name"].append(i[:-1])

        if "技能改造技能改造技能" in self.char["game"]["skill"]:
            self.char["game"]["skill"].remove("技能改造技能改造技能")

        self.ans = self.char["name"]

        self.game_info = [
            f"她的技能名为: {' & '.join([x for x in self.char['game']['skill']])}",
            f"她的舰船类型为: {self.char['game']['type']}",
            f"她的稀有度为: {self.char['game']['rarity']}",
            f"她的阵营为: {self.char['game']['camp']}",
            f"她的建造时间为: {self.char['game']['buildtime']}",
        ]

        self.char_info = []
        if self.char["info"]["status"]:
            self.char_info.append(f"她的身份为: {self.char['info']['status']}")
        if self.char["info"]["temp"]:
            self.char_info.append(f"她的阵营为: {self.char['info']['temp']}")
        if self.char["info"]["keyword"]:
            self.char_info.append(f"她的关键词为: {self.char['info']['keyword']}")
        if self.char["info"]["hold"]:
            self.char_info.append(f"她的持有物为: {self.char['info']['hold']}")
        if self.char["info"]["hair_color"] and self.char["info"]["pupil_color"]:
            self.char_info.append(
                f"她的发色为: {self.char['info']['hair_color']} & 瞳色为: {self.char['info']['pupil_color']}"
            )
        if self.char["info"]["cv"]:
            self.char_info.append(f"她的cv为: {self.char['info']['cv']}")
        if self.char["info"]["illu"]:
            self.char_info.append(f"她的画师为: {self.char['info']['illu']}")

        text = (
            f"欢迎来到紧张刺激的厨力大比拼!(?)\n"
            f"接下来我将每 6 秒说一次提示!\n"
            f"提示总共由随机的 3 个游戏属性(技能名|舰船类型|稀有度|阵营|建造时间) 以及\n"
            f"随机的 3 个角色信息(身份|性格|关键词|持有物|瞳色&发色|cv|画师) 组成\n"
            f"一共 42 秒作答时间!如果都没猜对就公布谜底!\n"
            f"====特别注意====\n"
            f"由于舰娘别名繁多, 请尽量使用公式名(和谐|非和谐皆可)\n"
            f"有别名没有录入的, 可以使用 添加舰娘别名 公式名 别名手动录入, 具体请查看使用帮助\n"
            f"游戏开始!"
        )

        async with async_uiclient(proxy=config.proxies_for_all) as cl:
            res = await cl.uiget(self.image)

        with open(self.path, "wb") as f:
            f.write(res.content)
        self.message_image = MessageSegment.image("file:///" + self.path)
        await session.send(text)

        # 答案 DEBUG用
        # await session.send(self.ans[0])

        self.winner = ""
        self.game_or_info = "game"
        self.time = 0

        while not self.winner and self.time < 6:
            if self.game_or_info == "game":
                t = random.choice(self.game_info)
                await session.send(t)
                self.game_or_info = "info"
                self.game_info.remove(t)
            else:
                t = random.choice(self.char_info)
                await session.send(t)
                self.game_or_info = "game"
                self.char_info.remove(t)
            self.time += 1
            await sleep(6.5)
        if self.time == 6 and not self.winner:
            self.GM.end_game(session.event.group_id)
            await session.finish(f"很遗憾没人猜对!正确答案: {self.ans[0]}\n{self.message_image}")
