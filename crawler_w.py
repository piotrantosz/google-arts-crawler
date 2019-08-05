import time
import base64
import re
import collections
import numpy as np
import os
import shutil
import click
import pyperclip

from selenium import webdriver
from PIL import Image
from slugify import slugify

from selenium.webdriver.chrome.options import Options


options = webdriver.ChromeOptions()
options.binary_location = ""
driver = webdriver.Chrome(options = options, executable_path="chromedriver.exe")
driver.get('https://github.com/Boquete/google-arts-crawler')
print("Chrome Browser Invoked")
driver.quit()


DEFAULT_SIZE = 12000
DEFAULT_HOST = 'artsandculture.google.com'


@click.command()
@click.option(
    "--url",
    help="Image URL e.g. https://artsandculture.google.com/asset/madame-moitessier/hQFUe-elM1npbw"
)
@click.option(
    "--size",
    default=DEFAULT_SIZE,
    help="Max image size (default is 12000). Ignored if not using the --url option."
)
@click.option(
    "--raise-errors",
    is_flag=True,
    help="Raise errors instead of just printing them. Useful for debugging."
)
def main(url, size, raise_errors):
    try:
        cleanup()
        url = pyperclip.paste()
        if not DEFAULT_HOST in url:
            url, size = get_user_input()
        print("> Opening website")
        generate_image(url, size, raise_errors)
        cleanup()
    except Exception as e:
        print("FAILED")
        if raise_errors:
            raise e
        print(e)


def get_user_input():
    print("=====================================")
    print("=== Google Arts & Culture crawler ===")
    print("=====================================")
    print("Provide image URL")
    print("sample url: https://artsandculture.google.com/asset/madame-moitessier/hQFUe-elM1npbw")
    url = input('> URL: ')
    print("=====================================")
    print("Provide image maximum SIZE")
    print("sample size: 12000 (recommended)")
    size = input('> SIZE: ')
    if size:
        size = int(size)
    else:
        size = DEFAULT_SIZE
    print("=====================================")
    return url, size

def generate_image(url, size, raise_errors, delay=5):
    mobile_emulation = {
        "deviceMetrics": {"width": size, "height": size, "pixelRatio": 1.0},
        "userAgent": "Mozilla/5.0 (Linux; Android 4.2.1; en-us; Nexus 5 Build/JOP40D) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/18.0.1025.166 Mobile Safari/535.19"}
    options.add_experimental_option("mobileEmulation", mobile_emulation)
    options.add_argument('--headless')
    #chrome_options.add_argument('--disable-gpu')
    browser = webdriver.Chrome(options=options)
    browser.set_window_position(-5000, 0)
    browser.get(url)
    time.sleep(delay)
    blobs = browser.find_elements_by_tag_name('img')
    print("> Downloading partial images..")
    os.mkdir('blobs')

    title = slugify(browser.title)
    columns = []
    rows = []
    pil_images = []
    i = 0

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
            image = (get_file_content_chrome(browser, blob.get_attribute('src')))
            filename = 'blobs/{0}.jpg'.format(i)

            with open(filename, 'wb') as f:
                f.write(image)

            # Create PIL objects list
            try:
                pil_images.append(Image.open('blobs/{0}.jpg'.format(i)))
            except Exception as e:
                print("Exception raised")
                cleanup()
                if raise_errors:
                    raise e
                print(str(e))
                print('Trying again...')
                generate_image(url, size, raise_errors, delay+10)

        i += 1

    print("> Downloaded {0} partial images".format(len(blobs)))
    columns = (len(collections.Counter(columns).keys()))
    rows = (len(collections.Counter(rows).keys()))

    inverted_pil_images = []

    # by default images are crawled in vertical direction
    # we re-arrange list to create horizontally sorted list
    for j in range(0, rows):
        for i in range(0, columns):
            inverted_pil_images.append(pil_images[(i * rows) + j])

    print("> Saving partial images as final image")
    grid = pil_grid(inverted_pil_images, columns)
    grid.save('output/' + title + '.jpg')
    print("> SUCCESS! Image location: output/{0}.jpg".format(title))
    browser.close()

def get_file_content_chrome(driver, uri):
    """
    Saves blob to base64.
    """
    result = driver.execute_async_script("""
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


def pil_grid(images, max_horiz=np.iinfo(int).max):
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


def cleanup():
    try:
        shutil.rmtree('blobs/')
    except Exception:
        pass
    if not os.path.exists('output'):
        os.makedirs('output')

if __name__ == '__main__':
    main()

