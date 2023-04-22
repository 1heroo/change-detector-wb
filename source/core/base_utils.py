import json

import aiohttp


class BaseUtils:

    @staticmethod
    async def make_get_request(url, headers, no_json=False):
        timeout_seconds = 500
        session_timeout = aiohttp.ClientTimeout(total=None, sock_connect=timeout_seconds, sock_read=timeout_seconds)
        async with aiohttp.ClientSession(trust_env=True, headers=headers, timeout=session_timeout) as session:
            async with session.get(url=url) as response:
                if response.status == 200:
                    return True if no_json else json.loads(await response.text())

    @staticmethod
    async def make_post_request(url, headers, payload, no_json=False):
        timeout_seconds = 500
        session_timeout = aiohttp.ClientTimeout(total=None, sock_connect=timeout_seconds, sock_read=timeout_seconds)
        async with aiohttp.ClientSession(trust_env=True, headers=headers, timeout=session_timeout) as session:
            async with session.post(url=url, json=payload) as response:

                if response.status == 200:
                    return True if no_json else json.loads(await response.text())

    @staticmethod
    def make_head(article: int):
        head = 'https://basket-{i}.wb.ru'

        if article < 14400000:
            number = '01'
        elif article < 28800000:
            number = '02'
        elif article < 43500000:
            number = '03'
        elif article < 72000000:
            number = '04'
        elif article < 100800000:
            number = '05'
        elif article < 106300000:
            number = '06'
        elif article < 111600000:
            number = '07'
        elif article < 117000000:
            number = '08'
        elif article < 131400000:
            number = '09'
        else:
            number = '10'
        return head.format(i=number)

    @staticmethod
    def make_tail(article: str, item: str):
        length = len(str(article))
        if length <= 3:
            return f'/vol{0}/part{0}/{article}/info/' + item
        elif length == 4:
            return f'/vol{0}/part{article[0]}/{article}/info/' + item
        elif length == 5:
            return f'/vol{0}/part{article[:2]}/{article}/info/' + item
        elif length == 6:
            return f'/vol{article[0]}/part{article[:3]}/{article}/info/' + item
        elif length == 7:
            return f'/vol{article[:2]}/part{article[:4]}/{article}/info/' + item
        elif length == 8:
            return f'/vol{article[:3]}/part{article[:5]}/{article}/info/' + item
        else:
            return f'/vol{article[:4]}/part{article[:6]}/{article}/info/' + item