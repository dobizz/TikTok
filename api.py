#!/usr/bin/python3
import os
import sys
import json
import random
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
        self.chrome_options.add_argument('--ignore-certificate-errors-spki-list')
        self.chrome_options.add_argument("--ignore-ssl-errors")
        self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('--disable-gpu')
        self.chrome_options.add_argument('--incognito')
        self.chrome_options.add_argument('--log-level=3')
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

        # limit maximum number of items per request
        count = item_count if item_count < self.maxCount else self.maxCount
        
        # query api in batches
        while len(tiktoks) < item_count:
            

            # prepare request url
            url = f'https://m.tiktok.com/api/item_list/?count={count}&id={_id}&type={self.type}&secUid={self.secUid}&maxCursor={self.maxCursor}&minCursor={self.minCursor}&sourceType={self.sourceType}&appId=1233&region={self.region}&language={self.language}&verifyFp={self.verifyFp if self.verifyFp else ""}'
            
            # get signature for request url
            signature = self._signURL(url)
            
            # affix signature to request url
            url = f'{url}&_signature={signature}'

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
            try:
                reply = json.loads(self.driver.find_element_by_tag_name('pre').text)
                items = reply['items']
                tiktoks.extend(items)

                # this is last batch, no more tiktoks to expect
                if not reply['hasMore']:
                    break

                # adjust count to reflect items returned in this batch
                count = item_count - len(tiktoks)
                self.maxCursor = reply['maxCursor']

            except:
                raise Exception('No items returned, possibly bad User-Agent. Please try again.')

        return tiktoks


def main():
    tt = TikTok()


if __name__ == '__main__':
    assert sys.version_info >= (3, 6), 'Python 3.6+ required.'
    main()