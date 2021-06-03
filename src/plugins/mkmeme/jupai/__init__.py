import os
import random
import string
import textwrap
from PIL import ImageDraw, Image, ImageFont

import config


font_path = os.path.join(config.res, 'source', 'mkmeme', 'jupai', 'SimHei.ttf')
image_path = os.path.join(config.res, 'source', 'mkmeme', 'jupai', 'jupai.png')
cacha_path = os.path.join(config.res, 'cacha', 'mkmeme')
font_center = (400, 650)
color = 'black'
font_max = 380
font_sub = 10


async def img(text: str) -> str:
    """拼合举牌表情的主函数

    Args:
        text (str): 需要拼合的文字

    Returns:
        str: 保存路径
    """
    if not text:
        return image_path

    font_size = 80

    image = Image.open(image_path)
    image_draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(font_path, font_size)
    for x, i in enumerate(textwrap.wrap(text, 10)):
        font_length = font.getsize(i)

        while font_length[0] > font_max:
            font_size -= font_sub
            font = ImageFont.truetype(font_path, font_size)
            font_length = font.getsize(i)

        if font_length[0] > 5:
            image_draw.text((font_center[0]-font_length[0]/2, font_center[1] - font_length[1]/2 + (
                x if i == text else x-1)*(font_length[1])), i, fill=color, font=font)

    image_name = ''.join(random.sample(
        string.ascii_letters + string.digits, 8)) + '.png'
    save_path = os.path.join(cacha_path, image_name)
    image.save(save_path)

    return save_path
