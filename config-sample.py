import datetime

# 超级用户(主人)的qq号
SUPERUSERS = {}
# 触发的指令前缀
COMMAND_START = {"", "/", "!", "#", "！"}
# 当有指令在运行时再次触发指令说的话(建议为空),否则容易不停刷屏
# 判定规则为A有指令在运行的时候B使用指令不会触发但A使用会触发,发送此消息
# 如果上面设置为空,则匹配所有人说的话,因此指令运行时,同一人说的任何一句话都会触发
SESSION_RUNNING_EXPRESSION = ""
# 一个命令运行的最长时间
# 如果网络较差请尽量长一点,涉及到拿图的请求如果时间到了会直接断掉
SESSION_RUN_TIMEOUT = datetime.timedelta(minutes=5)
# 等待用户回复的最长时间
SESSION_EXPIRE_TIMEOUT = datetime.timedelta(seconds=30)
# 机器人昵称,替代@xxx,否则使用指令必须@
# 空('')=匹配所有指令
NICKNAME = {""}
# 指令分割(指令的参数用什么符号分割)
# 可以无视这设置…实际使用中用其他方法替代了
COMMAND_SEP = {" "}
# APScheduler的配置,不明白的话默认即可
APSCHEDULER_CONFIG = {"coalesce": True, "max_instances": 1024}
# 运行端口,默认即可
HOST = "127.0.0.1"
PORT = 19198
# 是否启用调试模式(更详细的输出)
DEBUG = False

# 图片路径(绝对路径，例如D:\mybot\photo)
# 图片会在photo文件下生成
res = r""

# 启用的模块,不用的用"#"注释掉
# 可以修改sv_config(插件文件夹下的,没有请加载一次插件,可以更加详细的修改配置,各属性含义可以参照src.Service中Service类的注解)或是使用插件管理器进行管理
plugins = {
    "setu": "获取色图",
    "cheru": "切噜语翻译",
    "russian": "俄罗斯轮盘",
    "marionette": "人偶",
    "aircon": "群空调",
    "reply_msg": "自定义回复",
    "bot_manager": "机器人管理",
    "mkmeme": "表情制作",
    "rsshub": "订阅RssHub",
    "yobot": "yobot",
    "twitter": "推特订阅",  # 没有梯子(下面proxies没有填)的请不要开启,会无法获取
    "pixiv": "pixiv相关",  # 同上
    "translate": "翻译漫画",  # 需要百度翻译以及百度ocr API 否则无法使用
    "search_image": "以图搜图",  # 需要sauceNao API
    # **请绝对不要关闭这几个插件！**
    # file_manager 可选关闭,所有获取的图片都会保存下来,不开启的话res文件夹大小会飞涨,想获取色图的话可以选择注释关一段时间,然后去res/cacha/setu查看
    "file_manager": "文件清理",
    "usage": "使用帮助",
    "plugin_manager": "插件管理器",
    # TODO(shiying): 待制作插件
    # 鬼知道为什么我要放进github里···
    # "priconne": "pcr相关",
    # TODO(shiying): 写好这几个插件 deadline: this life
    # 'web_ui': '网页界面',
    # "uma_musume": "赛马娘",
}

# 所有插件请求外网时统一使用的代理
# 填写示例{
#   'http://': 'http://127.0.0.1:8080',
#   'https://': 'http://127.0.0.1:8080'    # 注意: https的值依然为http://xxx
# }
proxies = {"http://": None, "https://": None}
# 所有插件访问国内网站时使用的代理(特定梯子会需要填写,否则国内的也无法访问,如果你一切顺利的话,无视即可)
proxies_for_all = {"http://": None, "https://": None}
# 推特模块封装api使用的代理
proxy = None  # 填写示例: 127.0.0.1:8080
# 获取pixiv的图时是否使用代理i.pixiv.cat
# False则直连i.pximg.net获取图片
# 一般来说建议开启(不知道为何就算服务器在日本也会连代理快点…)
proxy_pixiv = True

# 自定义回复开关(有些时候会太吵了)
reply_switch = True

# Twitter模块用到的api
Access_token_for_Twitter = ""
Access_token_secret_for_Twitter = ""
API_key_for_Twitter = ""
API_secret_key_for_Twitter = ""

# 翻译模块用到的api
# ocr
# baidu_ocr_client_id = ''
baidu_ocr_client_id = ""
# baidu_ocr_client_secret = ''
baidu_ocr_client_secret = ""
# 翻译
baidu_translate_api_id = ""
baidu_translate_secret_key = ""

# 搜图模块用到的api
sauceNAO_api = ""
# sauce搜图相似度低于X%时候使用ascii2d (范围0-100,记得不要带%) (推荐60-70)
sim_to_ascii2d = 70  # **注意: 不要带% 否则会报错**

# pixiv的cookie
# 如果不使用,某些时候(画师精选等)的返回结果会与实际不符
# 获取方法,进入pixiv任意一个网站然后按f12随便点一个,查看request header中的cookie,然后copy value
# 具体可以百度如何获取cookie 一样的
pixiv_cookie = ""

# 短链用到的apikey
# 目前仅适配了Polr的api,也就是我自建的api,欢迎使用,也可以自己自建,并不难,都是跟着教程一步步走(前提是有个服务器)
# https://short.uisbox.com
short_url_apikey = ""

# 自建Rss
use_self_Rss = False
# 如果上面是False,则使用官方demo,否则使用下方的链接
# 填入Rsshub链接,例如https://rsshub.123456.com
# 欢迎使用我的自建rsshub(但是肯定没有官方demo稳定) https://rsshub.uisbox.com
# 胜在每分钟更新一次,而官方demo是一小时
# 注意: Rss在国内并不稳定,经常被墙,需要一个代理
Rss_route = ""
