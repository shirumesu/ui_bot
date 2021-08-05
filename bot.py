"""
@Author     : shiying (github: LYshiying)
@Contact    : Twitter: @shiying_ui | QQ: 839778960
@Version    : 1.0.2.1
@EditTime   : 2021/7/15 4:41pm(Editor: shiying)
@Desc       : 新增了碧蓝航线wiki相关的功能,并且重新调整了权限配置,优化了使用帮助的文本
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


version = "1.0.2.1"


def check_update():
    logger.info("正在尝试检查更新……")
    resp = requests.get(
        "https://raw.githubusercontent.com/LYshiying/ui_bot/main/bot.py",
        proxies=config.proxies,
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
        check_update()
    os.makedirs(config.res, exist_ok=True)

    log(config.DEBUG)
    nonebot.init(config)
    init_bot()

    nonebot.run()
