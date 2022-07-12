import base64
import os
import time
import traceback
import urllib.request
from concurrent.futures import ThreadPoolExecutor  # 导入需要的包

import cv2
import numpy as np
from selenium import webdriver


def base64_to_cv2(base64_str):
    imgString = base64.b64decode(base64_str)
    nparr = np.frombuffer(imgString, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return image


def download_pic(url, name, path):
    if not os.path.exists(path):
        os.makedirs(path)
    res = urllib.request.urlopen(url, timeout=3).read()
    with open(os.path.join(path, name + '.jpg'), 'wb') as file:
        file.write(res)
        file.close()


class Crawler_google_images:
    # 初始化
    def __init__(self, keyword, picCount):
        self.keyword = keyword
        self.url = 'https://www.google.com.hk/search?q=' + keyword + '&source=lnms&tbm=isch'
        self.picCount = picCount
        self.threadPool = ThreadPoolExecutor(max_workers=10)  # 线程池的池子大小

    # 获得Chrome驱动，并访问url
    def init_browser(self):
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--disable-infobars")
        # 设置谷歌浏览器的页面无可视化，如果需要可视化请注释这两行代码
        # chrome_options.add_argument('--headless')
        # chrome_options.add_argument('--disable-gpu')
        browser = webdriver.Chrome(chrome_options=chrome_options)
        # 访问url
        browser.get(self.url)
        # 最大化窗口，之后需要爬取窗口中所见的所有图片
        browser.maximize_window()
        return browser

    # 下载图片
    def download_images(self, driver):
        # 路径不存在时创建一个
        if not os.path.exists(self.keyword):
            os.makedirs(self.keyword)

        count = 0  # 图片序号
        pos = 0

        # 图片是有限的，这步操作向下滚动到最底下
        last_height = driver.execute_script('return document.body.scrollHeight')
        while True:
            driver.execute_script('window.scrollTo(0,document.body.scrollHeight)')
            time.sleep(1)  # 取决于vpn速度
            new_height = driver.execute_script('return document.body.scrollHeight')
            try:
                driver.find_element(by="xpath", value='//*[@id="islmp"]/div/div/div/div/div[5]/input').click()
            except:
                pass
            if new_height == last_height:
                # 点击显示更多结果
                try:
                    driver.find_element(by="xpath",
                                        value='//*[@id="islmp"]/div/div/div/div[1]/div[2]/div[2]/input').click()
                except:
                    break
            last_height = new_height

        for i in range(1, self.picCount):
            try:
                button = driver.find_element(by="xpath",
                                             value='//*[@id="islrg"]/div[1]/div[' + str(i) + ']/a[1]/div[1]/img')

                # 此选项为下载缩略图
                # image_src = image.get_attribute("src")
                # image.click()  # 点开大图
                driver.execute_script("arguments[0].click();", button)
                time.sleep(4)  # 因为谷歌页面是动态加载的，需要给予页面加载时间，否则无法获取原图url，如果你的网络状况一般请适当延长
                # 获取原图的url
                image_real = driver.find_element(by="xpath",
                                                 value='//*[@id="Sva75c"]/div/div/div[3]/div[2]/c-wiz/div/div[1]/div[1]/div[3]/div/a/img')
                image_url = image_real.get_attribute("src")

                self.threadPool.submit(self.save_img, i, image_url)

                print(str(i) + ': ' + image_url)

            except:
                traceback.print_exc()

    def save_img(self, count, image_url):
        try:
            if "/9j/" in image_url:
                img = base64_to_cv2(image_url[image_url.index("/9j/"):])
                cv2.imwrite(os.path.join(self.keyword, str(count) + ".jpg"), img)
            else:
                filename = os.path.join(self.keyword, str(count) + ".jpg")
                res = urllib.request.urlopen(image_url, timeout=3).read()
                with open(filename, 'wb') as f:
                    f.write(res)
        except:
            traceback.print_exc()

    def run(self):
        browser = self.init_browser()
        self.download_images(browser)  # 可以修改爬取的图片数
        self.threadPool.shutdown(wait=True)  # 释放线程池资源
        browser.quit()

        print("############爬取完成")


if __name__ == '__main__':
    craw = Crawler_google_images(keyword="cat", picCount=100)
    craw.run()

