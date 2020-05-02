#!/usr/bin/python3
''' TikTok media crawler '''
import re
import os
import sys
import random
import hashlib
import asyncio
from datetime import datetime
from typing import Generator, List  # pep-0484
import requests
from aiohttp import ClientSession
from bs4 import BeautifulSoup
from lxml import html


# Global variables
LOCK = asyncio.Lock()   # for shared resources
MAX_WORKERS = 4         # for use in producer-consumer asyncio loop
MIN_DELAY = 1           # seconds
MAX_DELAY = 5           # seconds

# get user agent from your web browser
USER_AGENTS = {
    'Safari - Mac' : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Safari/605.1.15',
    'Edge - Windows' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.129 Safari/537.36 Edg/81.0.100.0',
    'Firefox - Windows' : 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:70.0) Gecko/20100101 Firefox/70.0',
    'IE11' : 'Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko',
    'Chrome - Windows' : 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.129 Safari/537.36',
}

# proxy list
PROXIES = {

}

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


async def log_completed(url: str, file_name: str = 'videolist_completed.txt') -> None:
    ''' records to videolist_completed '''
    with open(file_name, 'a+') as file:
        file.write(f"{url}\n")


async def download_video(file_name: str, url: str, session) -> bool:
    ''' download video from url and write to file '''
    try:
        # get bytes from url
        reply = await session.request(method='GET', url=url)

        status_code = reply.status
        # check for status code
        if status_code != 200:
            raise Exception(f'Error {status_code}')

        # save bytes to file
        with open(file_name, 'wb') as file:
            async for data_chunk in reply.content.iter_chunked(1024):
                if data_chunk:
                    file.write(data_chunk)
        status = True

    except Exception as e:
        print(f'Exception Found: {e}')
        status = False

    return status


def purge_duplicate_links(file_name: str = 'videolist.txt') -> tuple:
    ''' remove duplicate links from video list file '''
    before = after = 0
    try:
        print('Starting cleanup...')
        with open('videolist.txt', 'r+') as file:
            links = file.readlines()
            before = len(links)
            print(f'\nBefore cleaning: {before} links found')
            links = sorted(set((link.strip() for link in links)))
            after = len(links)
            print(f'\nAfter cleaning: {after} links found')
            file.seek(0)
            file.write('\n'.join(links))
            print('\nWriting changes...')
            file.truncate()
        print('\nCleanup completed!')

    except:
        print('\nCleanup aborted!')

    return (before, after)


async def fetch_html(session, url):
    ''' async request and return html data '''
    async with session.request(method='GET', url=url) as reply:
        # check for status code
        status_code = reply.status
        if status_code != 200:
            raise Exception(f'Error {status_code}')
        return await reply.text()


async def download_worker(name, queue, session):
    ''' async function for handling worker queue'''
    while True:
        # get url from queue
        video_url = await queue.get()

        if video_url is None:
            break

        await asyncio.sleep(random.randint(MIN_DELAY, MAX_DELAY))
        print(f'[Worker-{name}-Starting]')

        try:
            t1 = datetime.now()

            html = await fetch_html(session, video_url)

            soup = BeautifulSoup(html, 'html5lib')

            # unique id for each video
            username, video_id = re.findall(r'com/@(.+)/video/(\d+)', video_url)[0]
            video_id = video_url.split('/')[-1]

            # creates username folder if not present
            if not os.path.exists(f'./videos/{username}'):
                print(f'Creating directory ./videos/{username}')
                os.makedirs(f'./videos/{username}')

            # find all videos inside link and save to file
            for index, video in enumerate(soup.find_all('video')):
                resource_link = video['src']
                link_hash = hashlib.md5(resource_link.encode()).hexdigest()
                print(f'[Worker-{name}-Downloading-{index}] {link_hash}')
                if await download_video(f'./videos/{username}/{video_id}_{index}.mp4', resource_link, session):
                    print(f'[Worker-{name}-File-{index}] Download Complete.')
                    await log_completed(video_url)
                else:
                    print(f'[Worker-{name}-File-{index}] Download Failure!')
                    raise Exception('Download Error!')

        except Exception as e:
            t2 = datetime.now()
            print(f'[Worker-{name}-Exception] {t2 -t1} | {e} | {video_url}')

        else:
            t2 = datetime.now()
            print(f'[Worker-{name}-Completed] {t2 -t1} | {video_url}')

        queue.task_done()
        print(f'[*] Tasks left in Queue = {queue.qsize()}')


async def main() -> None:
    ''' main program sequence '''
    # creates videos folder if not present
    if not os.path.exists('videos'):
        os.makedirs('videos')

    # check for duplicates and run cleanup
    purge_duplicate_links()

    completed_videos = get_completed()

    # create a queue that will store urls for download
    queue = asyncio.Queue()

    print('\nGenerating work queue...\n')

    # get video urls from file
    for video_url in video_list_generator():
        print(f'Now opening : {video_url}')

        # skip videos already downloaded
        if video_url in completed_videos:
            print('[*] Skipping link, already completed.')
            continue

        # add url to queue
        queue.put_nowait(video_url)

    print('\nAll tasks pushed to queue for processing.\n')

    UA = random.choice(list(USER_AGENTS))
    print(f'Using User-Agent: {UA}\n')
    async with ClientSession(headers={'User-Agent': USER_AGENTS[UA]}) as session:
        # create workers to download the urls concurrently
        tasks = []
        for worker in range(MAX_WORKERS):
            task = asyncio.create_task(download_worker(worker, queue, session))
            tasks.append(task)

        # wait until the queue is consumed
        print('Waiting for tasks in queue to be processed...\n')
        await queue.join()

        # dismiss workers once queue is finished
        print('Finishing tasks...\n')
        for task in tasks:
            task.cancel()

        # wait until all workers are dismissed
        await asyncio.gather(*tasks, return_exceptions=True)

    print('\nAll tasks finished.\n')


if __name__ == '__main__':
    assert sys.version_info >= (3, 6), 'Python 3.6+ required.'

    t1 = datetime.now()
    asyncio.run(main())
    t2 = datetime.now()
    print(f'\nFinished in {t2 - t1} seconds.')
