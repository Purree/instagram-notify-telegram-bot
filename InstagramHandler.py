import asyncio
import threading
from datetime import datetime

import aiohttp

from Debug import Debug
from InstagramController import InstagramController


class InstagramHandler:
    def __init__(self, parameters, telegram):
        self._parameters = parameters
        self.controller = InstagramController()
        self.telegram = telegram
        self.debug = Debug()
        threading.Thread(target=self.new_events_handler, args=()).start()

    def new_events_handler(self):
        threading.Timer(float(self._parameters["newpostscheckinginterval"]), self.new_events_handler).start()
        self.debug.dump("Checked at", datetime.now().strftime("%H:%M:%S"))
        self.debug.dump(f"Next check after {self._parameters['newpostscheckinginterval']} seconds")
        users_with_new_posts = self.compare_bloggers_information()

        if not users_with_new_posts:
            return

        for blogger_id in users_with_new_posts:
            blogger_data_with_subscribers = self.controller.get_blogger_subscribers(blogger_id)

            if not blogger_data_with_subscribers:
                return

            if 'post' in users_with_new_posts[blogger_id]:
                for message in self.telegram.send_new_posts_message(blogger_data_with_subscribers):
                    self.telegram.send_medias(users_with_new_posts[blogger_id]['post'][2],
                                              [message.chat_id],
                                              message.message_id)

                self.controller.update_blogger_posts_info(
                    users_with_new_posts[blogger_id]['post'][0],
                    users_with_new_posts[blogger_id]['post'][1],
                    blogger_id
                )

            if 'story' in users_with_new_posts[blogger_id]:
                for message in self.telegram.send_new_stories_message(blogger_data_with_subscribers):
                    self.telegram.send_medias(users_with_new_posts[blogger_id]['story'][1],
                                              [message.chat_id],
                                              message.message_id)

                self.controller.update_blogger_stories_info(
                    users_with_new_posts[blogger_id]['story'][0],
                    blogger_id
                )

            if 'reels' in users_with_new_posts[blogger_id]:
                if users_with_new_posts[blogger_id]['reels']['new'] != {}:
                    self.telegram.send_new_reels_message(blogger_data_with_subscribers)

                    self.update_reels_in_database(users_with_new_posts[blogger_id]['reels']['new'], blogger_id)

                if users_with_new_posts[blogger_id]['reels']['deleted'] != {}:
                    self.delete_reels_from_database(users_with_new_posts[blogger_id]['reels']['deleted'])

    def compare_bloggers_information(self):
        bloggers_with_new_events = {}
        bloggers = self.controller.get_bloggers_with_subscriptions()

        self.handle_connection_errors(self.main_data_handler, bloggers, bloggers_with_new_events)

        self.handle_connection_errors(self.reels_handler, bloggers, bloggers_with_new_events)

        self.handle_connection_errors(self.stories_handler, bloggers, bloggers_with_new_events)

        self.debug.dump("Bloggers with new data: ", bloggers_with_new_events)

        return bloggers_with_new_events

    def handle_connection_errors(self, function, *params):
        try:
            function(*params)
        except aiohttp.client_exceptions.ClientConnectorError:
            self.debug.error_handler("Error when trying to connect to Instagram")
        except asyncio.exceptions.TimeoutError:
            self.debug.error_handler("Timeout on trying to connect to Instagram")

    def main_data_handler(self, bloggers, bloggers_with_new_events):
        for index, blogger_info in enumerate(
                self.controller.get_main_info_of_many_bloggers([blogger[1] for blogger in bloggers])):

            if blogger_info == {}:
                self.remove_blogger(bloggers[index][0], bloggers[index][1])
                return {}

            # If count of posts != 0 and last post id > last saved post id
            if blogger_info['graphql']['user']['edge_owner_to_timeline_media']['count'] != 0 and \
                    int(blogger_info['graphql']['user']['edge_owner_to_timeline_media']['edges'][0]['node']['id']) > \
                    int(bloggers[index][3]):
                bloggers_with_new_events[(self.controller.get_blogger_id(blogger_data=blogger_info))] = \
                    {
                        "post":
                            [
                                blogger_info['graphql']['user']['edge_owner_to_timeline_media']['count'],
                                blogger_info['graphql']['user']['edge_owner_to_timeline_media']['edges'][0]['node'][
                                    'id'],
                                self.get_new_posts_data(blogger_info, bloggers[index][3])
                            ]
                    }

        return bloggers_with_new_events

    def stories_handler(self, bloggers, bloggers_with_new_events):
        for index, blogger_stories in enumerate(
                self.controller.get_stories_of_many_bloggers([blogger[0] for blogger in bloggers])):

            # If count of stories != 0 and last story id > last saved story id
            if blogger_stories['items'] != [] and \
                    int(self.controller.get_last_blogger_story_id_from_data(blogger_stories)) > int(bloggers[index][4]):
                blogger_id = blogger_stories['id']

                if blogger_id not in bloggers_with_new_events:
                    bloggers_with_new_events[blogger_id] = {}

                bloggers_with_new_events[blogger_id]['story'] = \
                    [
                        self.controller.get_last_blogger_story_id_from_data(blogger_stories),
                        self.get_new_stories_data(blogger_stories, bloggers[index][4])
                    ]
        return bloggers_with_new_events

    def reels_handler(self, bloggers, bloggers_with_new_events):
        new_reels = {}
        for index, blogger_reels in enumerate(
                self.controller.get_reels_of_many_bloggers([blogger[0] for blogger in bloggers])):

            if not blogger_reels['tray']:
                continue

            blogger_id = bloggers[index][0]

            saved_reels = self.controller.get_saved_blogger_reels(blogger_id)
            deleted_reels = saved_reels.copy()

            for reel in blogger_reels['tray']:
                reel_album_id = int(self.controller.get_reel_album_id(reel))
                reel_id = int(reel['latest_reel_media'])

                if reel_album_id not in saved_reels:
                    new_reels[reel_album_id] = reel_id

                    if blogger_id not in bloggers_with_new_events:
                        bloggers_with_new_events[blogger_id] = {}

                    continue

                if reel_id > saved_reels[reel_album_id]:
                    new_reels[reel_album_id] = reel_id

                    if blogger_id not in bloggers_with_new_events:
                        bloggers_with_new_events[blogger_id] = {}

                del deleted_reels[reel_album_id]

            if blogger_id not in bloggers_with_new_events:
                bloggers_with_new_events[blogger_id] = {}

            bloggers_with_new_events[blogger_id]['reels'] = {}
            bloggers_with_new_events[blogger_id]['reels']['new'] = new_reels
            bloggers_with_new_events[blogger_id]['reels']['deleted'] = deleted_reels



            self.debug.dump(new_reels, "- new reels")
            self.debug.dump(deleted_reels, "- deleted reels")

        return bloggers_with_new_events

    def remove_blogger(self, blogger_id, blogger_name):
        for blogger_with_subscriber in self.controller.get_blogger_subscribers(blogger_id):
            self.telegram.send_custom_message(
                "Блоггер %s сменил никнейм, переподпишитесь на него с новым ником" % blogger_with_subscriber[1],
                blogger_with_subscriber[4]
            )

        self.controller.delete_blogger(blogger_name)

    def get_new_posts_data(self, blogger_info, last_post_id):
        if blogger_info['graphql']['user']['edge_owner_to_timeline_media']['count'] == 0:
            return

        return self.parse_post_data(blogger_info['graphql']['user']['edge_owner_to_timeline_media'], last_post_id)

    def parse_post_data(self, posts, last_post_id, new_posts=None):
        if new_posts is None:
            new_posts = {}

        for post in posts['edges']:
            post = post['node']

            if int(post['id']) <= int(last_post_id):
                break

            new_posts[post['id']] = {}

            if 'video' in post['__typename'].lower():
                new_posts[post['id']]['type'] = 'video'
                new_posts[post['id']]['text'] = post['edge_media_to_caption']['edges'][0]['node']['text'] \
                    if 'edge_media_to_caption' in post and post['edge_media_to_caption']['edges'] != [] \
                    else ''
                new_posts[post['id']]['url'] = post['video_url']
                new_posts[post['id']]['image_url'] = post['display_url']

            if 'image' in post['__typename'].lower():
                new_posts[post['id']]['type'] = 'image'
                new_posts[post['id']]['text'] = post['edge_media_to_caption']['edges'][0]['node']['text'] \
                    if 'edge_media_to_caption' in post and post['edge_media_to_caption']['edges'] != [] \
                    else ''
                new_posts[post['id']]['url'] = post['display_url']

            if 'sidecar' in post['__typename'].lower():
                new_posts[post['id']]['type'] = 'sidecar'
                new_posts[post['id']]['text'] = post['edge_media_to_caption']['edges'][0]['node']['text'] \
                    if 'edge_media_to_caption' in post and post['edge_media_to_caption']['edges'] != [] \
                    else ''

                new_posts[post['id']]['attachments'] = {}

                self.parse_post_data(post['edge_sidecar_to_children'], last_post_id,
                                     new_posts[post['id']]['attachments'])

        return new_posts

    def get_new_stories_data(self, blogger_stories, last_story_id):
        if not blogger_stories['items']:
            return

        return self.parse_stories_data(blogger_stories, last_story_id)

    def parse_stories_data(self, blogger_stories, last_story_id):
        new_stories = {}

        for story in blogger_stories['items']:
            story_id = story['id'].split('_')[0]

            if int(story_id) <= int(last_story_id):
                break

            new_stories[story_id] = {}

            if story['media_type'] == 2:  # 2 - video
                new_stories[story_id]['type'] = 'video'
                new_stories[story_id]['text'] = ''
                new_stories[story_id]['url'] = story['video_versions']['candidates'][0]['url'] \
                    if 'candidates' in story['video_versions'] \
                    else story['video_versions'][0]['url']
                new_stories[story_id]['image_url'] = story['image_versions2']['candidates'][0]['url']

            if story['media_type'] == 1:  # 1 - image
                new_stories[story_id]['type'] = 'image'
                new_stories[story_id]['text'] = ''
                new_stories[story_id]['url'] = story['image_versions2']['candidates'][0]['url']

        return new_stories

    def delete_reels_from_database(self, deleted_reels):
        self.controller.delete_many_reels_albums(deleted_reels)

    def update_reels_in_database(self, new_reels, blogger_id):
        for new_reel in new_reels:
            if self.controller.update_reel_id_in_album(blogger_id, new_reel, new_reels[new_reel]) == 0:
                self.controller.add_reel_to_blogger(blogger_id, new_reel, new_reels[new_reel])
