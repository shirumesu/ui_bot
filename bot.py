"""
@Author     : shiying (github: LYshiying)
@Contact    : Twitter: @shiying_ui | QQ: 839778960
@Version    : 1.0.2.5
@EditTime   : 2021/7/15 4:41pm(Editor: shiying)
@Desc       : 修复bug(request下代理会更改代理字典导致httpx报错),优化推特跟pixiv的错误跳过功能
"""
import os
import sys
import requests
import time
import re
from loguru import logger

import nonebot
import config
from src.Services import init_bot


version = "1.0.2.5"


def check_update():
    logger.info("正在尝试检查更新……")
    resp = requests.get(
        "https://raw.githubusercontent.com/LYshiying/ui_bot/main/bot.py",
        proxies=config.proxies.copy(),
    )

    version_git = re.findall("@Version    : (.+)", resp.text)[0]
    version_desc = re.findall("@Desc       : (.+)", resp.text)[0]

    new_msg = (
        f"发现新版本更新: {version_git}\n"
        f"更新描述: {version_desc}\n"
        f"请在根目录shift+右键打开终端PowerShell,使用git pull进行更新"
    )
    msg = (
        f"目前uibot版本为: {version},无需更新"
        if version_git == version
        else f"目前uibot版本为: {version}\n{new_msg}"
    )

    logger.info(msg)
    time.sleep(3)


def switch_modules(modules_list):
    for module_name in modules_list:
        nonebot.load_plugin(f"src.plugins.{module_name}")
    return


def log(debug_mode: bool = False):
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <lvl>{level}</lvl> | <lvl>{message}</lvl>",
        level="DEBUG" if debug_mode else "INFO",
        colorize=True,
    )
    logger.add(
        "./log/uilog.log",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <lvl>{level}</lvl> | <lvl>{message}</lvl>",
        rotation="00:00",
        retention="5 days",
        diagnose=False,
        level="DEBUG" if debug_mode else "INFO",
    )


if __name__ == "__main__":
    if config.checkupdate:
        try:
            check_update()
        except:
            logger.error("检查更新失败,自动跳过")
    os.makedirs(config.res, exist_ok=True)

    log(config.DEBUG)
    nonebot.init(config)
    init_bot()

    nonebot.run()
