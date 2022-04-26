import aiohttp
import asyncio

from aiohttp import TraceConfig
from aiohttp_retry import RetryClient, ExponentialRetry
import platform

from Config import Config
from Database import Database
from Debug import Debug


class InstagramController:
    BLOGGER_DATA_LINK = "https://www.instagram.com/%s/?__a=1"  # %s - blogger short name
    BLOGGER_STORIES_LINK = "https://i.instagram.com/api/v1/feed/user/%s/reel_media/"
    BLOGGER_REELS_LINK = "https://i.instagram.com/api/v1/highlights/%s/highlights_tray/"
    BLOGGER_STORIES_USER_AGENT = "Mozilla/5.0 (iPhone; CPU iPhone OS 12_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Instagram 105.0.0.11.118 (iPhone11,8; iOS 12_3_1; en_US; en-US; scale=2.00; 828x1792; 165586599)"

    def __init__(self):
        self.config = Config()
        self.database = Database(self.config.get_all_section_parameters('DATABASE'))
        self.proxy = self.config.read_from_config("PROXY", "proxy")
        self.debug = Debug()

        self.trace_config = TraceConfig()
        self.trace_config.on_request_exception.append(self.on_request_exception)

        self.retry_options = ExponentialRetry(
            attempts=int(self.config.read_from_config("INSTAGRAM", "requestsreconnectattemptcount")),
            start_timeout=0.1,
            max_timeout=int(self.config.read_from_config("INSTAGRAM", "requestsreconnectmaxinterval")),
            factor=int(self.config.read_from_config("INSTAGRAM", "requestsreconnectinterval")))

        if platform.system() == 'Windows':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        setattr(asyncio.sslproto._SSLProtocolTransport, "_start_tls_compatible", True)

    async def on_request_exception(self, session, trace_config_ctx, params):
        Debug().error_handler(Exception('Error on request send: ', trace_config_ctx, params))

    def get_blogger_id(self, short_name=None, blogger_data=None):
        if short_name is None and blogger_data is None:
            return None

        return (blogger_data
                if blogger_data is not None
                else self.get_blogger_main_info(short_name)
                )['logging_page_id'].replace('profilePage_', '')

    async def _get_blogger_main_info(self, session, blogger_short_name):
        async with session.get(self.BLOGGER_DATA_LINK % blogger_short_name, ssl=False, proxy=self.proxy,
                               cookies={
                                   "sessionid": self.config.read_from_config("INSTAGRAM", "sessionid")},
                               timeout=float(
                                   self.config.read_from_config('INSTAGRAM', 'responsetime'))) as response:
            return await response.json()

    async def _get_main_info_of_many_bloggers(self, bloggers_short_names):
        async with RetryClient(raise_for_status=True, retry_options=self.retry_options,
                               trace_configs=[self.trace_config]) as session:
            tasks = []

            for blogger_short_name in bloggers_short_names:
                tasks.append(asyncio.ensure_future(self._get_blogger_main_info(session, blogger_short_name)))

            return await asyncio.gather(*tasks)

    def get_blogger_main_info(self, blogger_short_name):
        return asyncio.run(self._get_main_info_of_many_bloggers([blogger_short_name]))[0]

    def get_main_info_of_many_bloggers(self, bloggers_short_names):
        return asyncio.run(self._get_main_info_of_many_bloggers(bloggers_short_names))

    async def _get_blogger_stories(self, session, blogger_id):
        async with session.get(self.BLOGGER_STORIES_LINK % blogger_id, ssl=False, proxy=self.proxy,
                               headers={
                                   'User-Agent': self.BLOGGER_STORIES_USER_AGENT
                               },
                               cookies={
                                   "sessionid": self.config.read_from_config("INSTAGRAM", "sessionid")},
                               timeout=float(
                                   self.config.read_from_config('INSTAGRAM', 'responsetime'))) as response:
            return await response.json()

    async def _get_stories_of_many_bloggers(self, blogger_ids):
        async with RetryClient(raise_for_status=True, retry_options=self.retry_options,
                               trace_configs=[self.trace_config]) as session:
            tasks = []

            for blogger_id in blogger_ids:
                tasks.append(asyncio.ensure_future(self._get_blogger_stories(session, blogger_id)))

            return await asyncio.gather(*tasks)

    def get_blogger_stories(self, blogger_id):
        return asyncio.run(self._get_stories_of_many_bloggers([blogger_id]))[0]

    def get_stories_of_many_bloggers(self, blogger_ids):
        return asyncio.run(self._get_stories_of_many_bloggers(blogger_ids))

    async def _get_blogger_reels(self, session, blogger_id):
        async with session.get(self.BLOGGER_REELS_LINK % blogger_id, ssl=False, proxy=self.proxy,
                               headers={
                                   'User-Agent': self.BLOGGER_STORIES_USER_AGENT
                               },
                               cookies={
                                   "sessionid": self.config.read_from_config("INSTAGRAM", "sessionid")},
                               timeout=float(
                                   self.config.read_from_config('INSTAGRAM', 'responsetime'))) as response:
            return await response.json()

    async def _get_reels_of_many_bloggers(self, blogger_ids):
        async with RetryClient(raise_for_status=True, retry_options=self.retry_options,
                               trace_configs=[self.trace_config]) as session:
            tasks = []

            for blogger_id in blogger_ids:
                tasks.append(asyncio.ensure_future(self._get_blogger_reels(session, blogger_id)))

            return await asyncio.gather(*tasks)

    def get_blogger_reels(self, blogger_id):
        return asyncio.run(self._get_reels_of_many_bloggers([blogger_id]))[0]

    def get_reels_of_many_bloggers(self, blogger_ids):
        return asyncio.run(self._get_reels_of_many_bloggers(blogger_ids))

    def get_reel_album_id(self, reel_data):
        return reel_data['id'].split('highlight:')[1]

    def get_saved_blogger_reels(self, blogger_id):
        return self.database.get_blogger_reels(blogger_id)

    def get_bloggers_with_subscriptions(self):
        return self.database.get_bloggers_with_subscriptions()

    def get_last_blogger_story_id_from_data(self, user_data):
        return user_data['items'][-1]['id'].split('_')[0] if user_data['items'] != [] else 0

    def get_blogger_subscribers(self, blogger_id):
        return self.database.get_all_blogger_subscribers(blogger_id)

    def update_blogger_posts_info(self, posts_count, last_post_id, blogger_id):
        self.database.update_blogger_posts_info(posts_count, last_post_id, blogger_id)

    def update_blogger_stories_info(self, last_story_id, blogger_id):
        self.database.update_blogger_stories_info(last_story_id, blogger_id)

    def delete_blogger(self, blogger_short_name):
        self.database.delete_blogger(blogger_short_name)

    def delete_many_reels_albums(self, albums_ids):
        for album_id in albums_ids:
            self.delete_reel_album(album_id)

    def delete_reel_album(self, album_id):
        self.database.delete_reels_album(album_id)

    def add_reel_to_blogger(self, blogger_id, album_id, reel_id):
        self.database.add_reel_to_blogger(blogger_id, album_id, reel_id)

    def update_reel_id_in_album(self, blogger_id, album_id, reel_id):
        return self.database.update_reel_id_in_album(blogger_id, album_id, reel_id)
