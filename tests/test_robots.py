import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from robots import getAllowedAgents

def test_uas():
    # valid as of 2020/05/25
    uas = getAllowedAgents()
    assert set(uas) == {'Googlebot', 'Applebot', 'Bingbot', 'DuckDuckBot', 'Naverbot', 'Twitterbot', 'Yandex'}

if __name__ == '__main__':
    test_uas()