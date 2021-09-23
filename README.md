# ui_Bot

![PyPI](https://img.shields.io/badge/PyPI-v1.8.2-blue)
![Python Version](https://img.shields.io/badge/python-3.9-brightgreen)

[![作者qq](https://img.shields.io/badge/作者qq-839778960-orange.svg?style=flat&logo=Tencent-QQ)](https://qm.qq.com/cgi-bin/qm/qr?k=WKBxF1bEZ2ghsbmW2dCx9DWtzOp7Oq94&noverify=0)
![~不存在的q群~](https://img.shields.io/badge/qq群-真的没有-orange.svg?style=flat&logo=Tencent-QQ)
## 简介
前身为dol_chan(~~一个从未公开过的bot~~)一边学python一边写的,代码屎山,最终打算重构并且成为了现在的羽衣bot(~~屎山bot~~)  
基于[Nonebot 1](https://github.com/nonebot/nonebot)可以在qq上配合[go-cqhttp](https://github.com/Mrs4s/go-cqhttp)运行，目前已经支持:
  - 获取色图
  - 订阅推特
  - 碧蓝航线wiki相关支持
  - 订阅pixiv画师,pixivison,查看榜单以及画师精选图等(使用pixiv官方api,稳定性大大提高了！)
  - 订阅RssHub
  - 搜图
  - 莫妮卡乱码(把任何文字变为justmonika乱码,同时可以进行翻译)
  - 搜本
  - 翻译图片(支持竖排的漫画(~~当然质量一般~~))
  - 制作表情包
  - 还有一些好玩的例如群空调等就不举出来了

### 特别说明
部分模块借鉴了一些github上的插件/代码,特别声明一下(代码可能经过自己再更改)
  - [Hoshino bot](https://github.com/Ice-Cirno/HoshinoBot)
      - [切噜语翻译](https://github.com/Ice-Cirno/HoshinoBot/blob/master/hoshino/modules/priconne/cherugo.py)

  - 表情制作
    - [鲁迅说](https://github.com/NothAmor/nonebot2_luxun_says)
    - [我好想要五千兆日语](https://github.com/assassingyk/5000choyen)
    - [举牌表情](https://github.com/fz6m/nonebot-plugin/tree/master/CQimage)

  - [群空调](https://github.com/iamwyh2019/aircon)

  - [俄罗斯轮盘](https://github.com/pcrbot/russian)

  - 莫妮卡乱码的基础: [RCNB](https://github.com/rcnbapp/RCNB.py)

## 如何使用  

### 安装  
1. 首先请安装下列软件
    - [python](https://www.python.org/downloads/windows/)
    - [git](https://git-scm.com/download/win)
    - [记事本(Sublime Text)](https://www.sublimetext.com/)也可以选择不安装,使用默认或者你自己有(也有人喜欢notepad++ 总之自己喜欢)
2. 进入想要存放bot的文件,shift+右键此处打开shell
  1. 下载本项目
    
    git clone https://github.com/LYshiying/ui_bot

  2. 安装需要的第三方库
    
    pip3 install -r requirements.txt

  > 国内可以使用下面这个,经清华大学代理源下载,速度提升很多

    pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt  

  > 有报错请自行百度解决,此过程如果报错不管可能导致bot无法使用

3. 将**config-sample.py**改名为**config.py**并打开根据注释编辑

4. 安装并配置[go-cqhttp](https://github.com/Mrs4s/go-cqhttp),教程请自行去查看[文档](https://docs.go-cqhttp.org/)
    1. 如果你知道要干什么，也可以安装你喜欢的框架
    2. 并未对其他框架做测试(不保证可用性(good luck.jpg))
 
5. 先双击bot初始化一下,然后关闭窗口,去./res/source/blhxwiki/下下载对应版本的chrome-drive
    1. 并不难,linux跟windows都有支持,并未支持mac版本的drive,有报错自行百度即可,一般都是简单的版本跟安装问题,几分钟就能处理完
 
6. 双击bot.py启动,同时别忘了go-cqhttp,一并启动
   1. bot.py初始化的时候会生成一些插件配置文件以及目录
  
7. 安装完毕,使用方法等请在qq私聊bot发送'使用帮助'/'查看所有插件'查看

## 关于api
由于本项目使用了不少api,需要用户自己申请,以下放出部分教程(都是别人的)  
1. 推特
   
    1. [推特开发者账号](https://blog.csdn.net/jzy3711/article/details/86535692)
    2. [创建app](https://www.howtoing.com/how-to-create-a-twitter-app)
    > 私货:申请开发者理由写学生需要关注一些不同的消息(总之就是学习方面),成功率会高很多

2. 搜图
   
    1. [sauceNAO](https://saucenao.com/)  
    这个只需要注册账号就好

3. 百度
   
    1. [百度翻译](https://api.fanyi.baidu.com/doc/21)  
    跟着“如何使用通用翻译API？”一步步注册到第四步即可
    1. [百度ocr](https://cloud.baidu.com/doc/OCR/index.html)  
    注册,实名然后申请‘通用文字识别’的应用即可,过程不复杂，请自行百度
    
## TODO list
  - [ ] 每日推送pixiv日榜(必要性不高,暂时咕了)
  - [ ] 学完JavaScript来写前端配置页面
  - [ ] 内置机器学习(用处待定)
  - [x] Pixiv用官方api替换掉第三方api,增加稳定性
  - [x] 咕咕咕(让我√一个吧,我已经写不动了)

## 重大更新日志
<details>
<summary>2021年</summary>
    
|   时间    | 更新内容                                                                                                         |
| :-------: | :--------------------------------------------------------------------------------------------------------------- |
| 2021/1/17 | 使用SQLite替代所有csv file,现在只有一个数据库分不同表装着数据,不用一堆csv file了                                 |
| 2021/4/18 | bot正式命名:由暂定的dol_chan(海豚项链)改名为uibot(羽衣)并正式公开(主要为了codacy.jpg)(2021.6.3记:你公开了个寄吧) |
| 2021/5/11 | 开始重构bot                                                                                                      |
| 2021/6/03 | 重构完毕,正式公开                                                                                                |
</details>

<details>
<summary>2020年</summary>
    
|    时间    | 更新内容                                                                                              |
| :--------: | ----------------------------------------------------------------------------------------------------- |
| 2020/12/19 | 由于[pixiv api](https://api.imjad.cn/pixiv_v2.md)因p站新增机制失效,pixiv插件暂时找不到新出路,整个弃用 |
| 2020/12/27 | 更换[新pixiv api](https://api.hcyacg.com/),重写部分代码后pixiv插件重新启用                            |

</details>

## 鸣谢
  - 各种开发者对我问题的解答
  - Github中的各种优秀的开源库(~~让我有了连绵不绝的想法~~)
  - 来自沙雕群友们的催促以及写完了用一会就再也没用过的可恶行径
  - 来自我自己的稳定且高效的精神支持
