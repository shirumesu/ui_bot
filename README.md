# ui_Bot

![PyPI](https://img.shields.io/badge/PyPI-1.8.2-blue?logo=#3775A9)
![Python Version](https://img.shields.io/badge/python-3.9-brightgreen)
![Code-style](https://img.shields.io/badge/Codestyle-black-black)

[![作者qq](https://img.shields.io/badge/作者qq-839778960-orange.svg?style=flat&logo=Tencent-QQ)](https://qm.qq.com/cgi-bin/qm/qr?k=WKBxF1bEZ2ghsbmW2dCx9DWtzOp7Oq94&noverify=0)

# 2022/8/5留： 要不还是跑路吧
总而言之，因为各种各样的原因，加上暑假太摆了，年久失修的bot终于迎来睡眠的一天了！  
下一次或许会尝试基于新的nonebot2或是koishi又或是别的什么来重启！  
因此如果你现在才看到！那么可以退出了非常抱歉！  
如果你是一直以来的用户…（会有嘛…尽管star在往上涨就是了……）那么也要对你说声抱歉！尽管如此，bot一些使用率较高的核心功能像是pixiv和推特相关的订阅在较长一段时间内应该还不会有任何问题，bot本身也不带任何与服务器连接的功能，因此实际上完全可以继续用下去！  
那么晚安啦~羽衣，下一次再一起冒险吧~等你下一次醒来

## 简介

**由于使用`Github Pages`托管文档, 不再使用此README 请转到: <https://uibot.uichans.com/>**

### 简单介绍

- 前身:`dol_chan`出自`魔女之旅`的`海豚项链`得名
  - 因为是自己一边学python一边写的, 代码屎山, 从未公开并现在已经弃用
  - 重构成为了现在的`uibot` (实际上`uibot`也经过一次重构)

### 原理

- 框架: [Nonebot 1](https://github.com/nonebot/nonebot)
- OneBot实现: [go-cqhttp](https://github.com/Mrs4s/go-cqhttp)
- 通信: 反向 WebSocket

### 主要功能

#### 娱乐

- 获取色图
- 彩云小梦续写
- 碧蓝航线版猜头像|猜角色
- 枝江查重(精准打击偷梗人！)
- 表情包制作
- 切噜语翻译 / 莫妮卡乱码(将文字翻译为 Just Monika)
- 等等……

#### 订阅

- 推特用户订阅
- Pixiv画师订阅
- RssHub订阅

#### 有点用的

- 今日新闻(60秒看世界)
- 碧蓝航线wiki
  - 支持查询舰船信息、装备信息、强度榜、装备一图榜、全装备秒伤榜
- SauceNao & Ascii2d 搜图
- E-hentai 搜本
