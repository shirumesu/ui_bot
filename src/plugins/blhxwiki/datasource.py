import os
import string
import random
import platform
import time
import traceback

from typing import Union
from aiocqhttp.message import MessageSegment
from loguru import logger

try:
    from selenium import webdriver
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.chrome.options import Options

    NOT_SELENIUM = False
except:
    logger.info("没有找到模块:selenium或导入错误 已自动禁用")
    NOT_SELENIUM = True

try:
    from playwright.sync_api import Playwright, sync_playwright

    NOT_PLAYWRIGHT = False
except:
    logger.info("没有找到模块:playwright或导入错误 已自动禁用")
    NOT_PLAYWRIGHT = True

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
            logger.debug(f"判断系统为:{self.sys},使用对应方法处理")
            if self.sys == "Windows":
                return self.win_driver(url)
            elif self.sys == "Linux":
                return self.linux_driver(url)
        except Exception as e:
            logger.debug(e)
            logger.error(f"暂不支持{self.sys}系统,尝试使用playwright进行截图")
            try:
                with sync_playwright() as playwright:
                    return self.play_wright(url, playwright)
            except:
                logger.info("截图失败,该功能无法使用")
                logger.debug(traceback.format_exc())
            return "该插件目前处于不可用状态"

    def win_driver(self, url: str) -> Union[str, MessageSegment]:
        """windows下获取页面截图的主要函数

        Args:
            url (str): 需要被截图的页面

        Returns:
            Union[str,MessageSegment]: 返回错误信息,或是成功保存的图片CQ码
        """
        chrome_options = Options()
        chrome_options.add_argument("headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")

        try:
            driver = webdriver.Chrome(chrome_options=chrome_options)
        except:
            try:
                chromedriver = os.path.join(
                    config.res, "source", "blhxwiki", "chromedriver.exe"
                )
                os.environ["webdriver.chrome.driver"] = chromedriver
                if not os.path.exists(chromedriver):
                    logger.warning("没有检测到对应的chrome-driver,无法进行截图")
                    return "该插件目前处于不可用状态"
                driver = webdriver.Chrome(chromedriver, chrome_options=chrome_options)
            except:
                logger.warning("检测到chromedriver存在但发生了错误,selenium无法使用")
                return "该插件目前处于不可用状态"

        logger.info(f"尝试用driver获取页面:{url}")
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
        chrome_options = Options()
        chrome_options.add_argument("headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")

        try:
            driver = webdriver.Chrome(chrome_options=chrome_options)
        except:
            logger.info("没有在系统环境找到对应的chromedriver,尝试在res文件夹下寻找")
            try:
                chromedriver = os.path.join(
                    config.res, "source", "blhxwiki", "chromedriver"
                )
                if not os.path.exists(chromedriver):
                    logger.warning("没有检测到对应的chrome-driver，无法进行截图")
                driver = webdriver.Chrome(chromedriver, chrome_options=chrome_options)
                os.environ["webdriver.chrome.driver"] = chromedriver
            except:
                return "该插件目前处于不可用状态"
        logger.info(f"尝试用driver获取页面:{url}")
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

    def play_wright(self, url: str, playwright: Playwright) -> MessageSegment:
        """当selenium无法使用的时候,使用`playwright`进行截图

        已知问题: 截图可能重复,并且存在懒加载导致部分图片未能加载的情况

        Args:
            url (str): 需要截图的连接地址
            playwright (Playwright): Playwright

        Returns:
            MessageSegment: 保存的CQ码
        """
        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context()

        # Open new page
        page = context.new_page()

        page.goto(url)

        pac_name = (
            "".join(random.sample(string.digits + string.ascii_letters, 8)) + ".png"
        )
        pac_path = os.path.join(config.res, "cacha", "blhxwiki", pac_name)

        page.screenshot(path=pac_path)

        context.close()
        browser.close()

        return MessageSegment.image(r"file:///" + pac_path)
