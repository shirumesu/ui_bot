"""
@Author     : shiying (github: LYshiying)
@Contact    : Twitter: @shiying_ui | QQ: 839778960
@Version    : 1.0.5.3
@EditTime   : 2021/9/30 15:35pm(Editor: shiying)
@Desc       : 修复: selenium跟playwright有一个不存在会导致整个插件无法使用的情况
"""
import os
import re
import asyncio
import uvicorn
import nest_asyncio
import uvicorn

import nonebot
import config
import soraha_utils
from soraha_utils import logger


version = "1.0.5.3"


def check_update():
    with soraha_utils.sync_uiclient(proxy=config.proxies.copy()) as uicl:
        res = uicl.get("https://raw.githubusercontent.com/LYshiying/ui_bot/main/bot.py")

    version_git = re.findall("@Version    : (.+)", res.text)[0]
    version_desc = re.findall("@Desc       : (.+)", res.text)[0]

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


def start() -> None:
    nonebot.init(config)
    name_list = [x for x in config.plugins]
    for i in name_list:
        nonebot.load_plugin(f"src.plugins.{i}")
    nest_asyncio.apply()
    nonebot.run(loop=asyncio.get_event_loop())


if __name__ == "__main__":
    logger = soraha_utils.set_logger(
        level=config.DEBUG,
        use_file=True,
        file_path="./log/uilog.log",
        file_level=config.DEBUG,
    )

    if config.checkupdate:
        try:
            check_update()
        except:
            logger.info("版本检查失败,那就由羽衣来猜吧！唔姆唔姆……有新版本可用！")

    os.makedirs(config.res, exist_ok=True)
    logger.debug("res文件夹创造完毕/已经存在res文件夹")

    uvicorn.run(app="bot:start", reload=True, reload_dirs=["bot.py"])
