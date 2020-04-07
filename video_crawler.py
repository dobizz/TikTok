#!/usr/bin/python3
''' TikTok media crawler '''
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime

def video_list_generator(file_name: str='videolist.txt'):
    ''' yields generator object of video links '''
    # open video list and yield each link
    with open(file_name, 'r') as file:
        videos = file.read().split('\n')

    for video in videos:
        yield video

def download_video(file_name: str, url: str):
    # get bytes from url
    r = requests.get(url, stream=True)
    
    # save bytes to file
    with open(f'./videos/{file_name}', 'wb') as f:
        for data_chunk in r.iter_content(chunk_size=1024*1024): 
            if data_chunk: 
                f.write(data_chunk) 

def main():
    ''' main program sequence '''
    # creates videos folder if not present
    if not os.path.exists('videos'):
        os.makedirs('videos')

    for video_url in video_list_generator():
        print(f'Now opening: {video_url}')
        
        # get user agent from your web browser
        user_agent = "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36"
        page = requests.get(video_url, headers={'User-Agent': user_agent})
        soup = BeautifulSoup(page.content, 'html5lib')
        
        # unique id for each video
        video_id = video_url.split('/')[-1]
        
        # find all videos inside link and save to file
        for index, video in enumerate(soup.find_all('video')):
            resource_link = video['src']
            print(f'\t[+] Now downloading: {resource_link}')
            download_video(f'tiktok_video_{video_id}_{index}.mp4', resource_link) 

if __name__ == '__main__':
    t1 = datetime.now()
    main()
    t2 = datetime.now()
    print(f'\nFinished in {t2 -t1} seconds.')
