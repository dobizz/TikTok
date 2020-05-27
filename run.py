#!/usr/bin/python3
import os
import sys
import enum
import random
import asyncio
import aiohttp
import aiofiles
from api import TikTok
from robots import getAllowedAgents


DOWNLOADS_BASE_DIR = './videos'
MAX_CONCURRENT = 4


class Scrape(enum.Enum):
    TRENDING = 0
    USER = 1
    MUSIC = 2
    HASHTAG = 3
    OTHERS = 4
    NONE = -1


async def download_worker(name, queue, session) -> None:
    ''' async function for handling worker queue'''
    while True:
        # get job from queue
        job = await queue.get()

        # unpack job
        username, video_id, video_url = job

        file_name = f'{DOWNLOADS_BASE_DIR}/{username}/{video_id}.mp4'
        print(f'[ w-{name} | q-{queue.qsize():03d} ] Downloading -> {file_name}')

        # download video
        if not await download_video(session, file_name, *job):
            print(f'[ w-{name} | q-{queue.qsize():03d} ] Download FAILED for {file_name}')
        
        # mark job as completed
        queue.task_done()


async def download_video(session, file_name, username, video_id, video_url) -> bool:
    ''' download video from url and write to file '''
    try:
        # get bytes from url
        response = await session.request(method='GET', url=video_url)

        # check for status code
        status_code = response.status
        if status_code != 200:
            raise Exception(f'Error {status_code}')

        # save bytes to file
        async with aiofiles.open(file_name, 'wb') as file:
            async for data_chunk in response.content.iter_chunked(1024):
                if data_chunk:
                    await file.write(data_chunk)
        status = True

    except Exception as e:
        print(f'Exception: {e}')
        status = False

    return status


async def scrape(mode, username: str=None, count: int=0, likes: int=0, views: int=0, shares: int=0, comments: int=0):
    ''' general scrape method '''
    tt = TikTok()

    if mode == Scrape.TRENDING:
        # change videos to number of videos you want to return
        username = 'trending'
        if count < 0:
            count = 30
        try:
            results = tt.getTrending(count)
        except Exception as e:
            print('Exception:', e)
            return None

    elif mode == Scrape.USER:
        try:
            details = tt.getUserDetails(username)
        except Exception as e:
            print('Exception:', e)
            return None

        userInfo = details['userInfo']
        _id = userInfo['user']['id']
        secUid = userInfo['user']['secUid']
        stats = details['userInfo']['stats']
        videos = stats['videoCount']

        if count < 0:
            count = videos

        results = tt.getUserTikToks(_id, count)

    elif mode == Scrape.MUSIC:
        pass

    elif mode == Scrape.HASHTAG:
        pass

    #####################
    # Results Filtering #
    #####################
    
    # filter according to likes
    if likes:
        results = list(filter(lambda x: x['stats']['diggCount'] >= likes, results))

    # filter according to views
    if views:
        results = list(filter(lambda x: x['stats']['playCount'] >= views, results))

    # filter according to shares
    if shares:
        results = list(filter(lambda x: x['stats']['shareCount'] >= shares, results))

    # filter according to comments
    if comments:
        results = list(filter(lambda x: x['stats']['commentCount'] >= comments, results))

    # creates username folder if not present
    path = f'{DOWNLOADS_BASE_DIR}/{username}'
    if not os.path.exists(path):
        print(f'Creating directory {path}')
        os.makedirs(path)

    # explicitly delete TikTok object as we don't need to make any more API calls
    del tt

    # process results in a producer-consumer async loop
    try:
        queue = asyncio.Queue(maxsize=1000)

        # enqueue items
        for item in results:
            video_id = item['id']
            download_url = item['video']['downloadAddr']
            print('Adding to queue:', video_id)
            await queue.put((username, video_id, download_url))

        headers = {
            'User-Agent': random.choice(getAllowedAgents()),
            'method': 'GET',
            'accept-encoding': 'gzip, deflate, br',
            'referrer': 'https://www.tiktok.com/trending',
            'upgrade-insecure-requests': '1',
        }

        # create http session
        async with aiohttp.ClientSession(headers=headers) as session:
            tasks = []
            # spawn worker tasks
            for worker in range(MAX_CONCURRENT):
                task = asyncio.create_task(download_worker(worker, queue, session))
                tasks.append(task)

            # wait until the queue is consumed
            print(f'\nWaiting for tasks in queue[{queue.qsize()}] to be processed...\n')
            await queue.join()

        # dismiss workers once queue is finished
        print('\nFinishing tasks...\n')
        for task in tasks:
            task.cancel()

        # wait until all workers are dismissed
        await asyncio.gather(*tasks, return_exceptions=True)

    except Exception as e:
        print('Exception', e)  


if __name__ == '__main__':
    assert sys.version_info >= (3, 6), 'Python 3.6+ required.'

    # default arguments
    mode = Scrape.TRENDING
    username = None
    count = 10
    likes = 0
    views = 0
    shares = 0
    comments = 0

    print('-=[ TikTok Public Video Scraper ]=-\n\n' +
            '0 - Scrape by Trending Videos\n' +
            '1 - Scrape by Username\n' +
            '2 - Scrape by Music [WIP]\n' +
            '3 - Scrape by Hashtag [WIP]\n')

    mode = Scrape(int(input('Enter choice [0-3]: ')))

    if mode == Scrape.USER:
        username = input('Enter username to scrape: ')

    count = int(input('\nHow many vidoes would you like to scrape [-1 for all possible]: '))

    # run scrape routine
    loop = asyncio.get_event_loop()
    loop.run_until_complete(scrape(mode, username=username, count=count, likes=likes, views=views, shares=shares, comments=comments))