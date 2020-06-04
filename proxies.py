#!/usr/bin/python3'
import json
import requests
import random
from lxml import html
from selenium import webdriver


def fetch_proxies() -> list:
    '''fetch list of proxies from url'''
    url = 'https://www.sslproxies.org/'

    page = requests.get(url)
    tree = html.fromstring(page.content)
    elements = tree.xpath('//*[@id="proxylisttable"]/tbody')[0]

    proxies = []
    keys = ['ip', 'port', 'code', 'country', 'anonymity', 'google', 'https', 'last_checked']

    for row in elements.getchildren():
        values = [col.text for col in row.getchildren()]
        proxies.append(dict(zip(keys, values)))

    return proxies


def get_my_ip() -> str:
    url = 'https://api.ipify.org'
    reply = requests.get(url)
    assert reply.status_code == 200

    return reply.text


if __name__ == '__main__':

    proxy = iter_random_proxy()

    # generate 10 random proxies
    for x in range(10):
        print(next(proxy))

    print(get_my_ip())