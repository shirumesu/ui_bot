import inspect
from json.decoder import JSONDecodeError
import json
import os
from typing import Union, Optional, Iterable
from nonebot import on_command, CommandSession, get_bot

import config
from soraha_utils import logger

bot = get_bot()

default_help = "这里没有使用帮助\n羽衣也不知道为什么没有使用帮助呢,大概就是盲人摸象的感觉吧(笑)\n嘛,那种事情怎么样都好啦\n总之,祝你好运"
SUPERUSER = 999
GROUP_OWNER = 100
GROUP_ADMIN = 50
GROUP_MEMBER = 10
PRIVATE_USER = 1
ALLUIPLUGINS = {}


class uiPlugin_Master:
    def __init__(self) -> None:
        self.all_uiplugin = ALLUIPLUGINS

    def regis_plugins(self, plugin) -> None:
        self.all_uiplugin[plugin.name_en] = plugin

    @staticmethod
    def get_plugins(plugin_name: str):
        """给模块内的子文件获取模块的插件函数

        Args:
            plugin_name (str): 插件名
        """
        for plugin in ALLUIPLUGINS.values():
            if plugin.name_en == plugin_name or plugin.name_cn == plugin_name:
                return plugin

    def check_perm(
        self,
        session: CommandSession,
        plugin,
        plugin_manager: bool = False,
        ignore_superuser: bool = False,
    ) -> list[bool, str]:
        """权限检查

        Args:
            session (CommandSession): session
            plugin ([type]): 需要被检查的插件
            plugin_manager (bool): 是否为插件管理器传入的,权限判断从使用插件更换为管理插件
            ignore_superuser (bool): 是否忽略superuser,为真则将superuser当作群员|群管理|群主处理

        Returns:
            list[bool,str]: [是否通过,对应理由]
        """
        if not ignore_superuser and session.event.user_id in config.SUPERUSERS:
            return [True, "用户为超级用户"]
        else:
            gid = session.event.group_id
            uid = session.event.user_id
            perm = self.__change_role(session)
            if not plugin.enable:
                return [False, "插件没有开启！"]
            if str(gid) not in plugin.enable_group.keys():
                return [False, f"本群{gid}不在白名单中"]
            if str(uid) in plugin.block_priv:
                return [False, f"用户{uid}在黑名单中"]
            group_type = plugin.enable_group[str(gid)]
            if plugin_manager:
                if perm == PRIVATE_USER:
                    return [False, "插件管理器禁止私聊使用"]
                else:
                    if (perm - plugin.perm_manager) < 0:
                        return [False, f"需求权限:{plugin.perm_manager},用户权限:{perm}"]
                    else:
                        return [True, f"需求权限:{plugin.perm_manager},用户权限:{perm}"]
            if perm == PRIVATE_USER:
                if plugin.private_use:
                    if session.event.user_id in plugin.block_priv:
                        return [False, "允许私聊使用但用户在黑名单中"]
                    else:
                        return [True, "允许私聊使用"]
                else:
                    return [False, "禁止私聊使用"]

            if group_type == "亲友群":
                perm = GROUP_OWNER
            if (perm - plugin.perm_use) < 0:
                return [False, f"需求权限:{plugin.perm_use},用户权限:{perm}"]
            else:
                return [True, f"需求权限:{plugin.perm_use},用户权限:{perm}"]

    def regis_group(self, gid: int, g_type: str) -> list:
        """注册一个新群,加入白名单

        Args:
            gid (int): 群号
            g_type (str): 群类型,可选:["亲友群"|"普通群"],亲友群默认所有人为群主权限(仅限管理的功能开放给所有人)

        Returns:
            list: 所有成功开启的插件名
        """
        enable_plugins = []
        for plugin in self.all_uiplugin.values():
            if str(gid) in plugin.enable_group:
                pass
            elif g_type == "亲友群":
                plugin.enable_group[str(gid)] = g_type
                enable_plugins.append(plugin.name_cn)
            elif g_type == "普通群":
                if not plugin.r18:
                    plugin.enable_group[str(gid)] = g_type
                    enable_plugins.append(plugin.name_cn)
            else:
                raise ValueError
            plugin.dump_config()
        return enable_plugins

    def __change_role(self, session: CommandSession) -> int:
        """从session中获取用户的权限

        Args:
            session (CommandSession): session

        Returns:
            int: 权限
        """
        ev = session.event
        if ev.detail_type == "private":
            return PRIVATE_USER
        else:
            role = ev.sender["role"]

        if role == "owner":
            return GROUP_OWNER
        elif role == "admin" or role == "administrator":
            return GROUP_ADMIN
        else:
            return GROUP_MEMBER

    def match_plugin(self, plugin_name: Optional[tuple] = None) -> list:
        """获取所有适合的插件返回操作

        Args:
            plugin_name Optional[tuple]: 插件的名字,不传入则默认所有

        Returns:
            list: 所有匹配的插件
        """
        if not plugin_name:
            return self.all_uiplugin.values()
        plugins = []
        for plugin in self.all_uiplugin.values():
            if plugin.name_en in plugin_name or plugin.name_cn in plugin_name:
                plugins.append(plugin)
        return plugins

    def __remove_item(self, iter_item: Iterable[int], item: int):
        try:
            iter_item.pop(str(item))
        except IndexError:
            logger.debug(f"{item} not in iter_item({iter_item})")

    def switch_all(self, state: bool, plugin_name: Optional[tuple] = None) -> dict:
        """调整插件enable的函数

        Args:
            state (bool): 传入需要调整的状态,True为开启
            plugin_name (Optional[tuple], optional): 传入需要被禁用的插件名,否则默认全部插件. Defaults to None.

        Returns:
            dict: 所有匹配的插件,以及信息(成功|失败原因)
        """
        plugin_name = (plugin_name,) if isinstance(plugin_name, str) else plugin_name
        plugins = self.match_plugin(plugin_name=plugin_name)
        changed_plugins = {}
        for plugin in plugins:
            plugin.enable = state
            plugin.dump_config()
            changed_plugins[plugin.name_cn] = "成功!"
        return changed_plugins

    def block_all(
        self,
        type: str,
        uid: int,
        gid: int,
        state: bool,
        plugin_name: Optional[list] = None,
    ) -> dict[str, str]:
        """调整插件enable外的权限控制相关的函数
        ```
        type = "disable_private"
        >>> 将该插件禁止(开启)私聊使用
        type = "private"
        >>> 该插件禁止(开启)某人私聊使用
        type = "group"
        >>> 将插件禁止(开启)某群使用
        ```

        Args:
            type (str): ["disable_private","private","group"]
            uid (int): 用户的uid
            gid (int): 群id
            state (bool): True为开启,对三种情况均适用
            plugin_name (Optional[str], optional): 插件的名字,不传入则默认全部. Defaults to None.

        Returns:
            dict[str,str]: [更改过的插件名字,成功|失败理由]
        """
        changed_plugins = {}
        plugin_name = (plugin_name,) if isinstance(plugin_name, str) else plugin_name
        plugins = self.match_plugin(plugin_name=plugin_name)
        for plugin in plugins:
            if type == "disable_private":
                plugin.private_use = state
                changed_plugins[plugin.name_cn] = "成功"
            elif type == "private":
                if state:
                    if uid in plugin.block_priv:
                        self.__remove_item(plugin.block_priv, uid)
                        changed_plugins[plugin.name_cn] = "成功"
                else:
                    if uid in plugin.block_priv:
                        changed_plugins[plugin.name_cn] = f"失败,用户({uid})已经在黑名单中了！"
                        continue
                    plugin.block_priv.append(uid)
                    changed_plugins[plugin.name_cn] = f"成功"
            elif type == "group":
                if state:
                    if str(gid) in plugin.enable_group:
                        changed_plugins[plugin.name_cn] = f"失败,群({uid})已经在白名单中了！"
                        continue
                    else:
                        plugin.enable_group[str(gid)] = "普通群"
                        changed_plugins[plugin.name_cn] = "成功"
                else:
                    self.__remove_item(plugin.enable_group, gid)
                    changed_plugins[plugin.name_cn] = f"成功"
            else:
                logger.warning(f"type输入错误!tpye:{type}")
                raise ValueError()
            plugin.dump_config()
        return changed_plugins


class uiPlugin(uiPlugin_Master):
    def __init__(
        self,
        name: list[str],
        r18: bool,
        plugin_path: str = None,
        usage: str = default_help,
        use_cache_folder: bool = False,
        use_source_folder: bool = False,
        perm_use: int = 0,
        perm_manager: int = 50,
        visible: bool = True,
        private_use: bool = False,
        block_priv: Iterable[int] = [],
        enable_group: dict[int, str] = {},
    ) -> None:
        """注册一个插件,任何插件都请在该插件注册！

        Args:
            name (list[str]): [插件英文名字,插件中文名字]
            r18 (bool): 该插件是否为r18
            plugin_path (str, optional): 插件的目录(尽可能绝对目录),会自动获取. Defaults to inspect.stack()[1].filenames.
            usage (str, optional): 插件的使用帮助. Defaults to default_help.
            use_cache_folder (bool, optional): 是否使用缓存文件夹,会自动创建. Defaults to False.
            use_source_folder (bool, optional): 是否使用固定资源文件夹,会自动创建. Defaults to False.
            perm_use (int, optional): 使用的权限. Defaults to 0.
            perm_manager (int, optional): 修改插件的权限. Defaults to 50.
            visible (bool, optional): 是否可见(查看所有插件时是否显示). Defaults to True.
            private_use (bool, optional): 是否允许私聊使用. Defaults to False.
            block_priv (Iterable[int], optional): 私聊黑名单. Defaults to [].
            enable_group (dict[int, str], optional): 群聊白名单(群第一次请使用注册群). Defaults to {}.
        """
        self.name_en = name[0]
        self.name_cn = name[1]
        self.r18 = r18
        self.enable = True
        self.path = inspect.stack()[1].filename
        if "\\" in self.path:
            self.path = self.path.rsplit("\\", 1)[0]
        else:
            self.path = self.path.rsplit("/", 1)[0]
        self.path = self.path if not plugin_path else plugin_path
        self.usage = usage
        self.use_cache_folder = use_cache_folder
        self.use_source_folder = use_source_folder
        self.perm_use = perm_use
        self.perm_manager = perm_manager
        self.visible = visible
        self.private_use = private_use
        self.block_priv = block_priv
        self.enable_group = enable_group
        try:
            self.load_config()
            self.private_use = self.config["private_use"]
            self.block_priv = self.config["block_priv"]
            self.enable_group = self.config["enable_group"]
        except:
            self.config = {
                "name_en": self.name_en,
                "name_cn": self.name_cn,
                "r18": self.r18,
                "enable": self.enable,
                "path": self.path,
                "usage": self.usage,
                "use_cache_folder": self.use_cache_folder,
                "use_source_folder": self.use_source_folder,
                "perm_use": self.perm_use,
                "perm_manager": self.perm_manager,
                "visible": self.visible,
                "private_use": self.private_use,
                "block_priv": self.block_priv,
                "enable_group": self.enable_group,
            }
            self.dump_config()
        super().__init__()
        self.regis_plugins(self)

    def load_config(self) -> None:
        try:
            with open(
                os.path.join(self.path, "uiconfig.json"), "r", encoding="utf-8"
            ) as f:
                self.config = json.load(f)
                self.config["r18"] = self.r18
                self.config["usage"] = self.usage
                self.config["perm_use"] = self.perm_use
                self.config["perm_manager"] = self.perm_manager
                self.config["visible"] = self.visible
                logger.info(f"{self.name_cn}配置文件成功加载！")
        except (JSONDecodeError, FileNotFoundError) as e:
            logger.error(f"{self.name_cn}配置文件加载失败!:{e}")
            raise e

    def dump_config(self) -> None:
        """json文件的保存"""
        self.config = {
            "name_en": self.name_en,
            "name_cn": self.name_cn,
            "r18": self.r18,
            "enable": self.enable,
            "path": self.path,
            "usage": self.usage,
            "use_cache_folder": self.use_cache_folder,
            "use_source_folder": self.use_source_folder,
            "perm_use": self.perm_use,
            "perm_manager": self.perm_manager,
            "visible": self.visible,
            "private_use": self.private_use,
            "block_priv": self.block_priv,
            "enable_group": self.enable_group,
        }
        try:
            with open(
                os.path.join(self.path, "uiconfig.json"), "w", encoding="utf-8"
            ) as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
                logger.info(f"{self.name_cn}配置文件成功保存！")
        except (JSONDecodeError, FileNotFoundError) as e:
            logger.error(f"{self.name_cn}配置文件加载失败!:{e}")

    def create_folder(self):
        """创建文件夹"""
        if self.use_cache_folder:
            os.makedirs(
                os.path.join(os.getcwd(), "res", "source", self.name_en),
                exist_ok=True,
            )
        if self.use_source_folder:
            os.makedirs(
                os.path.join(os.getcwd(), "res", "source", self.name_en),
                exist_ok=True,
            )

    def ui_command(
        self,
        name: str,
        plugin_manager: bool = False,
        ignore_superuser: bool = False,
        aliases: Iterable[str] = (),
        patterns: Union[str, tuple] = (),
        privileged: bool = True,
        shell_like: bool = False,
    ) -> on_command:
        """替换Nonebot的on_command,所有command请使用这个注册！否则会没有权限检查跟内容发送的重试,同时请尽量不要使用`session.finish()`,因为没有重试
        使用方法:
        ```
        pl = uiPlugin(xxxx)

        @pl.ui_command(xxx)
        async def abc():
            session.send("end")
        ```

        Args:
            name (str): 同on_command,指令触发的名字
            plugin_manager (bool): 是否为插件管理相关插件,为真则使用判断管理插件所需的权限. Defaults to False.
            ignore_superuser (bool, optional): 是否无视超级用户的权限. Defaults to False.
            aliases (Iterable[str], optional): 同on_command,指令的别名. Defaults to ().
            patterns (Union[str, tuple], optional): 同on_command,regex触发. Defaults to ().
            privileged (bool, optional): 同on_command,是否可以多个指令同步使用. Defaults to True.
            shell_like (bool, optional): 同on_command. Defaults to False.

        Returns:
            on_command: on_command
        """

        def deco(func):
            @on_command(
                name,
                aliases=aliases,
                patterns=patterns,
                privileged=privileged,
                shell_like=shell_like,
            )
            async def wrap_command(session: CommandSession):
                checker = self.check_perm(
                    session, self, plugin_manager, ignore_superuser
                )
                if checker[0]:
                    logger.debug(
                        f"用户{session.event.user_id}使用插件{self.name_cn}(cmd:{name})通过: {checker[1]}"
                    )
                    return await func(session)
                else:
                    logger.info(
                        f"用户{session.event.user_id}使用插件{self.name_cn}(cmd:{name})不通过: {checker[1]}"
                    )
                    await session.send("啊咧咧,哦卡西那~权限不够哦")

            return wrap_command

        return deco
