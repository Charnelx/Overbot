import asyncio
import datetime
import logging
from lxml import html

from scraper_base import *
from session import GSession


class Scraper(BaseScraper):

    FORUM_URL = 'https://forum.overclockers.ua/viewforum.php'
    TOPIC_URL = 'https://forum.overclockers.ua/viewtopic.php'
    DOMAIN = 'https://forum.overclockers.ua'
    HEADERS = {
        'Host': 'forum.overclockers.ua',
        'User-Agent': 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
                      ' Chrome/69.0.3497.100 Safari/537.36 OPR/56.0.3051.52',
        'Referer': 'https://forum.overclockers.ua/',
    }

    FORUMS = {
        'buy': '26',
    }

    def __init__(self, coros_limit=100, r_timeout=5, pause=2, raise_exceptions=True):
        self.r_timeout = r_timeout
        self.coros_limit = coros_limit
        self.raise_exceptions = raise_exceptions
        self.logger = logging.getLogger('od_scraper')
        self.pause = pause

        self.id = 'overclocker_scraper'

    def _generate_page(self, start: int, end: int):
        for i in range(start - 1, end):
            yield i * 40

    def _generate_listing_urls(self, start: int, end: int, forum='buy'):
        urls = []
        forum = self.FORUMS.get(forum)
        for page_index in self._generate_page(start, end):
            req_params = {'f': forum, 'start': page_index}
            urls.append(
                (
                    self.FORUM_URL,
                    req_params
                )
            )
        return urls

    def get_content(self, start: int, end: int, *args, **kwargs):

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        urls = self._generate_listing_urls(start, end)
        results_raw = loop.run_until_complete(self._get_content(urls))

        topics_listing = []
        for page_index, page in enumerate(results_raw):
            if isinstance(page, Exception):
                self.logger.error(page)
            else:
                for data_raw in page.values():
                    data = self._process_listing(data_raw)
                    for list_index, item in enumerate(data):
                        item['page'] = page_index
                        item['item_index'] = list_index
                        topics_listing.append(item)

        topics_raw = loop.run_until_complete(self.get_topic_content(topics_listing))

        topics_mapping = {}
        for topic in topics_raw:
            topic['content'] = self.process_topic(topic.get('content'))
            topics_mapping[topic.get('id')] = topic

        loop.close()

        for item in topics_listing:
            topic = topics_mapping.get(str(item.get('id')))
            item['post'] = topic.get('content') if topic else ''

        return topics_listing

    async def _get_content(self, urls) -> list:
        session = GSession(headers=self.HEADERS)
        semaphore = asyncio.Semaphore(self.coros_limit)

        tasks, result = [], []

        for url, req_params in urls:
            tasks.append(self._get_data(url, req_params, session, semaphore))

        result = await asyncio.gather(*tasks, return_exceptions=self.raise_exceptions)

        await session.close()
        return result

    async def _get_data(self, url, req_params, session, semaphore):
        data = None
        response=None
        try:
            response = await session.get(url, params=req_params, semaphore=semaphore, timeout=self.r_timeout)
        except Exception as err:
            raise ResponseError(f' -> Request on {self.FORUM_URL} failed. Error: {err}', url='None')
        if response and response.text_content:
            data = {str(response.url): response.text_content}
        return data

    def _process_listing(self, data):
        results = []
        if data:
            root = html.fromstring(data)
            topics_elem = root.xpath('//div[@class="forumbg"]/div[@class="inner"]/ul[@class="topiclist topics"]/li')
            for topic in topics_elem:
                result = {
                    'id': None,
                    'url': None,
                    'title': '',
                    'location': '',
                    'author': '',
                    'author_profile_link': '',
                    'posts_count': 0,
                    'views_count': 0,
                    'last_post_ts': 0,
                }

                node_topic_url = topic.xpath('./dl/dt/div/a')[0]
                result['id'] = int(node_topic_url.get('href').split('&t=')[-1].split('&')[0])
                result['url'] = self.DOMAIN + node_topic_url.get('href').replace('.', '', 1).rsplit('&', 1)[0]
                result['title'] = node_topic_url.text.split(']', 1)[1].lstrip(' ')
                result['location'] = node_topic_url.text.split(']', 1)[0].replace('[', '')

                node_author = topic.xpath('./dl/dd[@class="author"]/a')[0]
                result['author_profile_link'] = self.DOMAIN + node_author.get('href').replace('.', '', 1).rsplit('&', 1)[0]
                result['author'] = node_author.text

                result['posts_count'] = int(topic.xpath('./dl/dd[@class="posts"]/text()')[0])

                result['views_count'] = int(topic.xpath('./dl/dd[@class="views"]/text()')[0])

                node_last_post_info = topic.xpath('./dl/dd[@class="lastpost"]/span/br/following::text()')[0]
                last_post_dt = datetime.datetime.strptime(node_last_post_info, '%d.%m.%Y %H:%M')
                result['last_post_ts'] = int(last_post_dt.replace(tzinfo=datetime.timezone.utc).timestamp())
                results.append(result)
        return results

    async def get_topic_content(self, topics_listing: list):
        await asyncio.sleep(self.pause)

        urls = []
        for topic in topics_listing[:]:
            req_params = {'f': self.FORUMS.get('buy'), 't': topic.get('id')}
            urls.append(
                (
                    self.TOPIC_URL,
                    req_params
                )
            )

        topics_data = []
        result = await self._get_content(urls)
        for topic in result:
            if topic:
                for url, content in topic.items():
                    topics_data.append(
                        {
                            'id': url.split('=')[-1],
                            'content': content
                        }
                    )
        return topics_data

    def process_topic(self, data):
        content = ''
        if data:
            root = html.fromstring(data)
            post_elem = root.xpath('//div[@class="content"]')[0]
            post_text = post_elem.xpath('./descendant-or-self::text()')
            content = ' '.join(post_text)
        return content
