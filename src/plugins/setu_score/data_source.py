import httpx
import requests
from typing import Union
from loguru import logger
from base64 import b64encode

import config


class pic_score:
    """图片打分类,提供了请求api返回分数的接口以及图片base64加密的接口"""

    api_key = config.baidu_setu_score_api_key
    secret_key = config.baidu_setu_score_secret_key
    api_host = f"https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={api_key}&client_secret={secret_key}"
    headers = {"content-type": "application/x-www-form-urlencoded"}
    token_host = None

    def __init__(self) -> None:
        """初始化方法,异步请求百度api获取access_token"""
        logger.info("setu_score: 正在尝试获取token")
        logger.debug(f"开始连接->{self.api_host}")
        res = requests.get(
            self.api_host, proxies=config.proxies_for_all.copy(), timeout=15
        )
        logger.debug(f"status_code = {res.status_code}")
        self.token = res.json()["access_token"]
        self.token_host = (
            "https://aip.baidubce.com/rest/2.0/solution/v1/img_censor/v2/user_defined"
            + "?access_token="
            + self.token
        )

    async def async_get_token(self) -> None:
        logger.info("setu_score: 正在尝试获取token")
        logger.debug(f"开始连接->{self.api_host}")
        res = requests.get(self.api_host, proxies=config.proxies_for_all.copy())
        logger.debug(f"status_code = {res.status_code}")
        self.token = res.json()["access_token"]
        self.token_host = (
            "https://aip.baidubce.com/rest/2.0/solution/v1/img_censor/v2/user_defined"
            + "?access_token="
            + self.token
        )

    async def get_score(
        self, url: str = None, img_path: b64encode = None
    ) -> dict[bool, str, Union[int, None]]:
        """请求百度api,获取分数,url/img_path二选一填写,都填写优先url

        Args:
            url (str, optional): 图片的url地址. Defaults to None.
            img_path (str, optional): 图片的base64加密. Defaults to base64.

        Returns:
            dict[bool,str,Union[int,None]]: {
                "status": False/True # 是否成功
                "error_msg": 错误信息 # 成功依然保留但为空
                "result": 结果 # 成功返回分数,失败返回None
            }
        """
        if not self.token_host:
            await self.async_get_token()

        data = {"imgUrl": url} if url else {"image": img_path}
        async with httpx.AsyncClient(
            self.token_host,
            headers=self.headers,
            proxies=config.proxies_for_all,
            timeout=15,
        ) as client:
            logger.debug(
                f"开始连接->{self.token_host}\nheader:{self.headers}\ndata:{data}\nproxy={config.proxies_for_all}"
            )
            res = await client.post(self.token_host, data=data)
            logger.debug(f"status_code:{res.status_code}")
            try:
                js = res.json()
            except:
                logger.debug(f"json解析失败")
                return {"status": False, "error_msg": "API Error", "result": None}
        score = [
            int(x["probability"]) * 500
            for x in js
            if x["type"] == 1
            and (x["subType"] == 0 or x["subType"] == 1 or x["subType"] == 10)
        ]
        return {"status": True, "error_msg": "", "result": max(score)}

    def image_encode(path: str) -> Union[None, b64encode]:
        """将图片加密至base64编码

        Args:
            path (str): 图片的保存路径

        Returns:
            base64: base64编码 # 错误时返回None
        """
        try:
            with open(path, "rb") as f:
                return b64encode(f.read())
        except FileNotFoundError:
            logger.warning(f"没有找到图片地址:{path}")
            return None
        except:
            return None
