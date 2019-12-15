# -*- coding:utf-8 -*-

"""
 Verion: 1.0
 Author: Helixcs
 File: example.py
 Time: 2019/12/15
"""
from selenium.webdriver import ChromeOptions

from api import GoogleArtsCrawlerProcess, GoogleArtsCrawlerOption

if __name__ == '__main__':
    chrome_option = ChromeOptions()
    chrome_option.add_argument("--headless")
    chrome_option.add_argument('--no-sandbox')
    chrome_option.add_argument('--disable-dev-shm-usage')
    chrome_option.add_argument('--disable-gpu')
    chrome_option.add_argument("--disable-dev-shm-usage")
    chrome_option.add_argument("start-maximized")
    chrome_option.add_argument("disable-infobars")
    chrome_option.add_argument("--disable-extensions")

    GoogleArtsCrawlerProcess(gaco=GoogleArtsCrawlerOption()
                             .set_url("https://artsandculture.google.com/asset/madame-moitessier/hQFUe-elM1npbw")
                             .set_chrome_options(chrome_option)
                             .set_need_download_webdrive(True)
                             # .set_webdriver_execute_path("webdriver/chromedriver")
                             .set_partial_tmp_path("custom_partial_dir")
                             .set_output_path("custom_output_dir")
                             .set_output_filename("custom.jpg")
                             .set_need_clear_cache(True)
                             .set_debug(True)
                             .prepare_options()).process()
