import threading
from datetime import datetime

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
                self.telegram.send_new_stories_message(blogger_data_with_subscribers)

                self.controller.update_blogger_stories_info(
                    users_with_new_posts[blogger_id]['story'][0],
                    blogger_id
                )

    def compare_bloggers_information(self):
        bloggers_with_new_events = {}
        bloggers = self.controller.get_bloggers_with_subscriptions()

        # Get blogger main data
        for index, blogger_info in enumerate(
                self.controller.get_main_info_of_many_bloggers([blogger[1] for blogger in bloggers])):

            if blogger_info == {}:
                self.remove_blogger(bloggers[index][0], bloggers[index][1])
                return {}

            # If count of posts != 0 and last post id > last saved post id
            if blogger_info['graphql']['user']['edge_owner_to_timeline_media']['count'] != 0 and \
                    blogger_info['graphql']['user']['edge_owner_to_timeline_media']['edges'][0]['node']['id'] > \
                    bloggers[index][3]:
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

        # Get blogger stories
        for index, blogger_stories in enumerate(
                self.controller.get_stories_of_many_bloggers([blogger[0] for blogger in bloggers])):

            # If count of stories != 0 and last story id > last saved story id
            if blogger_stories['items'] != [] and \
                    self.controller.get_last_blogger_story_id_from_data(blogger_stories) > bloggers[index][4]:
                blogger_id = blogger_stories['id']
                if blogger_id not in bloggers_with_new_events:
                    bloggers_with_new_events[blogger_id] = {}

                bloggers_with_new_events[blogger_id]['story'] = \
                    [
                        self.controller.get_last_blogger_story_id_from_data(blogger_stories)
                    ]

        self.debug.dump("Bloggers with new data: ", bloggers_with_new_events)
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

            if post['id'] <= last_post_id:
                break

            new_posts[post['id']] = {}

            if 'video' in post['__typename'].lower():
                new_posts[post['id']]['type'] = 'video'
                new_posts[post['id']]['text'] = post['edge_media_to_caption']['edges'][0]['node']['text'] \
                    if post['edge_media_to_caption']['edges'] != [] \
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
