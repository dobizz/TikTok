#!/usr/bin/env python3
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


def has_chromedriver() -> bool:
    '''check if chromedriver is present in current directory'''
    executable = 'chromedriver.exe' if platform.system() == 'Windows' else 'chromedriver'
    return os.path.exists(executable)
    

def download_chromedriver() -> None:
    '''Download released chromedriver'''
    # check current chrome version
    version = check_system_chrome_version()
    print(f'Installed Chrome version: {version}\n')
    # get available release of version
    release = get_latest_release(version)
    print(f'Available Chrome release: {release}\n')

    # get system platform in order to determine filename to download
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
    uri = urlparse(f'https://chromedriver.storage.googleapis.com/{release}/')
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
    assert reply.status_code == 200
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
        # Try searching for 32-bit installation
        try:
            cmd = 'dir /B/AD "C:\Program Files (x86)\Google\Chrome\Application\"|findstr /R /C:"^[0-9].*\..*[0-9]$"'
            version = subprocess.check_output(cmd, shell=True).decode().strip()
        # Try searching for 64-bit installation
        except:
            cmd = 'dir /B/AD "C:\Program Files\Google\Chrome\Application\"|findstr /R /C:"^[0-9].*\..*[0-9]$"'
            version = subprocess.check_output(cmd, shell=True).decode().strip()

        # get the latest version from results
        version = version.split()[-1]

    # Linux/Mac
    else:
        cmd = 'google-chrome --version'
        result = os.popen(cmd).read()

        # if no results, try chromium browser
        if not result:
            cmd = 'chromium-browser --version'
            result = os.popen(cmd).read()

        version = result.strip().split()[-1]

    # return version string to caller
    return version


def get_latest_release(version:str) -> str:
    main_version = version.split('.')[0]
    url = f'https://chromedriver.storage.googleapis.com/LATEST_RELEASE_{main_version}'
    reply = requests.get(url)
    assert reply.status_code == 200
    latest_relase = reply.text
    return latest_relase 


if __name__ == '__main__':
    download_chromedriver()
