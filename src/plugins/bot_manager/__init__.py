import psutil
import random
import time

from nonebot import on_command, CommandSession, MessageSegment

from src.Services import Service, Service_Master

sv_help = """bot状态 | 使用帮助
括号内的文字即为指令,小括号内为可选文字(是否必带请自行参照使用示例)
[bot状态] -> 查看目前bot状态
"""
sv = Service(["bot_manager", "bot状态"], sv_help, priv_use=False)


@on_command("bot状态")
async def bot_status(session: CommandSession):
    stat = await Service_Master().check_permission(
        "bot_manager", session.event, disable_superuser=True
    )
    if not stat[0]:
        await session.finish(stat[3])

    cpu = psutil.cpu_percent(1)
    memory = psutil.virtual_memory().percent
    disk = psutil.disk_usage("/").percent
    pid = psutil.Process()
    bot_memory = pid.memory_percent()
    create_time = pid.create_time()
    use_time = time.time() - create_time
    use_time_hour = use_time / (60 * 60)  # 单位: 小时
    use_time_error = use_time * random.uniform(0.95, 1.05)
    calc_error = random.choice([True, False])

    msg = (
        f"bot已不间断的运行了{use_time_hour:.2f}小时\n"
        f"唔姆…大概{use_time_error if calc_error else use_time:.2f}秒？\n"
        f"{'呜哇…算错了啦…' if calc_error else '…还有还有……'}\n"
        f"cpu使用:{cpu}%\n"
        f"内存使用:{memory}%\n"
        f"bot的内存占用:{bot_memory:.2f}%\n"
        f"硬盘使用:{disk}%\n"
        f"好累哦,要不然休息会吧~"
    )
    await session.finish(msg)
