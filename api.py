#!/usr/bin/python3
import os
import sys
import json
import random
import asyncio
import aiohttp
import aiofiles
import async_timeout
from selenium import webdriver
from robots import getAllowedAgents


class TikTok:
    ''' TikTok object with Selenium '''

    # Get Allow: / from robots.txt
    USER_AGENTS = getAllowedAgents()

    def __init__(self, path: str=None):
        # select random UserAgent from robots.txt
        self.UserAgent = random.choice(TikTok.USER_AGENTS)
        # self.UserAgent = 'Twitterbot'
        print(f'User-Agent: {self.UserAgent}')

        # set default webdriver path
        self.driver_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'chromedriver.exe') if path is None else path 

        # set chrome options
        self.chrome_options = webdriver.ChromeOptions()
        self.chrome_options.add_argument('--ignore-certificate-errors')
        self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('--disable-gpu')
        self.chrome_options.add_argument('--incognito')
        self.chrome_options.add_argument(f'user-agent={self.UserAgent}')

        # start webdriver
        self.driver = webdriver.Chrome(self.driver_path, options=self.chrome_options)

        # modify HTTP request headers
        self.driver.header_overrides = {
            'method': 'GET',
            'accept-encoding': 'gzip, deflate, br',
            'referrer': 'https://www.tiktok.com/trending',
            'upgrade-insecure-requests': '1',
        }

        # set tiktok default variables
        self.language = 'en'
        self.region = 'PH'
        self.type = 1
        self.secUid = 0
        self.verifyFp = None
        self.maxCount = 99
        self.minCursor = 0
        self.maxCursor = 0
        self.sourceType = 8 # 12 for trending


    def __del__(self):
        self.driver.quit()


    def _signURL(self, url):
        '''Sign URL using duD4 function defined in webpackJsonp'''
        sign_js_url = 'https://www.tiktok.com/trending'
        self.driver.get(sign_js_url)

        # save cookie information if not present
        if not self.verifyFp:
            self.verifyFp = self.driver.get_cookie('s_v_web_id')['value']

        # execute JS in browser sign url
        script = '''
            let t = {};
            webpackJsonp.filter(x => typeof x[1]['duD4'] === "function")[0][1].duD4(null, t);
            return t.sign({url: "''' + url +'''"});;'''    
        signature = self.driver.execute_script(script)

        return signature


    def getUserDetails(self, username):
        url = f'https://m.tiktok.com/api/user/detail/?uniqueId={username}&language={self.language}&verifyFp={self.verifyFp if self.verifyFp else ""}'

        signature = self._signURL(url)
        url = f'{url}&_signature={signature}'

        self.driver.get(url)

        text = self.driver.page_source
        details = json.loads(self.driver.find_element_by_tag_name('pre').text)
        secUid =  details['userInfo']['user']['secUid']
        self.secUid = secUid
        return details

    def getTrending(self, count: int=50):
        '''get list of trending tiktok videos'''
        self.sourceType = 12
        self.type = 5
        return self.__getTikToks(_id=1, item_count=count)


    def getUserTikToks(self, userid, count: int=0):
        '''get list of user tiktok videos'''
        self.sourceType = 8
        self.type = 1
        return self.__getTikToks(_id=userid, item_count=count)


    def __getTikToks(self, _id, item_count: int=0):
        '''general get tiktok method'''
        self.minCursor = 0
        self.maxCursor = 0

        tiktoks = []
        
        # query api in batches
        while len(tiktoks) < item_count:
            # limit maximum number of items per request
            count = item_count if item_count < self.maxCount else self.maxCount

            # prepare request url
            url = f'https://m.tiktok.com/api/item_list/?count={count}&id={_id}&type={self.type}&secUid={self.secUid}&maxCursor={self.maxCursor}&minCursor={self.minCursor}&sourceType={self.sourceType}&appId=1233&region={self.region}&language={self.language}&verifyFp={self.verifyFp if self.verifyFp else ""}'
            
            # get signature for request url
            signature = self._signURL(url)
            
            # affix signature to request url
            url = f'{url}&_signature={signature}'

            print(url) #debug
            # send request
            self.driver.get(url)

            # JSON reply sample
            # {
            #     "statusCode": 0,
            #     "items": [],
            #     "hasMore": true,
            #     "maxCursor": 1235,
            #     "minCursor": 1234
            # } 

            # parse response
            reply = json.loads(self.driver.find_element_by_tag_name('pre').text)
            items = reply['items']
            tiktoks.extend(items)

            # this is last batch, no more tiktoks to expect
            if not reply['hasMore']:
                break

            # adjust count to reflect items returned in this batch
            count = item_count - len(tiktoks)
            self.maxCursor = reply['maxCursor']
        return tiktoks


async def download_worker(name, queue):
    ''' async function for handling worker queue'''
    while True:
        # get url from queue
        job = await queue.get()

        username, video_id, video_url = job

        file_name = f'./videos/{username}/{video_id}.mp4'
        print(f'[ w-{name} | q-{queue.qsize():03d} ] Downloading -> {file_name}')

        headers = {
            'User-Agent': random.choice(getAllowedAgents()),
            'method': 'GET',
            'accept-encoding': 'gzip, deflate, br',
            'referrer': 'https://www.tiktok.com/trending',
            'upgrade-insecure-requests': '1',
        }

        # create separate http session and download video 
        async with aiohttp.ClientSession(headers=headers) as session:
            await download_video(session, file_name, *job)

        queue.task_done()
        # print(f'[*] Tasks left in Queue = {queue.qsize()}')


async def download_video(session, file_name, username, video_id, video_url) -> bool:
    ''' download video from url and write to file '''
    try:
        # get bytes from url
        reply = await session.request(method='GET', url=video_url)

        status_code = reply.status
        # check for status code
        if status_code != 200:
            raise Exception(f'Error {status_code}')

        # save bytes to file
        async with aiofiles.open(file_name, 'wb') as file:
            async for data_chunk in reply.content.iter_chunked(1024):
                if data_chunk:
                    await file.write(data_chunk)
            await file.flush()
        status = True

    except Exception as e:
        print(f'Exception Found: {e}')
        status = False

    return status


##########################
# Example Implementation #
##########################
async def scrapeUser():

    tt = TikTok()

    try:
        ###############################
        # change target username here #
        ###############################
        username = 'ENTER_USERNAME_HERE'
        ###############################
        details = tt.getUserDetails(username)
        userInfo = details['userInfo']
        _id = userInfo['user']['id']
        secUid = userInfo['user']['secUid']
        stats = details['userInfo']['stats']
        videos = stats['videoCount']
        print('Total TikToks:', videos)
        print('User Id:', _id)

        # change videos to number of videos you want to return
        reply = tt.getUserTikToks(_id, videos)

        # creates username folder if not present
        if not os.path.exists(f'./videos/{username}'):
            print(f'Creating directory ./videos/{username}')
            os.makedirs(f'./videos/{username}')

        # create a queue that will store urls for download
        queue = asyncio.Queue()

        for item in reply:
            video_id = item['id']
            download_url = item['video']['downloadAddr']
            print('Adding to queue:', video_id)
            # print(download_url,'\n')
            await queue.put((username, video_id, download_url))

        tasks = []
        for worker in range(4):
            task = asyncio.create_task(download_worker(worker, queue))
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

    finally:
        del tt

if __name__ == '__main__':
    assert sys.version_info >= (3, 6), 'Python 3.6+ required.'
    asyncio.run(scrapeUser())