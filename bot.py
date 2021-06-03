import shutil
import os
import json

from loguru import logger

import nonebot.log

import config
from src.Services import init_bot


def switch_modules(modules_list):
    for module_name in modules_list:
        nonebot.load_plugin(f'src.plugins.{module_name}')
    return


def log(debug_mode: bool = False):
    logger.add("./log/ui_bot.log",
               rotation="00:00",
               retention='5 days',
               diagnose=False,
               level="DEBUG" if debug_mode else "INFO")


if __name__ == '__main__':

    os.makedirs(config.res, exist_ok=True)

    log(config.DEBUG)

    nonebot.init(config)
    init_bot()

    nonebot.run()
