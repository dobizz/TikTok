import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from api import TikTok

def test_signURL():
    # for Windows
    if os.name == 'nt':
        print('Testing Signatures')
        tt = TikTok()
        url = 'https://www.tiktok.com/'
        signature1 = tt._signURL(url)
        signature2 = tt._signURL(url)

        assert signature1 is not None, 'Signature 1 is Empty'
        assert signature2 is not None, 'Signature 2 is Empty'
        assert signature1 != signature2, 'Duplicate signature'

    # for Linux
    elif os.name == 'posix':
        pass

    else:
        print(f'{os.name} not supported')

if __name__ == '__main__':
    test_signURL()