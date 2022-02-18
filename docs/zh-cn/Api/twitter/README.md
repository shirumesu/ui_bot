# 推特开发者账号申请

> 由于我已经拥有开发者账号了, 以下教程是凭借记忆和网上其他教程写的, 不保证完全就是我当初的操作, 更不保证成功

## 你需要准备的
1. 一个正常的推特账号(并且**绑定了邮箱**)
2. 一个神必的上网环境
3. 属于你自己独一无二的脑子

## 开始申请
1. 首先请来到[推特](https://twitter.com/home)登录
   1. 你需要一个推特账号, 这里我没法帮你, 如果推特不支持内地手机号申请, 你也可以试试虚拟邮箱 虚拟手机号等方式。
2. 来到[推特开发者平台](https://developer.twitter.com/en/apps)
   1. 此时页面右上角应该显示你的头像(即**你已登录推特**)
   2. 点击右上角的`Sign up`
3. 填写相关信息
   1. 应该会问你`申请账号的用途`、`你的身份`等消息, 由于据说开发者账号审核非常严格, 请尽量按实填写
   2. 对于`申请账号的用途`, **据说**填写 学生, 课业研究 相关的会有更高的成功率~~具体自己吹吧~~
4. 等待邮件
   1. 提交后会由推特审核, 在一段时间(大概几天)后会回复是否通过的结果到你的邮箱, 请注意检查

## 申请Api
1. 当你拥有一个`推特开发者`账号后
   1. 登录,来到[管理页面](https://developer.twitter.com/en/portal/projects-and-apps)
   2. 应该有一项为`Standalone Apps`, 点击他下面的`+ Create App`
   3. 填入应用名字, 这里任意
2. 拥有一个应用后
   1. 回到[管理页面](https://developer.twitter.com/en/portal/projects-and-apps)点击新建应用的**齿轮**进入设置页面
   2. 点击`App details`右边的`Edit`
   3. 点击`Keys and tokens`
   4. `Consumer Keys`以及`Authentication Tokens`, 分别点击`Regenerate`并记下他们(一共应该有各两项, 总共四项)
3. 填入`config.py`
   1. 请按以下方式一一对应填入:
   2. `Consumer Keys → API Key` → `config.py → API_key_for_Twitter`
   3. `Consumer Keys → API Key Secret` → `config.py → API_secret_key_for_Twitter`
   4. `Authentication Tokens → Access Token` → `config.py → Access_token_for_Twitter`
   5. `Authentication Tokens → Access Token Secret` → `config.py → Access_token_secret_for_Twitter`