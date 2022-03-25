import aiohttp
import asyncio
import requests

from Config import Config
from Database import Database
from Debug import Debug


class InstagramController:
    BLOGGER_DATA_LINK = "https://www.instagram.com/%s/?__a=1"  # %s - blogger short name
    BLOGGER_STORIES_LINK = "https://i.instagram.com/api/v1/feed/user/%s/reel_media/"
    BLOGGER_STORIES_USER_AGENT = "Mozilla/5.0 (iPhone; CPU iPhone OS 12_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Instagram 105.0.0.11.118 (iPhone11,8; iOS 12_3_1; en_US; en-US; scale=2.00; 828x1792; 165586599)"

    def __init__(self):
        self.config = Config()
        self.database = Database(self.config.get_all_section_parameters('DATABASE'))
        self.proxy = self.config.read_from_config("PROXY", "proxy")
        self.debug = Debug()
        setattr(asyncio.sslproto._SSLProtocolTransport, "_start_tls_compatible", True)

    def get_blogger_id(self, short_name=None, blogger_data=None):
        if short_name is None and blogger_data is None:
            return None

        return (blogger_data
                if blogger_data is not None
                else self.get_blogger_main_info(short_name)
                )['logging_page_id'].replace('profilePage_', '')

    async def _get_blogger_main_info(self, session, blogger_short_name):
        async with session.get(self.BLOGGER_DATA_LINK % blogger_short_name, proxy=self.proxy,
                               cookies={
                                   "sessionid": self.config.read_from_config("INSTAGRAM", "sessionid")}) as response:
            return await response.json()

    async def _get_main_info_of_many_bloggers(self, bloggers_short_names):
        async with aiohttp.ClientSession() as session:
            tasks = []

            for blogger_short_name in bloggers_short_names:
                tasks.append(asyncio.ensure_future(self._get_blogger_main_info(session, blogger_short_name)))

            return await asyncio.gather(*tasks)

    def get_blogger_main_info(self, blogger_short_name):
        return asyncio.run(self._get_main_info_of_many_bloggers([blogger_short_name]))[0]

    def get_main_info_of_many_bloggers(self, bloggers_short_names):
        return asyncio.run(self._get_main_info_of_many_bloggers(bloggers_short_names))

    async def _get_blogger_stories(self, session, blogger_id):
        async with session.get(self.BLOGGER_STORIES_LINK % blogger_id, proxy=self.proxy,
                               headers={
                                   'User-Agent': self.BLOGGER_STORIES_USER_AGENT
                               },
                               cookies={
                                   "sessionid": self.config.read_from_config("INSTAGRAM", "sessionid")}) as response:
            return await response.json()

    async def _get_stories_of_many_bloggers(self, blogger_ids):
        async with aiohttp.ClientSession() as session:
            tasks = []

            for blogger_id in blogger_ids:
                tasks.append(asyncio.ensure_future(self._get_blogger_stories(session, blogger_id)))

            return await asyncio.gather(*tasks)

    def get_blogger_stories(self, blogger_id):
        return asyncio.run(self._get_stories_of_many_bloggers([blogger_id]))[0]

    def get_stories_of_many_bloggers(self, blogger_ids):
        return asyncio.run(self._get_stories_of_many_bloggers(blogger_ids))

    def get_bloggers_with_subscriptions(self):
        return self.database.get_bloggers_with_subscriptions()

    def get_last_blogger_story_id_from_data(self, user_data):
        return user_data['items'][-1]['id'].split('_')[1] if user_data['items'] != [] else 0

    def get_blogger_subscribers(self, blogger_id):
        return self.database.get_all_blogger_subscribers(blogger_id)

    def update_blogger_posts_info(self, posts_count, last_post_id, blogger_id):
        self.database.update_blogger_posts_info(posts_count, last_post_id, blogger_id)

    def delete_blogger(self, blogger_short_name):
        self.database.delete_blogger(blogger_short_name)
