import os
import json
from loguru import logger

import nonebot
from aiocqhttp import Event

import config
from src.ui_exception import Plugin_Change_Error


ALL_SERVICES = {}

SUPERUSER = 999
GROUP_OWNER = 100
GROUP_ADMIN = 50
GROUP_MEMBER = 5
PRIVATE_USER = 5
BLOCK_USER = -999

perm = {999: "羽衣酱的管理者", 100: "群主", 50: "群管理", 5: "群员/私聊", -999: "黑名单"}


def init_bot() -> None:
    """二次初始化机器人(

    nonebot启动后由service进行插件的加载工作
    同时将sv加入ALL_SERVICES
    不启用的插件将会简单的实例化service但不会加载

    **如果不存在sv_config.json文件(该插件从未启用过)将会加载初始化一次然后根据is_enable属性决定是否关闭**
    """
    name_list = [x for x, y in config.plugins.items()]
    for i in name_list:
        nonebot.load_plugin(f"src.plugins.{i}")


class Service_Master:
    """管理所有Service

    提供统一开关以及权限检查等功能
    Attributes:
        sv_list = ALL_SERVICES
    """

    def __init__(self):
        self.sv_list = ALL_SERVICES

    async def enable_plugin(
        self, plugin_name: str, state: bool, gid: int = None, uid: int = None
    ) -> bool:
        """插件管理器中对某群或某私聊开启/关闭插件

        与下面的函数不同,这个插件为加入/移除白名单
        而下面的函数为整个插件对象移除或加载

        Args:
            plugin_name: 插件的名字
            state: 开启或关闭插件
            gid: 开启的群号
            uid: 开启的私聊对象的qq号

        特别注意:
            gid跟uid只需要传入其中一个就好,会自动判断,两个都传入则会报错

        Return:
            bool: 是否成功加入/移除白名单
        """
        sv = self.sv_list[plugin_name]
        if gid and uid:
            logger.warning("gid跟uid同时存在")
            raise Plugin_Change_Error("gid and uid exist at same time")
        if gid:
            if state:
                try:
                    sv.block_group.remove(gid)
                finally:
                    if gid in sv.enable_group:
                        return True
                    sv.enable_group.append(gid)
                    self.sv_list[plugin_name] = sv
                    sv.save_config()
                    return True
            else:
                try:
                    sv.enable_group.remove(gid)
                finally:
                    if gid in sv.block_group:
                        return True
                    sv.block_group.append(gid)
                    self.sv_list[plugin_name] = sv
                    sv.save_config()
                    return True
        else:
            if state:
                sv.priv_use = True
                try:
                    sv.block_priv.remove(uid)
                finally:
                    self.sv_list[plugin_name] = sv
                    sv.save_config()
                    return True
            else:
                try:
                    sv.block_priv.append(uid)
                finally:
                    self.sv_list[plugin_name] = sv
                    sv.save_config()
                    return True

    async def switch_plugin_global(self, plugin_name: str, status: bool) -> bool:
        """全局开关插件

        设置插件的is_enable属性

        Args：
            plugin_name： 插件名字
            status： 开或关闭插件

        Return：
            是否成功关闭
        """
        sv = self.sv_list[plugin_name]
        sv.is_enable = False if not status else True
        sv.save_config()
        self.sv_list[plugin_name] = sv
        return True

    async def role_to_perm(self, ev: Event, role: str) -> int:
        """将role的文本转换为permission的数字

        Args:
            ev: 消息封装的event
            role: 文本例如owner, admin等
        """
        uid = ev["user_id"]
        if uid in config.SUPERUSERS:
            return SUPERUSER
        elif ev.detail_type == "private":
            return PRIVATE_USER
        elif role == "owner":
            return GROUP_OWNER
        elif role == "admin":
            return GROUP_ADMIN
        elif role == "administrator":
            return GROUP_ADMIN
        else:
            return GROUP_MEMBER

    async def check_permission(
        self,
        plugin_name,
        event: Event,
        perm: int = None,
        disable_superuser: bool = False,
    ) -> list:
        """对插件进行权利检查

        是否启用/是否允许私聊使用/是否允许使用
        以及对白名单黑名单进行检查

        Args:
            sv: Service要检查的插件的类
            event: 信息的event, 包含uid等内容
            perm: 需要的权限, 如果传入则单纯判断是否满足权限要求(**仅支持群聊消息使用**)
            disable_superuser: 是否检查超级用户的权限(True则为天子与民同罪)

        Return:
            list: list[bool, role, need_role,extra]
                >>> bool: 是否通过检查,有权限使用
                >>> role: 该用户是什么样的权限(admin/superuser等) -1为插件未启用,跳过获取用户权限的阶段
                >>> need_role: 该插件所需要的权限
                >>> extra: 不是由于权限不足而导致的未通过检查,为文本,描述原因


        权限判断较为复杂,特此说明
        关于白名单和黑名单的几种情况:
               情况                                       结果
        在白名单里,不在黑名单里                      正常情况,执行程序
        不在黑名单里,不在白名单里且白名单为空         正常情况,执行程序
        在黑名单里,不在白名单里且白名单不为空         正常情况,不执行程序
        在黑名单里,不在白名单里且白名单为空           正常情况,不执行程序
        不在黑名单里,不在白名单里且白名单不为空       正常情况,不执行程序
        在白名单里,在黑名单里                        优先处理黑名单,不执行程序

        一句话总结: 优先处理黑名单,不在黑名单判断白名单是否为空,不为空则判断群号是否在白名单内,不在则否

        程序处理顺序:
            1. 检查传入的插件名是否合法,否则返回 '没有找到该插件'
            2. 检查是否传入perm参数
                2.1. 是且为字符串格式
                    2.1.1. 目前仅可能传入ump字符串,代表插件管理器传入,启用特殊规则,判断更改的权限而非使用的权限
                    2.1.2. 进行正常处理,对比用户权限是否高于插件的permission_change参数
                2.2. 是且为数字格式(SUPERUSER,GROUP_ADMIN等实际上为数字格式)
                    2.2.1 跳过,后续检查
            3. 检查插件是否启用
                3.1. 备注: 后检查插件是否启用是为了防止插件管理器这类关键插件被关闭
            4. 检查是否传入disable_superuser参数
                4.1. 是,无视超级用户规则,如果插件在群被禁止,超级用户也无法使用
                4.2. 否,与上方相反,就算插件被禁止使用超级用户依旧可以调用
            5. 获取用户的权限等级
                5.1. 这里实际上是Nonebot原先封装好的权限,只是额外造了个轮子
                5.2. 群聊会获取到超级用户/群主/群管理员/群员四个权限,而非群聊消息只会获取到超级用户/相等于群员的私聊用户权限
            6. 权限判断
                6.1. 判断群聊权限
                    6.1.1. 检查群号是否同时在黑名单和白名单 -> 日志报错,优先处理黑名单,返回不通过以及错误信息
                    6.1.2. 检查群号是否在黑名单中 -> 返回不通过,错误信息
                    6.1.3. 检查是否开启白名单且群号不在白名单中 -> 返回不通过,错误信息
                6.2. 判断私聊权限
                    6.2.1. 检查插件是否禁止私聊使用 -> 返回不通过,错误信息
                    6.2.2. 检查用户uid是否在私聊黑名单中 -> 返回不通过,错误信息
            7. 检查是否传入了perm参数(2.2.1的后续检查)
                7.1. 对比perm参数是否小于permission_use -> 返回不通过,错误信息
            8. 前面一路过来没有被return的 -> 返回通过
        """
        try:
            sv = self.sv_list[plugin_name]
        except Exception:
            return [False, 0, 0, "没有找到该插件！"]

        if isinstance(perm, str):
            # ui_plugin_manager
            if perm == "upm":
                if event["user_id"] in config.SUPERUSERS:
                    return [True, SUPERUSER, sv.permission_change, ""]
                elif event.detail_type == "group":
                    user_perm = await self.role_to_perm(event, event["sender"]["role"])
                else:
                    user_perm = PRIVATE_USER
                if user_perm > sv.permission_change:
                    return [False, user_perm, sv.permission_use, "你的权限不足以修改此插件！"]
                else:
                    return [True, user_perm, sv.permission_use, ""]

        if not sv.is_enable:
            return [False, -1, sv.permission_use, "插件未启用！"]

        if not disable_superuser:
            if event["user_id"] in config.SUPERUSERS:
                return [True, SUPERUSER, sv.permission_use, ""]

        if event.detail_type == "group":
            user_perm = await self.role_to_perm(event, event["sender"]["role"])
        else:
            user_perm = PRIVATE_USER

        if event.detail_type == "group":
            gid = event["group_id"]
            if gid in sv.block_group and gid in sv.enable_group:
                logger.error(f"插件{sv.plugin_name[0]}中群号{gid}同时存在于黑名单与白名单中！优先处理黑名单")
                return [False, user_perm, sv.permission_use, "你群在黑名单中！不能使用该功能哦"]
            elif gid in sv.block_group:
                return [False, user_perm, sv.permission_use, "你群在黑名单中!不能使用该功能哦"]
            elif sv.enable_group and gid not in sv.enable_group:
                return [
                    False,
                    user_perm,
                    sv.permission_use,
                    "你群不在白名单中！请通知有权限的管理开启！(一般为管理员或以上)",
                ]

        elif event.detail_type == "private":
            uid = event["user_id"]
            if not sv.priv_use:
                return [False, user_perm, sv.permission_use, "此插件禁止私聊使用！"]
            elif uid in sv.block_priv:
                return [False, user_perm, sv.permission_use, "你已被禁止私聊使用此插件！"]

        if perm is not None:
            if user_perm < perm:
                return [False, user_perm, perm, "你的权限不足以使用此插件！"]
            return [True, user_perm, perm, ""]
        else:
            if user_perm < sv.permission_use:
                return [False, user_perm, perm, "你的权限不足以使用此插件！"]
        return [True, user_perm, sv.permission_use, ""]


class Service:
    """注册一个独立的插件

    设置单独每个插件的黑名单, 是否私聊使用, 是否启动等信息
    并且dump为json-file保存
    允许机器人的超级用户在qq上管理此配置
    **插件单独的固定配置(如: Api Key)会在.env.dev文件**

    Attributes:
        plugin_name: [英文文件名, 别名]
        path: 插件的文件夹路径 用于保存json-file
        plugin_usage: 插件的帮助文档
        use_folder: 是否使用文件夹(会在res/cacha文件夹下额外新建一个文件夹存放资源)
        use_cacha_folder: 是否使用文件夹(会在res/source下新建文件夹存放临时资源)(**会被自动删除,如果需要固定资源请使用use_folder**)
        permission_change: 修改权 记录高于或等于这个权限才能修改
        permission_use: 同上 使用权 高于或等于这个权限才能使用
        is_enalbe: 插件是否启用(设置为False代表不会响应此插件)
        priv_use: 是否接受私聊使用此插件
        enable_priv: 谁的私聊可以使用 空列表则任意(除了block_priv)内的
        block_priv: 禁止私聊的黑名单(群号)
        visible: 是否被显示在help里
        enable_group: 在什么group启用(群号) 空列表则为在任何群(除了block_group内)启用
        block_group: 禁止的黑名单群号

    关于enable和block的几种情况:
           情况                                       结果
    在enable里,不在block里                      正常情况,执行程序
    不在block里,不在enable里且enable为空         正常情况,执行程序
    在block里,不在enable里且enable不为空         正常情况,不执行程序
    在block里,不在enable里且enable为空           正常情况,不执行程序
    不在block里,不在enable里且enable不为空       正常情况,不执行程序
    在enable里,在block里                        优先处理block,不执行程序

    json格式:
        {
            {key:value}
        }
    """

    def __init__(
        self,
        plugin_name: list[str],
        plugin_usage: str = "",
        use_folder: bool = False,
        use_cacha_folder: bool = False,
        permission_change: int = SUPERUSER,
        permission_use: int = GROUP_MEMBER,
        is_enalbe: bool = True,
        priv_use: bool = True,
        block_priv: list[int] = [],
        visible: bool = True,
        enable_group: list[int] = [],
        block_group: list[int] = [],
    ):
        """注册一个独立的插件

        设置单独每个插件的黑名单, 是否私聊使用, 是否启动等信息
        并且dump为json-file保存
        允许机器人的超级用户在qq上管理此配置
        **插件单独的固定配置(如: Api Key)会在.env.dev文件**

        Args:
            plugin_name (list[str, str]): 插件名字[插件的英文名(src.plugin.xxxxx)的xxxxx,插件的中文名(最好与config文件一致)]
            plugin_usage (str, optional): 插件的使用帮助(每次启动会自动检测是否与json的一致,不一致则更改) Defaults to "".
            use_folder (bool, optional): 是否需要使用文件夹存放**固定**资源,会在res/source下新建文件夹(清理时不会清理source文件夹) Defaults to False.
            use_cacha_folder (bool, optional): 是否需要使用文件夹存放**临时**资源,会在res/cacha下新建文件夹(每个小时会自动清理一次) Defaults to False.
            permission_change (int, optional): 更改插件状态(是否在此群关闭/开启插件)的权限,
                                               可选:超级用户SUPERUSER>群主GROUP_OWNER>群管理GROUP_ADMIN>群员GROUP_MEMBER=私聊用户PRIVATE_USER>黑名单用户BLOCK_USER
                                               普通插件建议GROUP_ADMIN可以控制,涉及R18或敏感资源的插件建议SUPERUSER
                                               Defaults to SUPERUSER.
            permission_use (int, optional): 同上,此处为可以使用该插件的权限(使用插件的命令) Defaults to GROUP_MEMBER.
            is_enalbe (bool, optional): 是否启用此插件(不建议在config文件夹注释掉插件,而是加载后关闭掉,这样可以不用重启直接管理插件)
                                        特例:插件管理器就算关闭也依然可以被超级用户使用
                                        Defaults to True.
            priv_use (bool, optional):  是否可以私聊使用,有可能被举报的东西建议禁止私聊(毕竟你不知道会有什么人用什么样的指令) Defaults to True.
            block_priv (list[int], optional): 私聊黑名单,用列表装着,**最好为int格式**,示例[12345,67890] Defaults to [].
            visible (bool, optional): 是否可见(在查看插件目录时是否显示)(一些内置且不带指令的插件不建议显示) Defaults to True.
            enable_group (list[int], optional): 群白名单,同私聊黑名单,如果为空则为不开启,具体规则请参照下方 Defaults to [].
            block_group (list[int], optional): 群黑名单,同上 Defaults to [].

        关于enable和block的几种情况:
               情况                                       结果
        在enable里,不在block里                      正常情况,执行程序
        不在block里,不在enable里且enable为空         正常情况,执行程序
        在block里,不在enable里且enable不为空         正常情况,不执行程序
        在block里,不在enable里且enable为空           正常情况,不执行程序
        不在block里,不在enable里且enable不为空       正常情况,不执行程序
        在enable里,在block里                        优先处理block,不执行程序

        一句话总结: 优先处理黑名单,不在黑名单判断白名单是否为空,不为空则判断群号是否在白名单内,不在则否
        """
        self.plugin_name = plugin_name
        self.path = os.path.join(
            os.getcwd(), "src", "plugins", plugin_name[0], "sv_config.json"
        )
        exist_config = self.load_config(self.path, plugin_usage)
        if not exist_config:
            self.plugin_name = plugin_name
            self.usage = plugin_usage
            self.use_folder = use_folder
            self.use_cacha_folder = use_cacha_folder
            self.permission_change = permission_change
            self.permission_use = permission_use
            self.is_enable = is_enalbe
            self.priv_use = priv_use
            self.block_priv = block_priv
            self.visible = visible
            self.enable_group = enable_group
            self.block_group = block_group
        self.create_folder()
        self.save_config()
        ALL_SERVICES[self.plugin_name[0]] = self
        logger.info(f"success to load plugin:{plugin_name[0]}({plugin_name[1]})")

    def create_folder(self):
        if self.use_folder:
            os.makedirs(
                os.path.join(os.getcwd(), "res", "source", self.plugin_name[0]),
                exist_ok=True,
            )
        if self.use_cacha_folder:
            os.makedirs(
                os.path.join(os.getcwd(), "res", "cacha", self.plugin_name[0]),
                exist_ok=True,
            )

    def save_config(self):
        """保存json-file"""
        dicts = {
            "name": self.plugin_name,
            "usage": self.usage,
            "path": self.path,
            "use_folder": self.use_folder,
            "use_cacha_folder": self.use_cacha_folder,
            "permission_change": self.permission_change,
            "permission_use": self.permission_use,
            "is_enable": self.is_enable,
            "priv_use": self.priv_use,
            "block_priv": self.block_priv,
            "visible": self.visible,
            "enable_group": self.enable_group,
            "block_group": self.block_group,
        }
        with open(self.path, mode="w", encoding="utf-8") as f:
            json.dump(dicts, f, ensure_ascii=False, indent=4)

    def load_config(self, path: str, usage: str):
        """加载json-file

        每次加载插件的时候都会调用这个函数注册service
        """
        if not os.path.exists(path):
            with open(path, mode="w", encoding="utf-8") as f:
                f.write("")
                logger.info(
                    f"插件{self.plugin_name[0]}({self.plugin_name[1]})下不存在配置文件,正在创建新文件"
                )
            return
        with open(path, "r", encoding="utf-8") as f:
            sv_config = json.load(f)
        self.plugin_name = sv_config["name"]
        self.usage = sv_config["usage"] if sv_config["usage"] == usage else usage
        self.use_folder = sv_config["use_folder"]
        self.use_cacha_folder = sv_config["use_cacha_folder"]
        self.permission_change = sv_config["permission_change"]
        self.permission_use = sv_config["permission_use"]
        self.is_enable = sv_config["is_enable"]
        self.priv_use = sv_config["priv_use"]
        self.block_priv = sv_config["block_priv"]
        self.visible = sv_config["visible"]
        self.enable_group = sv_config["enable_group"]
        self.block_group = sv_config["block_group"]
        return True
