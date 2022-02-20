"""
@Author     : shiying (github: LYshiying)
@Contact    : Twitter: @shiying_ui | QQ: 839778960
@Version    : 2.0.3
@EditTime   : 2022/2/18 16:22am(Editor: shiying)
@Desc       : 由于文档更新, 不再使用头文件写注释
"""
import os
import re
import logging
import asyncio
import nest_asyncio
import uvicorn

import nonebot
from nonebot.log import logger as nlog

import config
from soraha_utils import set_logger, sync_uiclient

version = "2.0.3"


def check_update():
    with sync_uiclient(proxy=config.proxies.copy()) as uicl:
        res = uicl.uiget(
            "https://raw.githubusercontent.com/LYshiying/ui_bot/main/bot.py"
        )

    version_git = re.findall("@Version    : (.+)", res.text)[0]
    version_desc = re.findall("@Desc       : (.+)", res.text)[0]

    new_msg = (
        f"发现新版本更新: {version_git}\n"
        f"更新描述: 请查阅: https://uibot.uisbox.com/#/zh-cn/update-log/\n"
        f"请在根目录shift+右键打开终端PowerShell,使用git pull进行更新"
    )
    msg = (
        f"目前uibot版本为: {version},无需更新"
        if version_git == version
        else f"目前uibot版本为: {version}\n{new_msg}"
    )

    logger.info(msg)


def switch_modules(modules_list):
    for module_name in modules_list:
        nonebot.load_plugin(f"src.plugins.{module_name}")
    return


def start() -> None:
    nonebot.init(config)
    _log("DEBUG") if config.DEBUG else _log()

    if config.checkupdate:
        try:
            check_update()
        except:
            logger.info("版本检查失败,那就由羽衣来猜吧！唔姆唔姆……有新版本可用！")

    os.makedirs(config.res, exist_ok=True)
    logger.debug("res文件夹创造完毕/已经存在res文件夹")

    name_list = [x for x in config.plugins]
    for i in name_list:
        nonebot.load_plugin(f"src.plugins.{i}")
    nest_asyncio.apply()
    nonebot.run(loop=asyncio.get_event_loop())


def _log(level: str = "INFO") -> None:
    """设置日志

    Args:
        level (str, optional): 目前仅支持'INFO'以及'DEBUG'. Defaults to "INFO".
    """
    global logger
    logger = set_logger(
        use_file=True,
        level=level,
        file_path="./log/uilog.log",
        file_level=level,
    )

    # nonebot 提供的 logger
    handler = logging.FileHandler("./log/uilog.log", encoding="utf-8")
    # 因为有点烦人 所以去掉了动态更改 我调试的时候只需要看 soraha utils 的 DEBUG 输出 暂时不需要……
    # 如果你需要 nonebot 的 DEBUG 输出请去掉注释
    # handler.setLevel(logging.INFO) if level.upper() == "INFO" else handler.setLevel(logging.DEBUG)
    nlog.setLevel(logging.INFO)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
    )
    handler.setFormatter(formatter)

    nlog.addHandler(handler)


if __name__ == "__main__":
    # 似乎是 APS scheduler 的问题, 导致重启并没有完全退出, 所以先不用了
    # uvicorn.run(
    #     app="bot:start",
    #     reload=True,
    #     reload_dirs=["bot.py"],
    #     port=9233,
    # )
    start()
