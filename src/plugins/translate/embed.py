import textwrap
from PIL import Image, ImageDraw, ImageFont
import os
import math

from src.plugins.translate import baidu

import config


async def process_photo(
    words: dict,image_path: str, vertical: bool
) -> str:
    """单张图片的处理函数,会将ocr结果进一步解析,并且翻译,最后传回进行图片编辑

    Args:
        words (dict): ocr结果
        image_path (str): 图片下载保存的路径
        vertical (bool): 图片是否为竖版,竖版横版处理有一点不一样

    Returns:
        str: 保存的路径
    """
    size = Image.open(image_path).size
    data_list = [
        {
            "top": int(x["location"]["top"]),
            "left": int(x["location"]["left"]),
            "width": int(x["location"]["width"]),
            "height": int(x["location"]["height"]),
            "words": x["words"],
        }
        for x in words
    ]
    data_list = data_list[::-1] if vertical else data_list

    trans_text = []
    sente_result = []
    cacha_word = []
    pos_data_for_word = []

    for word in data_list:
        if not cacha_word:
            cacha_word.append(word)
            sentense = word["words"]
            continue
        if abs(word["top"] - cacha_word[-1]["top"]) <= round(size[0] * 0.02) and abs(
            word["left"] - cacha_word[-1]["left"]
        ) <= round(size[1] * 0.05):
            sentense += word["words"]
            cacha_word.append(word)
            continue
        else:
            pos_data_for_word.append(cacha_word)
            sentense = (
                sentense.replace(",", "")
                if word["left"] <= word["height"]
                else sentense
            )
            sente_result += await baidu.baidu_fanyi(sentense)
            trans_text.append([sentense, "".join(sente_result)])
            sentense = word["words"]
            cacha_word = []
            sente_result = []
            cacha_word.append(word)

    pos_data_for_word.append(cacha_word)
    sentense = sentense.replace(",", "") if word["left"] <= word["height"] else sentense
    sente_result += await baidu.baidu_fanyi(sentense)
    trans_text.append([sentense, "".join(sente_result)])

    words_data = []

    for index, i in enumerate(pos_data_for_word):
        top = (min([x["left"] for x in i]), min([x["top"] for x in i]))
        down = (
            max([x["left"] + x["width"] for x in i]),
            max([x["top"] + x["height"] for x in i]),
        )
        words = trans_text[index][0]
        trans = trans_text[index][1]
        if i[0]["width"] <= i[0]["height"]:
            is_vertical = True
            text_size = i[0]["width"]
        else:
            is_vertical = False
            text_size = i[0]["height"]
        words_data.append(
            {
                "top": top,
                "down": down,
                "words": words,
                "trans": trans,
                "is_vertical": is_vertical,
                "text_size": text_size,
            }
        )

    return words_data, image_path


async def draw_white(image: Image.open, position_data: dict) -> Image.open:
    """对ocr识别出文字的地方进行涂白以写入文字

    Args:
        image (Image.open): 图片对象
        position_data (dict): ocr识别的位置信息

    Returns:
        Image.open: 返回突破对象
    """
    for y in range(position_data["top"][1], position_data["down"][1]):
        for x in range(position_data["top"][0], position_data["down"][0]):
            try:
                image.putpixel((x, y), (255, 255, 255))
            except Exception:
                continue
    return image


async def add_text(image: Image.open, words: dict) -> Image:
    """对横排的图片添加文字

    Args:
        image (Image.open): 图片对象
        words (dict): 文字信息

    Returns:
        Image: 图片对象
    """
    size_of_text = words["text_size"]
    image_draw = ImageDraw.Draw(image)
    fontstyle = ImageFont.truetype(
        os.path.join(config.res, "source", "translate", "simhei.ttf"),
        size_of_text,
        encoding="utf-8",
    )

    width_text = abs(words["top"][0] - words["down"][0]) / words["text_size"]
    height_text = abs(words["top"][1] - words["down"][1]) / words["text_size"]
    text_number = len(words["trans"])

    while (width_text * height_text) < text_number:
        words["text_size"] -= 5
        width_text = abs(words["top"][0] - words["down"][0]) / words["text_size"]
        height_text = abs(words["top"][1] - words["down"][1]) / words["text_size"]

    down_tigg = words["text_size"] + 5
    for x, y in enumerate(textwrap.wrap(words["trans"], round(width_text))):
        image_draw.text(
            (words["top"][0], words["top"][1] + x * down_tigg),
            text=y,
            fill=(0, 0, 0),
            font=fontstyle,
        )
    return image


async def add_text_for_manga(image: Image.open, words: dict) -> Image.open:
    """对竖排的漫画类文字添加文字

    Args:
        image (Image.open): 图片对象
        words (dict): 文字的数据,包含位置以及原文,翻译结果,字体大小等

    Returns:
        Image.open: 图片对象
    """
    y_diff = abs(words["top"][1] - words["down"][1])
    x_diff = abs(words["top"][0] - words["down"][0])
    vertical_text = int(math.ceil(y_diff / words["text_size"]))

    total_pixiv_for_text = (y_diff * x_diff) / (words["text_size"] * words["text_size"])
    text_number = len(words["trans"])

    while total_pixiv_for_text < text_number:
        words["text_size"] -= 5
        vertical_text = int(math.ceil(y_diff / words["text_size"]))
        total_pixiv_for_text = (y_diff * x_diff) / (
            words["text_size"] * words["text_size"]
        )
        text_number = len(words["trans"])

    ttwrap = textwrap.wrap(words["trans"], vertical_text)
    image_draw = ImageDraw.Draw(image)
    fontstyle = ImageFont.truetype(
        os.path.join(config.res, "source", "translate", "simhei.ttf"),
        words["text_size"],
        encoding="utf-8",
    )
    down_tigg = words["text_size"] + 5
    right_tigg = words["text_size"] + 5
    ray = (words["down"][0] - words["text_size"], words["top"][1])
    for right_times, i in enumerate(ttwrap):
        for times, text in enumerate(i):
            image_draw.text(
                (ray[0] - right_tigg * right_times, ray[1] + down_tigg * times),
                text=text,
                fill=(0, 0, 0),
                font=fontstyle,
            )

    return image


async def process_manga(data_list: list[dict], image_path: str) -> str:
    """对单张图片进行涂白和嵌字的工序

    Args:
        data_list (list[dict]): ocr识别的文字再次封装
        image_path (str): 图片下载的路径(同时也作为最后保存覆盖的路径)

    Returns:
        str: 保存的路径
    """
    image = Image.open(image_path).convert("RGB")

    for i in data_list:
        image = await draw_white(image, i)
        if i["is_vertical"]:
            image = await add_text_for_manga(image, i)
        else:
            image = await add_text(image, i)

    image.save(image_path)
    return image_path
