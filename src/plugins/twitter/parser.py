from src.plugins.twitter.translate import baidu_translate


async def sendmsg(msg: dict) -> dict:
    """tweepy传回的result中不存在被回复的推文,因此进行额外获取与整理

    import方面: 由于相互导入,无法在导入前导入插件主文件的函数,因此在现在导入

    Args:
        msg (dict): 被回复的推文(tweepy api获取回来的结果)

    Returns:
        dict: 整理封装好的推文信息
    """
    from src.plugins.twitter import get_user, dl_image

    data = {
        "senderid": msg["user"]["name"],
        "text": None,
        "have_img": False,
        "imgurl": [],
        "urls_old": [],
        "urls_new": [],
        "isvideo": False,
        "isreply": False,
        "replyuser": None,
        "isRT": False,
        "RTuser": None,
        "RTtext": None,
        "isquote": False,
        "quoteuser": None,
        "quotetext": None,
        "quote_url_old": [],
        "quote_url_new": [],
        "quote_in_img": False,
        "quote_in_video": False,
        "quote_media_url": [],
        "lastid": msg["id"],
        "lang": msg["lang"],
        "quotelang": "zh",
        "RTlang": "zh",
        "translate_result": "翻译错误",
        "quote_translate_result": "翻译错误",
        "no_china": False,
        "quote_in_not_china": False,
        "is_tweet": False,
        "seq": ""
    }
    # 回复
    if msg["in_reply_to_status_id"] != None:
        data["isreply"] = True
        user_name = await get_user(msg["in_reply_to_screen_name"])
        try:
            if user_name == "访问失败":
                data["replyuser"] = msg["in_reply_to_screen_name"]
        except Exception:
            pass
        data["replyuser"] = user_name["name"]
        data["text"] = msg["full_text"]
        try:
            if msg["entities"]["urls"]["media"]:
                if msg["entities"]["urls"]["media"]["type"] == "photo":
                    data["imgurl"].append(
                        msg["entities"]["media"][0]["media_url"])
                    data["have_img"] = True
                else:
                    data["isvideo"] = True
        except:
            pass
        try:
            for i in msg["entities"]["urls"]:
                data["urls_old"].append(i["url"])
                data["urls_new"].append(i["expanded_url"])
        except:
            pass
        try:
            if msg["extended_entities"]:
                for i in msg["extended_entities"]["media"]:
                    if i["type"] == "photo":
                        # data["imgurl"].append(i["media_url"])
                        data["imgurl"].append(i["media_url"])
                        data["have_img"] = True
                    else:
                        data["isvideo"] = True
        except:
            pass

    # 转推
    elif "retweeted_status" in msg:
        data["isRT"] = True
        data["RTlang"] = msg["retweeted_status"]["lang"]
        try:
            data["RTtext"] = msg["retweeted_status"]["full_text"]
        except:
            pass
        #data["RTuser"] = msg["full_text"][4:].split(":", 1)[0]
        data["RTuser"] = msg["retweeted_status"]["user"]["name"]
        try:
            if msg["retweeted_status"]["entities"]["urls"]["media"]:
                if msg["retweeted_status"]["entities"]["urls"]["media"][
                        "type"] == "photo":
                    data["imgurl"].append(msg["retweeted_status"]["entities"]
                                          ["media"][0]["media_url"])
                    data["have_img"] = True
                else:
                    data["isvideo"] = True
        except:
            pass
        try:
            for i in msg["retweeted_status"]["entities"]["urls"]:
                data["urls_old"].append(i["url"])
                data["urls_new"].append(i["expanded_url"])
        except:
            pass
        try:
            if msg["retweeted_status"]["extended_entities"]:
                for i in msg["retweeted_status"]["extended_entities"]["media"]:
                    if i["type"] == "photo":
                        data["imgurl"].append(i["media_url"])
                        data["have_img"] = True
                    else:
                        data["isvideo"] = True
        except:
            pass

    # 引用推文
    elif msg["is_quote_status"] == True:
        data["isquote"] = True
        data["quotetext"] = msg["quoted_status"]["full_text"]
        data["senderid"] = msg["user"]["name"]
        data["quoteuser"] = msg["quoted_status"]["user"]["name"]
        data["quotelang"] = msg["quoted_status"]["lang"]
        try:
            data["text"] = msg["full_text"]
        except:
            pass
        try:
            for i in msg["entities"]["urls"]:
                data["urls_old"].append(i["url"])
                data["urls_new"].append(i["expanded_url"])
        except:
            pass
        try:
            if msg["entities"]["urls"]["media"]:
                if msg["entities"]["urls"]["media"]["type"] == "photo":
                    data["imgurl"].append(
                        msg["entities"]["media"][0]["media_url"])
                    data["have_img"] = True
                else:
                    data["isvideo"] = True
        except:
            pass
        try:
            if msg["extended_entities"]:
                for i in msg["extended_entities"]["media"]:
                    if i["type"] == "photo":
                        data["imgurl"].append(i["media_url"])
                        data["have_img"] = True
                    else:
                        data["isvideo"] = True
        except:
            pass

    # 发推
    else:
        try:
            data["text"] = msg["full_text"]
        except:
            pass
        try:
            if msg["entities"]["urls"]["media"]:
                if msg["entities"]["urls"]["media"]["type"] == "photo":
                    data["imgurl"].append(
                        msg["entities"]["media"][0]["media_url"])
                    data["have_img"] = True
                else:
                    data["isvideo"] = True
        except:
            pass
        try:
            if msg["extended_entities"]:
                for i in msg["extended_entities"]["media"]:
                    if i["type"] == "photo":
                        data["imgurl"].append(i["media_url"])
                        data["have_img"] = True
                    else:
                        data["isvideo"] = True
        except:
            pass
        try:
            for i in msg["entities"]["urls"]:
                data["urls_old"].append(i["url"])
                data["urls_new"].append(i["expanded_url"])
        except:
            pass
    # 去掉多余链接
    if data["isquote"] == True:
        data["text"] = data["text"][:-23]
    if data["text"] != None:
        if (data["isvideo"] == True or data["have_img"] == True
                and data["text"][-23:-10] == "https://t.co/") == True:
            data["text"] = data["text"][:-23]

    # 去掉多余的@user/reply_link
    if data["isreply"] == True:
        try:
            data["text"] = data["text"].rsplit("https://", 1)[0].strip()
        except:
            pass
        try:
            if f"@{msg['in_reply_to_screen_name']} " in data["text"]:
                data["text"] = data["text"].rsplit(" ", 1)[1]
        except:
            pass

    # 替换链接
    try:
        i = 0
        for old in data["urls_old"]:
            data["text"] = data["text"].replace(old, data["urls_new"][i])
            i = i + 1
    except:
        pass

    # 翻译
    if data["lang"] != "zh":
        data["no_china"] = True
        try:
            data["translate_result"] = await baidu_translate(
                data["text"])
        except:
            pass

    if data["imgurl"]:
        data["seq"] = await dl_image(data["imgurl"])

    return data
