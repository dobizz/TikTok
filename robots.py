#!/usr/bin/python3

''' Get allowed UA's from robots.txt '''

import requests
import re

def getAllowedAgents():
    regex = re.compile(r'(?:User-agent: (\w+)+\n)|(?:(Allow: /)\n)')

    reply = requests.get('https://www.tiktok.com/robots.txt')
    assert reply.status_code == 200

    results = regex.findall(reply.text)
    limit = results.index(('','Allow: /'))

    return [item[0] for index, item in enumerate(results) if index < limit]
