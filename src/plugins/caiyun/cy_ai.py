"""
本文件内容大多参考自: https://github.com/MeetWq/nonebot-plugin-caiyunai
感谢 MeetWq 佬的付出…
"""
from typing import *

from config import proxies_for_all
from soraha_utils import async_uiclient


class Caiyun:
    def __init__(
        self,
        uid: str,
        title: str,
        content: List[str],
        mid: str = "60094a2a9661080dc490f75a",
        branchid: str = "",
        lang: str = "zh",
        nodeid: List[str] = [],
        nid: str = "",
        ostype: str = "",
        status: str = "http",
        storyline: bool = False,
    ) -> None:
        """彩云小梦的请求类, 参数来自于彩云小梦ai续写的post参数

        Args:
            uid (str): 自己账号的uid
            title(str): 标题
            content (List[str]): List[0] -> 需要续写的原文, List[1:] ->续写的内容
            mid (str, optional): 小梦ai的id. Defaults to "60094a2a9661080dc490f75a"(小梦0号)
            branchid (str, optional): 含义未知. Defaults to "".
            lang (str, optional): 语言,默认为'zh'. Defaults to "zh".
            nodeid (List[str], optional): 含义未知. Defaults to [].
            nid (str, optional): 含义未知. Defaults to "".
            ostype (str, optional): 推测为系统类型, 但post居然不需要填写. Defaults to "".
            status (str, optional): 推测为访问类型, 默认为"http". Defaults to "http".
            storyline (bool, optional): 含义未知(我甚至在网页版都找不到怎么让他变成true). Defaults to False.
        """
        self.uid = uid
        self.title = title
        self.content = content
        self.mid = mid
        self.bid = branchid
        self.lang = lang
        self.nodes = nodeid
        self.nid = nid
        self.ostype = ostype
        self.status = status
        self.storyline = storyline

        # 分支content
        self.temp_content = []
        # 分支node
        self.temp_node = []

    async def caiyun_clean(self) -> None:
        """初始化这个类, 为了应付奇奇怪怪的问题"""
        self.title = ""
        self.content = ""
        self.mid = ""
        self.bid = ""
        self.lang = ""
        self.nodes = ""
        self.nid = ""
        self.ostype = ""
        self.status = ""
        self.storyline = ""

        # 分支content
        self.temp_content = ""
        # 分支node
        self.temp_node = ""

    async def xuxie(self):
        if not self.nid:
            await self.novel_save()
        if len(self.nodes) != 1:
            await self.add_node()
        await self.novel_ai()

    async def select(self, num) -> None:
        self.nodes.append(self.temp_node[num - 1])
        self.content.append(self.temp_content[num - 1])

    async def novel_save(self):
        """我也不知道是用来干嘛的, 人官方网页版那么干了 我也就那么发post……

        Raises:
            RuntimeError: 访问发生错误时抛出信息, 可直接发出来
        """
        url = f"https://if.caiyunai.com/v2/novel/{self.uid}/novel_save"
        js = {
            "lang": self.lang,
            "nodes": self.nodes,
            "ostype": self.ostype,
            "text": "".join(self.content),
            "title": self.title,
        }
        async with async_uiclient(proxy=proxies_for_all, request_json=js) as cl:
            res = await cl.uipost(url)
            res = res.json()
            if res["msg"] == "ok" and (err := await self.check_status(res)) is True:
                self.nid = res["data"]["nid"]
                self.bid = res["data"]["novel"]["branchid"]
                self.nodes.append(res["data"]["novel"]["firstnode"])
            else:
                raise RuntimeError(f"访问彩云ai发生错误: {res['msg']}\n推测: {err}")

    async def add_node(self):
        """我也不知道是用来干嘛的, 人官方网页版那么干了 我也就那么发post……

        Raises:
            RuntimeError: 访问发生错误时抛出信息, 可直接发出来
        """
        url = f"https://if.caiyunai.com/v2/novel/{self.uid}/add_node"
        js = {
            "choose": self.nodes[-1],
            "lang": self.lang,
            "nid": self.nid,
            "nodeids": self.nodes,
            "ostype": self.ostype,
            "value": self.content[:-1],
        }
        async with async_uiclient(proxy=proxies_for_all, request_json=js) as cl:
            res = await cl.uipost(url)
            res = res.json()
            if res["msg"] == "ok" and (err := await self.check_status(res)) is True:
                return
            else:
                raise RuntimeError(f"访问彩云ai发生错误: {res['msg']}\n推测: {err}")

    async def novel_ai(self):
        """我也不知道是用来干嘛的, 人官方网页版那么干了 我也就那么发post……

        Raises:
            RuntimeError: 访问发生错误时抛出信息, 可直接发出来
        """
        url = f"https://if.caiyunai.com/v2/novel/{self.uid}/novel_ai"
        js = {
            "branchid": self.bid,
            "content": "".join(self.content),
            "lang": self.lang,
            "lastnode": self.nodes[-1],
            "mid": self.mid,
            "nid": self.nid,
            "ostype": self.ostype,
            "status": self.status,
            "storyline": self.storyline,
            "title": self.title,
            "uid": self.uid,
        }
        async with async_uiclient(proxy=proxies_for_all, request_json=js) as cl:
            res = await cl.uipost(url)
            res = res.json()
            if res["msg"] == "ok" and (err := await self.check_status(res)) is True:
                self.temp_node = [x["nodeid"] for x in res["data"]["nodes"]]
                self.temp_content = [x["content"] for x in res["data"]["nodes"]]
            else:
                raise RuntimeError(f"访问彩云ai发生错误: {res['msg']}\n推测: {err}")

    async def check_status(self, res: dict) -> Union[bool, str]:
        """对返回结果的status值进行检查,

        Args:
            res (dict): 返回结果的json格式

        Returns:
            Union[bool, str]: bool -> True, 没有任何问题; str -> 错误信息
        """
        stu = res["status"]
        if stu == 0:
            return True
        elif stu == -1:
            return ""
        elif stu == -6:
            return "账号已被封!"
        elif stu == -5:
            return "存在不和谐内容,请不要当炸弹人"
        else:
            return "存在未知错误"
