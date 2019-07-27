# Google Arts & Culture crawler
Google Arts &amp; Culture high quality image downloader

Download images from Google Arts and Culture in high resolution

Using this script you can download any image from <https://artsandculture.google.com/> in high quality (even 12k!)

_Warning: it's simple and ugly code created at one night. It might be full of bugs._
_Feel free to do anything you want with this code_

_If you got any trouble, just send me an email boquete37@gmail.com_

## Installation

### Linux
* `git clone https://github.com/Boquete/google-arts-crawler.git`
* `cd google-arts-crawler/`
* `virtualenv venv`
* `source venv/bin/activate`
* `pip3 install -r requirements.txt`
* `python3 crawler.py`

### Windows
* Install Python <https://www.python.org/>
* Download Chromedriver <https://sites.google.com/a/chromium.org/chromedriver/downloads>
* Copy Chromedriver to PATH (see #Problems)
* Open command prompt (Administrator) and run the following commands:
	cd C:\your\path\to\google-arts-crawler\
	pip install -r requirements.txt
	python crawler.py

## Usage


If there is a string containing "artsandculture.google.com" in your clipboard the script will attempt to run it as the input url and use the default image size, otherwise you will be asked for:
* url - url of image, for example: <https://artsandculture.google.com/asset/madame-moitessier/hQFUe-elM1npbw>
* size (px) - maximum size. Downloaded image will be NOT exact size as *size*, but close enough.

In Windows, feel free to instead use the provided docrawl.bat file for ease of use (e.g. binding it to a keyboard/mouse key with your control software). It is programmed to assume Administrator privileges automatically and can be customized with image size presets.


## Output
After script ends, your image (.jpg)w ill be located at:

outputs/image_name.jpg

## Problems
1. chromedriver executable needs to be in PATH

You can download ChromeDriver here: <https://sites.google.com/a/chromium.org/chromedriver/downloads> .
Then you have multiple options:

* add it to your system path (usually C:\Users\USERNAME\AppData\Local\Programs\Python\PythonXX-XX\)
* put it in the same directory as your python script
* specify the location directly via executable_path
driver = webdriver.Chrome(executable_path='C:/path/to/chromedriver.exe')

( <https://stackoverflow.com/a/40556092/4807171> )
