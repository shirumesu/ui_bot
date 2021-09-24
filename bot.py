"""
@Author     : shiying (github: LYshiying)
@Contact    : Twitter: @shiying_ui | QQ: 839778960
@Version    : 1.0.5.1
@EditTime   : 2021/9/19 20:19pm(Editor: shiying)
@Desc       : 新增: 使用闭嘴的时候可以屏蔽所有推送相关功能, 修复: 闭嘴功能在推送屏蔽的bug(闭嘴了依旧推送)
"""
import os
import sys
import requests
import time
import re
from loguru import logger
from bs4 import BeautifulSoup

import nonebot
import config
from src.Services import init_bot


version = "1.0.5.1"


def get_chrome():
    logger.info("正在尝试检查chrome-drive内核……")
    if not os.listdir(os.path.join(config.res, "source", "blhxwiki")):
        logger.debug(
            f"连接url:https://chromedriver.chromium.org/,代理:{str(config.proxies.copy())}"
        )
        s = requests.get(
            "https://chromedriver.chromium.org/",
            proxies=config.proxies.copy(),
            timeout=10,
        )
        logger.debug(f"status_code:{str(s.status_code)}")
        soup = BeautifulSoup(s.text, "lxml")
        html = soup.find_all("a", {"class": "XqQF9c"})
        logger.info(
            f"检测到稳定版chrome-drive:{html[4].string},请前往下载:{html[4].attrs['href']}"
        )
    else:
        logger.info("已有chrome-drive,无需下载")
    time.sleep(3)


def check_update():
    logger.info("正在尝试检查更新……")
    logger.debug(
        "连接url:https://raw.githubusercontent.com/LYshiying/ui_bot/main/bot.py,代理:{str(config.proxies.copy())}"
    )
    resp = requests.get(
        "https://raw.githubusercontent.com/LYshiying/ui_bot/main/bot.py",
        proxies=config.proxies.copy(),
    )
    logger.debug(f"status_code:{str(resp.status_code)}")

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
    logger.debug("日志配置加载完毕")


if __name__ == "__main__":
    log(config.DEBUG)

    if config.checkupdate:
        try:
            check_update()
        except:
            logger.error("检查更新失败,自动跳过")
        else:
            try:
                get_chrome()
            except:
                logger.error(
                    "无法检查chrome内核版本,请前往手动下载:https://chromedriver.chromium.org/\n(否则blhxwiki插件无法使用)"
                )
    os.makedirs(config.res, exist_ok=True)
    logger.debug("res文件夹创造完毕/已经存在res文件夹")

    nonebot.init(config)
    init_bot()

    nonebot.run()
