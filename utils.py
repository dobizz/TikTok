#!/usr/bin/python3
import os
import time
import stat
import platform
import requests
from lxml import html
from zipfile import ZipFile 
from urllib.parse import urlparse, urlunparse


class Release:
    STABLE = 0
    BETA = 1


def has_chromedriver() -> bool:
    '''check if chromedriver is present in current directory'''
    executable = 'chromedriver.exe' if platform.system() == 'Windows' else 'chromedriver'
    return os.path.exists(executable)
    

def download_chromedriver(release=Release.STABLE) -> None:
    '''Download released chromedriver'''
    url = 'https://chromedriver.chromium.org/'

    # get link to latest stable release
    print('Checking available versions.\n')
    page = requests.get(url)
    tree = html.fromstring(page.content)

    # select html element based on release
    if release == Release.STABLE:
        element = tree.xpath('//*[@id="sites-canvas-main-content"]/table/tbody/tr/td/div/div[4]/ul/li[1]/a')[0]
    
    elif release == Release.BETA:
        element = tree.xpath('//*[@id="sites-canvas-main-content"]/table/tbody/tr/td/div/div[4]/ul/li[2]/a')[0]
    
    else:
        raise ValueError('ValueError invalid release option')

    version = element.text.split()[-1]
    print(f'Version: {version}\n')

    sys_platform = platform.system()
    
    # Linux
    if sys_platform == 'Linux':
        filename = 'chromedriver_linux64.zip'
    # Windows
    elif sys_platform == 'Windows':
        filename = 'chromedriver_win32.zip'
    # Mac
    else:
        filename = 'chromedriver_mac64.zip'

    # build uri
    uri = urlparse(f'https://chromedriver.storage.googleapis.com/{version}/')
    uri = uri._replace(path=uri.path+filename)

    # build url from uri
    url = urlunparse(uri)

    # rename old files
    executable = 'chromedriver.exe' if sys_platform == 'Windows' else 'chromedriver'
    if has_chromedriver():
        src = executable
        dst = f'backup_{int(time.time())}_{executable}'
        os.rename(src, dst)

    # download zip file
    print(f'Downloading: {url}\n')
    reply = requests.get(url)
    open(filename, 'wb').write(reply.content)
    print('Download complete.\n')

    # unzip downloaded file
    with ZipFile(filename, 'r') as zip:
        print(f'Extracting: {filename}\n')
        zip.printdir()
        zip.extractall()

    # set file permissions for Linux/Mac
    if sys_platform != 'Windows':
        # chmod 774 chromedriver
        os.chmod(executable, stat.S_IRWXU | stat.S_IRWXG | stat.S_IROTH)

    # delete zip file
    os.remove(filename)

    print('\nDone!\n')


if __name__ == '__main__':
    download_chromedriver()