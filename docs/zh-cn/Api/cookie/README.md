# 各类cookie获取

## pixiv

1. 来到[pixiv](https://www.pixiv.net/)登录
2. 打开开发者工具
   1. 谷歌快捷键为`F12`
   2. 点击网络/Network
3. 点击控制台(英文应该是`console`)
4. 输入以下文字并复制输出的内容

   ```javascript
   document.cookie
   ```

5. 将其填入`config.py`中的`pixiv_cookie`

## 彩云续写

1. 来到[彩云网页版](https://if.caiyunai.com/#/)
   1. 登录
2. 打开开发者工具
3. 点击控制台(英文应该是`console`)
4. 输入以下文字

   ```javascript
   localStorage.cy_dream_user
   ```

5. 应该会输出`'{"uid":"something"}'`
6. 将`something`填入`config.py`的`caiyun_token`
