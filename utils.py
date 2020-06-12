#!/usr/bin/python3
import os
import re
import time
import stat
import subprocess
import platform
import requests
from lxml import html
from zipfile import ZipFile 
from urllib.parse import urlparse, urlunparse


class Release:
    AUTO_DETECT = 0
    STABLE = 1
    BETA = 2



def has_chromedriver() -> bool:
    '''check if chromedriver is present in current directory'''
    executable = 'chromedriver.exe' if platform.system() == 'Windows' else 'chromedriver'
    return os.path.exists(executable)
    

def download_chromedriver(release=Release.AUTO_DETECT) -> None:
    '''Download released chromedriver'''
    url = 'https://chromedriver.chromium.org/'
    if release == Release.AUTO_DETECT: url = url + 'downloads/'
    print(url)

    # get link to latest stable release
    print('Checking available versions.\n')
    page = requests.get(url)
    tree = html.fromstring(page.content)

    # select html element based on release
    if release == Release.AUTO_DETECT:
        installed_version = check_system_chrome_version()
        search_str = '.'.join(installed_version.split('.')[:-1])
        version = re.search(rf'{search_str}.\d+', page.text).group()

    elif release == Release.STABLE:
        element = tree.xpath('//*[@id="sites-canvas-main-content"]/table/tbody/tr/td/div/div[4]/ul/li[1]/a')[0]
        version = element.text.split()[-1]
    
    elif release == Release.BETA:
        element = tree.xpath('//*[@id="sites-canvas-main-content"]/table/tbody/tr/td/div/div[4]/ul/li[2]/a')[0]
        version = element.text.split()[-1]
    
    else:
        raise ValueError('ValueError invalid release option')

    
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


def check_system_chrome_version() -> str:
    sys_platform = platform.system()

    # Windows
    if sys_platform == 'Windows':
        cmd = 'dir /B/AD "C:\Program Files (x86)\Google\Chrome\Application\"|findstr /R /C:"^[0-9].*\..*[0-9]$"'
        version = subprocess.check_output(cmd, shell=True).decode().strip()
    # Linux/Mac
    else:
        cmd = 'google-chrome --version'
        version = os.popen(cmd).read().strip().split()[-1]

    return version


if __name__ == '__main__':
    print('Installed Chrome version:', check_system_chrome_version())
    download_chromedriver()
    