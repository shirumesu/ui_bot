import os
import string
import random
import platform
import time
from typing import Union
from aiocqhttp.message import MessageSegment
from loguru import logger
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options


import config


class driver:
    def __init__(self) -> None:
        self.sys = platform.system()

    def get_pac(self, url: str) -> Union[str, MessageSegment]:
        """判断使用哪一种方式去获取截图

        Args:
            url (str): 需要截图的页面

        Returns:
            Union[str,MessageSegment]: 返回错误信息,或是成功保存的图片CQ码
        """
        try:
            if self.sys == "Windows":
                return self.win_driver(url)
            elif self.sys == "Linux":
                return self.linux_driver(url)
        except:
            logger.error(f"暂不支持{self.sys}系统")
            return "该插件目前处于不可用状态"

    def win_driver(self, url: str) -> Union[str, MessageSegment]:
        """windows下获取页面截图的主要函数

        Args:
            url (str): 需要被截图的页面

        Returns:
            Union[str,MessageSegment]: 返回错误信息,或是成功保存的图片CQ码
        """
        chromedriver = os.path.join(
            config.res, "source", "blhxwiki", "chromedriver.exe"
        )
        if not os.path.exists(chromedriver):
            logger.warning("没有检测到对应的chrome-driver,无法进行截图")
            return "该插件目前处于不可用状态"
        os.environ["webdriver.chrome.driver"] = chromedriver

        chrome_options = Options()
        chrome_options.add_argument("headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        driver = webdriver.Chrome(chromedriver, chrome_options=chrome_options)
        driver.get(url)
        try:
            WebDriverWait(driver, 15)

            height = driver.execute_script(
                "return document.documentElement.scrollHeight"
            )

            driver.set_window_size(1400, height)  # blhxwiki的宽度为1400 可以设置其他
            WebDriverWait(driver, 15)
            driver.execute_script(f"window.scrollTo(0,{height})")

            # 应对懒加载问题
            s = 1
            height = driver.execute_script("return document.body.clientHeight")
            while True:
                if s * 500 < height:
                    js_move = f"window.scrollTo(0,{s*500})"
                    driver.execute_script(js_move)
                    time.sleep(0.2)
                    WebDriverWait(driver, 15)
                    height = driver.execute_script("return document.body.clientHeight")
                    s += 1
                else:
                    break
        except:
            logger.error("等待页面加载元素超时!")
            return "等待页面加载元素超时！"
        pac_name = (
            "".join(random.sample(string.digits + string.ascii_letters, 8)) + ".png"
        )
        pac_path = os.path.join(config.res, "cacha", "blhxwiki", pac_name)
        driver.save_screenshot(pac_path)
        driver.quit()

        return MessageSegment.image(r"file:///" + pac_path)

    def linux_driver(self, url: str) -> Union[str, MessageSegment]:
        """windows下获取页面截图的主要函数

        Args:
            url (str): 需要被截图的页面

        Returns:
            Union[str,MessageSegment]: 返回错误信息,或是成功保存的图片CQ码
        """
        chromedriver = os.path.join(config.res, "source", "blhxwiki", "chromedriver")
        if not os.path.exists(chromedriver):
            logger.warning("没有检测到对应的chrome-driver,无法进行截图")
            return "该插件目前处于不可用状态"
        os.environ["webdriver.chrome.driver"] = chromedriver

        chrome_options = Options()
        chrome_options.add_argument("headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        driver = webdriver.Chrome(chromedriver, chrome_options=chrome_options)
        driver.get(url)
        try:
            WebDriverWait(driver, 15)

            height = driver.execute_script(
                "return document.documentElement.scrollHeight"
            )

            driver.set_window_size(1400, height)  # blhxwiki的宽度为1400 可以设置其他
            WebDriverWait(driver, 15)
            driver.execute_script(f"window.scrollTo(0,{height})")

            # 应对懒加载问题
            s = 1
            height = driver.execute_script("return document.body.clientHeight")
            while True:
                if s * 500 < height:
                    js_move = f"window.scrollTo(0,{s*500})"
                    driver.execute_script(js_move)
                    time.sleep(0.2)
                    WebDriverWait(driver, 15)
                    height = driver.execute_script("return document.body.clientHeight")
                    s += 1
                else:
                    break
        except:
            logger.error("等待页面加载元素超时!")
            return "等待页面加载元素超时！"
        pac_name = (
            "".join(random.sample(string.digits + string.ascii_letters, 8)) + ".png"
        )
        pac_path = os.path.join(config.res, "cacha", "blhxwiki", pac_name)
        driver.save_screenshot(pac_path)
        driver.quit()

        return MessageSegment.image(r"file:///" + pac_path)
