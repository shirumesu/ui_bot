# 各类cookie获取

## pixiv
1. 来到[pixiv](https://www.pixiv.net/)
2. 打开开发者工具
   1. 谷歌快捷键为`F12`
   2. 点击网络/Network
3. 随意打开一个作品
   1. 这时候你的开发者工具页面应该有一堆东西刷新
   2. 等待网页加载完成
4. 按时间右边的一项(中文为`瀑布`)排序(排序标志为`正三角形`)
   1. 点击第一项, 点击标头(`x`右边第一项)
   2. 拉到最下面的`请求标头`, 找到一项为`cookie`
      1. 右键-`复制值`
5. 将其填入`config.py`中的`pixiv_cookie`(记得用双引号括起来)

## 彩云续写
1. 来到[彩云网页版](https://if.caiyunai.com/#/)
   1. 登录
2. 打开开发者工具
3. 点击控制台(英文应该是`console`)
4. 输入以下文字
```
localStorage.cy_dream_user
```
5. 应该会输出`'{"uid":"something"}'`
6. 将`something`填入`config.py`的`caiyun_token`