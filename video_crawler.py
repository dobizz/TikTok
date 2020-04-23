#!/usr/bin/python3
''' TikTok media crawler '''
import re
import os
import time
import random
import hashlib
import requests
import threading
from bs4 import BeautifulSoup
from datetime import datetime
from lxml import html
from typing import Generator, List  # pep-0484

# threading variables
PRINT_LOCK = threading.Lock()
THREAD_COUNT = 4    # for use in producer-consumer threading model
MIN_DELAY = 1       # seconds
MAX_DELAY = 5       # seconds

# get user agent from your web browser
CHROME_UA = "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36"

# proxy list
PROXIES = {

}


def t_print(message: str) -> None:
    ''' message printer to avoid race conditions'''
    with PRINT_LOCK:
        print(message)

def threader(thread_id: int, video_url: str) -> None:
    ''' thread function for processing video urls '''
    time.sleep(random.randint(MIN_DELAY, MAX_DELAY))
    t_print(f'[Thread-{thread_id}-Starting]')

    try:
        # retrieve html data
        page = requests.get(video_url, headers={'User-Agent': CHROME_UA})
        soup = BeautifulSoup(page.content, 'html5lib')

        # unique id for each video
        username, video_id = re.findall(r'com/@(.+)/video/(\d+)', video_url)[0]
        video_id = video_url.split('/')[-1]

        # creates username folder if not present
        if not os.path.exists(f'./videos/{username}'):
            os.makedirs(f'./videos/{username}')

        # find all videos inside link and save to file
        for index, video in enumerate(soup.find_all('video')):
            resource_link = video['src']
            link_hash = hashlib.md5(resource_link.encode()).hexdigest()
            t_print(f'[Thread-{thread_id}-Downloading-{index}] {link_hash}')
            if download_video(f'./videos/{username}/{video_id}_{index}.mp4', resource_link):
                t_print(f'[{index}] Download completed')
                log_completed(video_url)
            else:
                t_print(f'[{index}] Failed!')

    except Exception as e:
        t_print(f'[Thread-{thread_id}-Exception] {e}')

    t_print(f'[Thread-{thread_id}-Finishing]')


def get_proxies(anonymity: str = 'elite proxy') -> List[str]:
    ''' get list of free proxies '''
    url = 'https://www.sslproxies.org/'
    response = requests.get(url)
    parser = html.fromstring(response.text)
    proxies = set()
    for i in parser.xpath('//tbody/tr')[:10]:
        if i.xpath('.//td[7][contains(text(),"yes")]')\
            and i.xpath(f'.//td[5][contains(text(),"{anonymity}")]'):
            proxy = ":".join([i.xpath('.//td[1]/text()')[0], i.xpath('.//td[2]/text()')[0]])
            proxies.add(proxy)
    return proxies


def video_list_generator(file_name: str = 'videolist.txt') -> Generator[str, None, None]:
    ''' yields generator object of video links '''
    # open video list and yield each link
    with open(file_name, 'r') as file:
        videos = file.read().split('\n')

    for video in videos:
        yield video


def get_completed(file_name: str = 'videolist_completed.txt') -> List[str]:
    ''' returns list of completed video links '''
    # open video list and yield each link
    try:
        with open(file_name, 'r') as file:
            videos = file.read().split('\n')
    except:
        videos = []
    return videos


def log_completed(url: str, file_name: str = 'videolist_completed.txt') -> None:
    ''' records to videolist_completed '''
    with open(file_name, 'a+') as file:
        file.write(f"{url}\n")


def download_video(file_name: str, url: str) -> bool:
    ''' download video from url and write to file '''
    try:
        # get bytes from url
        reply = requests.get(url, stream=True)

        # save bytes to file
        with open(file_name, 'wb') as file:
            for data_chunk in reply.iter_content(chunk_size=1024 * 1024):
                if data_chunk:
                    file.write(data_chunk)
        status = True

    except Exception as e:
        status = False

    return status

def purge_duplicate_links(file_name: str = 'videolist.txt') -> tuple:
    ''' remove duplicate links from video list file '''
    before = after = 0
    try:
        print('Starting cleanup')
        with open('videolist.txt', 'r+') as file:
            links = file.readlines()
            before = len(links)
            print(f'Before cleaning: {before} links')
            links = sorted(set((link.strip() for link in links)))
            after = len(links)
            print(f'After cleaning: {after} links')
            file.seek(0)
            file.write('\n'.join(links))
            print('Writing changes')
            file.truncate()
        print('Cleanup completed')

    except:
        print('Cleanup aborted')
    return (before, after)

def main() -> None:
    ''' main program sequence '''
    # creates videos folder if not present
    if not os.path.exists('videos'):
        os.makedirs('videos')

    print(purge_duplicate_links())

    completed_videos = get_completed()

    index = 1
    threads = list()
    for video_url in video_list_generator():
        t_print(f'\nNow opening: {video_url}')

        # skip videos already downloaded
        if video_url in completed_videos:
            t_print('Skipping link, already completed.')
            continue

        # initialize threads
        thread = threading.Thread(target=threader, args=(index, video_url,))
        threads.append(thread)
        thread.start()
        index += 1

    t_print('\nAll threads started and waiting to complete.\n')
    for index, thread in enumerate(threads):
        thread.join()
    print('\nAll threads finished.\n')


if __name__ == '__main__':
    t1 = datetime.now()
    main()
    t2 = datetime.now()
    print(f'\nFinished in {t2 - t1} seconds.')