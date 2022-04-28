# 安装

1. 安装软件
   1. [python](https://www.python.org/)
   2. [git](https://git-scm.com/)
   3. [(可选)记事本软件-Sublime Text](https://www.sublimetext.com/)
      1. 用于代码上色, 更方便编辑, 你自己有或者不介意干脆记事本也行

2. 下载bot
   1. `按住shift + 右键`,点击`在此处打开 Powershell 窗口` / `Open in Windows Terminal`

   ```shell
   git clone https://github.com/LYshiying/ui_bot
   ```

3. 安装依赖

   ```shell
   pip3 install -r requirements.txt
   # 或者使用清华大学代理源, 国内会快不少
   pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt 
   ```

4. 将`config-sample.py`改为`config.py`并打开根据注释编辑
   1. 未来新增插件可能会在配置文件新增几个变量, 如果发现新增插件请查看[更新日志](/zh-cn/update-log/)是否需要……
   2. 或是留意是否存在以下报错:
      1. `ImportError: cannot import name 'xxxxx' from 'config'`
      2. `AttributeError: module 'config' has no attribute 'xxxxx'`

5. 安装并配置[go-cqhttp](https://github.com/Mrs4s/go-cqhttp)
   1. 这边建议参考[Nonebot1官方提供的安装教程](https://docs.nonebot.dev/guide/installation.html)

6. 启动bot以及go-cqhttp
   1. 会自动创建一些配置文件以及目录, 因为一开始没有配置文件可能日志满屏warning, 并不重要

7. 在qq私聊bot, 发送`bot状态`, `使用帮助`等查看
   1. 由于个人水平的问题……bot的使用帮助其实有点鸡肋, 可以查看[使用bot](/zh-cn/usage/)来简单了解插件相关的使用
