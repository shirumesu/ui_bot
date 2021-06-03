import cv2
import numpy as np
from PIL import ImageFont, ImageDraw, Image
import textwrap
import random
import os
import string

import config


async def process_pic(content, book_name):
    if not content and not book_name:
        return os.path.join(config.res, 'source', 'mkmeme', 'luxun_say', 'sample.png')
    text = content

    font_path = os.path.join(config.res, 'source',
                             'mkmeme', 'luxun_say', 'msyh.ttf')
    font_size = 48

    image = Image.open(os.path.join(config.res, 'source',
                                    'mkmeme', 'luxun_say', 'luxun.png'))
    image_draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(font_path, font_size)
    font2 = ImageFont.truetype(font_path, 30)

    for x, y in enumerate(textwrap.wrap(text, 15)):
        font_length = font.getsize(y)

        while font_length[0] > 480:
            font_size -= 5
            font = ImageFont.truetype(font_path, font_size)
            font_length = font.getsize(y)

        if font_length[0] > 5:
            image_draw.text((240-font_length[0]/2, 350-font_length[1]/2 + (
                x if y == content else x-1)*font_length[1]), y, fill='white', font=font)

    if book_name:
        bn_num = len(book_name) + 0.5
    else:
        bn_num = 0

    bookname = f"——鲁迅{f'《{book_name}》' if book_name is not None else ''}"
    image_draw.text((320 - round(bn_num*30), 400),  bookname,
                    font=font2, fill=(255, 255, 255))

    bk_img = np.array(image)
    save_name = ''.join(random.sample(string.ascii_letters + string.digits, 8))
    save_path = os.path.join(config.res, 'cacha', 'mkmeme', save_name + '.png')
    cv2.imwrite(save_path, bk_img)
    return save_path
