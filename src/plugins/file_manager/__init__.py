import os
import time
from pathlib import Path

import nonebot

import config as cfg
from src.Services import uiPlugin, SUPERUSER
from soraha_utils import logger


sv_help = """文件清理 | 使用帮助
啊这…森林里的精灵们会自动打扫的 还要什么使用帮助吗？
""".strip()
sv = uiPlugin(
    ["file_manager", "文件清理"],
    False,
    usage=sv_help,
    perm_use=SUPERUSER,
    perm_manager=SUPERUSER,
    private_use=False,
    visible=False,
)


async def rt_all_file(dir_path: str) -> list:
    """遍历文件夹

    遍历传入的文件夹,将所有文件装入file_list

    Args:
        dir_path: 需要遍历的文件夹绝对路径

    Return:
        file_list: 该文件夹下所有文件
    """
    pt = Path(dir_path)
    file_list = [x for x in pt.glob("**/*") if x.is_file()]
    return file_list


async def rt_res(
    file_list: list, now_time: float, overtime: int, list_name: str
) -> None:
    """清理文件

    对于传入的文件列表,对比创建时间以及现在时间,如果少于overtime则清理

    Args:
        file_list: 文件列表
        now_time: 时间戳表示的现在时间
        overtime: 过期时间,如果文件创建时间超过这个时间则清理
        list_name: 文件夹名字,单纯用于打印日志
    """
    logger.debug(f"开始清理{list_name}文件")
    total_size = 0
    num = 0
    for file in set(file_list):
        ctime = os.path.getctime(file)
        size = os.path.getsize(file)
        br = abs(ctime - now_time)
        if os.path.isfile(file) and br > overtime:
            strf_ctime = time.strftime(r"%Y-%m-%d %H %M %S", time.localtime(ctime))
            os.remove(file)
            total_size += size
            num += 1
            logger.debug(
                f"清除文件:{file}\n文件大小:{round((size/1024),2)} KB\n创建时间{strf_ctime}"
            )
    logger.info(
        f"定期清理{list_name}文件完毕,清理文件数目:{num},总大小:{round(total_size/(1024*1024),2)} MB"
    )


@nonebot.scheduler.scheduled_job("interval", minutes=60, jitter=60)
async def _():
    """定时函数 定时清理文件"""
    now_time = time.time()
    file_list = await rt_all_file(os.path.join(cfg.res, "cacha"))
    await rt_res(file_list, now_time, 600, r"res/cacha")
