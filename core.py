import time
import base64
import re
import collections
from zipfile import ZipFile

import numpy as np
import os
import sys
import shutil
from typing import Optional, Union
from urllib3.util.url import parse_url
from urllib3 import PoolManager
from urllib3.contrib.socks import SOCKSProxyManager
from selenium import webdriver
from selenium.webdriver import ChromeOptions
from PIL import Image
from slugify import slugify

WINDOWS = os.name == 'nt'
LINUX = sys.platform.startswith('linux')
DARWIN = sys.platform.startswith('darwin')


def is_blank(value: Optional[Union[int, str, dict, list, bytes, tuple, object]]) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return True if value is None or value.strip('') == '' else False
    if isinstance(value, dict):
        return True if len(value) < 1 else False
    if isinstance(value, list):
        return True if len(value) < 1 else False
    if isinstance(value, bytes):
        return True if value == b'' else False
    # (None,None) ==> False
    if isinstance(value, tuple):
        if len(value) < 1:
            return True
        for i in value:
            if i is not None:
                return False
        return True
    if isinstance(value, set):
        return True if len(value) < 1 else False

    return value is None


def is_not_blank(value: Optional[Union[int, str, dict, list, tuple,]]) -> bool:
    return not is_blank(value=value)


DEFAULT_GCO_SIZE = 12000
DEFAULT_GCO_OUTPUT_PATH = 'output'
DEFAULT_GCO_PARTIAL_PATH = 'partial'
DEFAULT_GCO_INIT_DELAY = 5


class GoogleArtsCrawlerOption(object):
    def __init__(self,
                 url: str = None,
                 chrome_options: ChromeOptions = None,
                 webdriver_execute_path: str = None,
                 size: int = DEFAULT_GCO_SIZE,
                 init_delay_time: int = DEFAULT_GCO_INIT_DELAY,
                 blob_loading_delay_time: int = 2,
                 output_path: str = DEFAULT_GCO_OUTPUT_PATH,
                 output_filename: str = None,
                 partial_tmp_path: str = DEFAULT_GCO_PARTIAL_PATH,
                 need_download_webdrive: bool = False,
                 need_clear_cache: bool = True,
                 is_debug: bool = False):
        """
        GoogleArtsCrawlerOption
        Usage:
        ```
            GoogleArtsCrawlerOption()
                                 .set_url("https://artsandculture.google.com/asset/madame-moitessier/hQFUe-elM1npbw")
                                 .set_chrome_options(chrome_option)
                                 .set_need_download_webdrive(True)
                                 # .set_webdriver_execute_path("webdriver/chromedriver")
                                 .set_partial_tmp_path("custom_partial_dir")
                                 .set_output_path("custom_output_dir")
                                 .set_output_filename("custom.jpg")
                                 .set_need_clear_cache(True)
                                 .prepare_options()
        ```
        :param url:                         google arts url.
        :param chrome_options:              chrome options , visit `https://chromedriver.chromium.org/capabilities` for detail.
        :param webdriver_execute_path:      webdrive executed path , if you do not set , it will auto download.
        :param size:                        webdrive simulated device size , default 120000.
        :param init_delay_time:             webdrive request url and set `init_delay_time` after render.
        :param blob_loading_delay_time:     webdrive get image blob  delay time if get filed at first time.
        :param output_path:                 custom output dir , default  `output`
        :param output_filename:             custom output filename, default arts name.
        :param need_download_webdrive       need download webdrive, default False , it will auto download webdrive if set True.
        :param partial_tmp_path:            custom partial tmp path , it will be deleted after finish, default `blob`.
        :param need_clear_cache:            auto clear webdriver download tmp  and partial images after finished.
        :param is_debug:

        """
        self._url = url
        self._chrome_options = chrome_options
        self._webdriver_execute_path = webdriver_execute_path
        self._size = size
        self._init_delay_time = init_delay_time
        self._blob_loading_delay_time = blob_loading_delay_time
        self._output_path = output_path
        self._output_filename = output_filename
        self._partial_tmp_path = partial_tmp_path
        self._is_debug: bool = is_debug
        self._need_download_webdrive = need_download_webdrive
        self._need_clear_cache = need_clear_cache

        pass

    def prepare_options(self):
        if is_blank(self._url):
            raise Exception("GoogleArtsCrawlerOption , url is blank!")
        uprs = parse_url(url=self._url)
        if not uprs.host == 'artsandculture.google.com':
            raise Exception("GoogleArtsCrawlerOption, url netloc is not `artsandculture.google.com`")
        self._url = "https://{0}{1}".format(uprs.host, uprs.path)

        # download webdriver
        if self._webdriver_execute_path is None and self._need_download_webdrive:
            default_webdrive_path = "webdriver"
            if os.path.isdir(default_webdrive_path):
                default_webdrive_files = os.listdir(default_webdrive_path)
                if len(default_webdrive_files) > 0:
                    default_webdrive_execute_file = os.path.join(default_webdrive_path, default_webdrive_files[0])
                    if os.path.isfile(default_webdrive_execute_file):
                        print("==> webdriver has exist at {0}".format(default_webdrive_execute_file))
                        self._webdriver_execute_path = default_webdrive_execute_file

            if self._webdriver_execute_path is None:
                if WINDOWS:
                    webdriver_download_url = "http://chromedriver.storage.googleapis.com/78.0.3904.70/chromedriver_win32.zip"
                elif DARWIN:
                    webdriver_download_url = "http://chromedriver.storage.googleapis.com/78.0.3904.70/chromedriver_mac64.zip"
                elif LINUX:
                    webdriver_download_url = "http://chromedriver.storage.googleapis.com/78.0.3904.70/chromedriver_linux64.zip"
                else:
                    raise Exception("GoogleArtsCrawlerOptions, unknown platform !")
                print("==> prepare download webdriver : {0}".format(webdriver_download_url))
                default_download_tmp = "tmp"
                webdriver_zip_filename = webdriver_download_url.split("/")[-1]
                webdriver_local_zip_filepath = os.path.join(default_download_tmp, webdriver_zip_filename)

                # not exist
                if not os.path.isfile(webdriver_local_zip_filepath):
                    # proxy = SOCKSProxyManager('socks5://localhost:1086/')
                    http = PoolManager()
                    response = http.request('GET', webdriver_download_url, preload_content=False)
                    if not os.path.isdir(default_download_tmp):
                        os.mkdir(default_download_tmp)
                    with open(webdriver_local_zip_filepath, mode="wb") as fd:
                        while True:
                            data = response.read(1024)
                            if not data:
                                break
                            fd.write(data)
                    response.release_conn()
                    print("==> webdriver zip file download finished , location at : {0}".format(
                        os.path.abspath(webdriver_local_zip_filepath)))
                else:
                    print("==> webdriver zip file has existed at {0}".format(webdriver_local_zip_filepath))
                with ZipFile(webdriver_local_zip_filepath, 'r') as zipfile:
                    zipfile.extractall(path=default_webdrive_path)

                if self._need_clear_cache:
                    shutil.rmtree(default_download_tmp)
                self._webdriver_execute_path = os.path.join(default_webdrive_path, os.listdir(default_webdrive_path)[0])

        if is_blank(self._webdriver_execute_path):
            raise Exception("GoogleArtsCrawlerOption , webdriver_execute_path is blank!")
        if not os.path.isfile(self._webdriver_execute_path):
            raise Exception("GoogleArtsCrawlerOption , webdriver_execute_path is not exist, this is file!")

        if LINUX or DARWIN:
            os.chmod(self._webdriver_execute_path, 0o777)

        mobile_emulation = {
            "deviceMetrics": {"width": self._size, "height": self._size, "pixelRatio": 1.0},
            "userAgent": "Mozilla/5.0 (Linux; Android 4.2.1; en-us; Nexus 5 Build/JOP40D) AppleWebKit/535.19 "
                         "(KHTML, like Gecko) Chrome/18.0.1025.166 Mobile Safari/535.19"}
        self._chrome_options.add_experimental_option("mobileEmulation", mobile_emulation)

        self._output_path = DEFAULT_GCO_OUTPUT_PATH if self._output_path is None else self._output_path
        self._size = DEFAULT_GCO_SIZE if self._size is None or self._size < 1 else self._size
        self._init_delay_time = DEFAULT_GCO_INIT_DELAY if self._init_delay_time is None or self._init_delay_time < 1 else self._init_delay_time

        if not os.path.isdir(self._output_path):
            os.makedirs(self._output_path)
        if not os.path.isdir(self._partial_tmp_path):
            os.makedirs(self._partial_tmp_path)
        if self._is_debug:
            print("GoogleArtsCrawlerOptions:")
            print("==> url:{0}".format(self._url))
            print("==> webdriver_execute_path:{0}".format(os.path.abspath(self._webdriver_execute_path)))
            print("==> output :{0}".format(os.path.abspath(self._output_path)))

        return self

    @property
    def url(self) -> str:
        return self._url

    def set_url(self, url):
        self._url = url
        return self

    @property
    def chrome_options(self) -> ChromeOptions:
        return self._chrome_options

    def set_chrome_options(self, chrome_options: ChromeOptions):
        self._chrome_options = chrome_options
        return self

    @property
    def webdriver_execute_path(self) -> str:
        return self._webdriver_execute_path

    def set_webdriver_execute_path(self, webdriver_execute_path: str):
        self._webdriver_execute_path = webdriver_execute_path
        return self

    @property
    def size(self) -> int:
        return self._size

    def set_size(self, size: int):
        self._size = size
        return self

    @property
    def init_delay(self) -> int:
        return self._init_delay_time

    def set_init_delay(self, init_delay_time: int):
        self._init_delay_time = init_delay_time
        return self

    @property
    def blob_loading_delay_time(self) -> int:
        return self._blob_loading_delay_time

    def set_blob_loading_delay_time(self, blob_loading_delay_time: int):
        self._blob_loading_delay_time = blob_loading_delay_time
        return self

    @property
    def output_path(self) -> str:
        return self._output_path

    def set_output_path(self, output_path: str):
        self._output_path = output_path
        return self

    @property
    def output_filename(self) -> str:
        return self._output_filename

    def set_output_filename(self, output_filename):
        self._output_filename = output_filename
        return self

    @property
    def partial_tmp_path(self):
        return self._partial_tmp_path

    def set_partial_tmp_path(self, partial_tmp_path: str):
        self._partial_tmp_path = partial_tmp_path
        return self

    @property
    def need_download_webdrive(self):
        return self._need_download_webdrive

    def set_need_download_webdrive(self, need_download_webdrive: bool):
        self._need_download_webdrive = need_download_webdrive
        return self

    @property
    def need_clear_cache(self):
        return self._need_clear_cache

    def set_need_clear_cache(self, need_clear_cache: bool):
        self._need_clear_cache = need_clear_cache
        return self

    @property
    def is_debug(self):
        return self._is_debug

    def set_debug(self, is_debug: bool):
        self._is_debug = is_debug
        return self


class GoogleArtsCrawlerProcess(object):
    def __init__(self, gaco: GoogleArtsCrawlerOption):
        """
        GoogleArtsCrawlerProcess
        Usage:
        ```
            GoogleArtsCrawlerProcess(gaco=GoogleArtsCrawlerOption()).process()
        ```
        :param gaco:  GoogleArtsCrawlerOption
        """

        self._gaco = gaco
        self._browser = webdriver.Chrome(options=self._gaco.chrome_options,
                                         executable_path=self._gaco.webdriver_execute_path)
        self._local_partial_tmp = None

    @property
    def gaco(self):
        return self._gaco

    def process(self):
        self._generate_image()
        if self._gaco.need_clear_cache:
            self._cleanup()
            pass

    # get blob content from blob:https://xxxxx
    def _get_blob_content(self, uri):
        """
        Saves blob to base64.
        """
        result = self._browser.execute_async_script("""
        var uri = arguments[0];
        var callback = arguments[1];
        var toBase64 = function(buffer){for(var r,n=new Uint8Array(buffer),t=n.length,a=new Uint8Array(4*Math.ceil(t/3)),i=new Uint8Array(64),o=0,c=0;64>c;++c)i[c]="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/".charCodeAt(c);for(c=0;t-t%3>c;c+=3,o+=4)r=n[c]<<16|n[c+1]<<8|n[c+2],a[o]=i[r>>18],a[o+1]=i[r>>12&63],a[o+2]=i[r>>6&63],a[o+3]=i[63&r];return t%3===1?(r=n[t-1],a[o]=i[r>>2],a[o+1]=i[r<<4&63],a[o+2]=61,a[o+3]=61):t%3===2&&(r=(n[t-2]<<8)+n[t-1],a[o]=i[r>>10],a[o+1]=i[r>>4&63],a[o+2]=i[r<<2&63],a[o+3]=61),new TextDecoder("ascii").decode(a)};
        var xhr = new XMLHttpRequest();
        xhr.responseType = 'arraybuffer';
        xhr.onload = function(){ callback(toBase64(xhr.response)) };
        xhr.onerror = function(){ callback(xhr.status) };
        xhr.open('GET', uri);
        xhr.send();
        """, uri)
        if type(result) == int:
            raise Exception("Request failed with status %s" % result)
        return base64.b64decode(result)

    def _pil_grid(self, images: list, max_horiz: int = np.iinfo(int).max) -> Image:
        """
        Generates one image out of many blobs.
        """
        n_images = len(images)
        n_horiz = min(n_images, max_horiz)
        h_sizes, v_sizes = [0] * n_horiz, [0] * (n_images // n_horiz)
        for i, im in enumerate(images):
            h, v = i % n_horiz, i // n_horiz
            h_sizes[h] = max(h_sizes[h], im.size[0])
            v_sizes[v] = max(v_sizes[v], im.size[1])
        h_sizes, v_sizes = np.cumsum([0] + h_sizes), np.cumsum([0] + v_sizes)
        im_grid = Image.new('RGB', (h_sizes[-1], v_sizes[-1]), color='white')
        for i, im in enumerate(images):
            im_grid.paste(im, (h_sizes[i % n_horiz], v_sizes[i // n_horiz]))
        return im_grid

    def _cleanup(self):
        if self._local_partial_tmp is not None:
            shutil.rmtree(self._local_partial_tmp)

    # 生成切片图，再组合成一张完整图片
    def _generate_image(self):
        try:
            print("==> staring request:{0}".format(self._gaco.url))
            self._browser.get(self._gaco.url)
            if self._gaco.init_delay is not None and self._gaco.init_delay > 0:
                time.sleep(self._gaco.init_delay)
            blobs = self._browser.find_elements_by_tag_name('img')
            print("==> get total partial images:{0}".format(len(blobs) - 2))
            title = slugify(self._browser.title)
            columns = []
            rows = []
            pil_images = []
            i = 0
            # 重建切片文件夹
            local_tmp_path = os.path.join(self._gaco.partial_tmp_path, title)
            self._local_partial_tmp = local_tmp_path
            if os.path.exists(local_tmp_path):
                shutil.rmtree(local_tmp_path)
            os.makedirs(local_tmp_path)

            for blob in blobs:
                if i > 2:
                    # Get number of rows and columns
                    style = blob.get_attribute('style')
                    style_end_index = style.find(');')
                    # -4 removes "z" translation
                    style = style[:style_end_index - 4]
                    style = style.replace('transform: translate3d(', '')
                    positions = list(map(int, re.findall(r'\d+', style)))

                    if len(positions) < 2:
                        # The positions are not available for this image - skip
                        continue

                    columns.append(positions[0])
                    rows.append(positions[1])

                    # Save blob to file
                    partial_image_src = blob.get_attribute('src')
                    while partial_image_src is None:
                        if self._gaco.blob_loading_delay_time and self._gaco.blob_loading_delay_time > 0:
                            time.sleep(self._gaco.blob_loading_delay_time)
                        partial_image_src = blob.get_attribute('src')

                    partial_image_content = self._get_blob_content(partial_image_src)
                    local_partial_filename = os.path.join(local_tmp_path, "{0}.jpg".format(i))
                    print("===> got blob content:{0} to {1}".format(blob.get_attribute('src'), local_partial_filename))

                    with open(local_partial_filename, 'wb') as fd:
                        fd.write(partial_image_content)
                        fd.flush()

                    # Create PIL objects list
                    pil_images.append(Image.open(local_partial_filename))
                i += 1
        finally:
            self._browser.close()

        print("==> partial images has downloaded, total:{0}".format(len(blobs) - 2))
        columns = len(collections.Counter(columns).keys())
        rows = len(collections.Counter(rows).keys())

        inverted_pil_images = []

        # by default images are crawled in vertical direction
        # we re-arrange list to create horizontally sorted list
        for j in range(0, rows):
            for i in range(0, columns):
                inverted_pil_images.append(pil_images[(i * rows) + j])

        grid = self._pil_grid(inverted_pil_images, columns)
        local_full_output_path = os.path.join(self._gaco.output_path,
                                              "{title}.jpg".format(title=title)
                                              if self._gaco.output_filename is None else self._gaco.output_filename)
        grid.save(local_full_output_path)
        print("==>  Image location: {0}".format(local_full_output_path))
        inverted_pil_images = None
        pil_images = None


if __name__ == '__main__':
    chrome_option = ChromeOptions()
    chrome_option.add_argument("--headless")
    # GoogleArtsCrawlerOption() \
    #     .set_url("https://artsandculture.google.com/asset/madame-moitessier/hQFUe-elM1npbw") \
    #     .set_chrome_options(chrome_option) \
    #     .set_need_download_webdrive(True) \
    #     .set_partial_tmp_path("custom_partial_dir") \
    #     .set_output_path("custom_output") \
    #     .set_output_filename("custom.jpg") \
    #     .prepare_options()
    GoogleArtsCrawlerProcess(gaco=GoogleArtsCrawlerOption()
                             .set_url("https://artsandculture.google.com/asset/madame-moitessier/hQFUe-elM1npbw")
                             .set_chrome_options(chrome_option)
                             .set_need_download_webdrive(True)
                             .set_webdriver_execute_path("webdriver/chromedriver")
                             .set_partial_tmp_path("custom_partial_dir")
                             .set_output_path("custom_output_dir")
                             .set_output_filename("custom.jpg")
                             .set_need_clear_cache(True)
                             .set_debug(True)
                             .prepare_options()).process()
