import threading
from datetime import datetime

from Debug import Debug
from InstagramController import InstagramController


class Instagram:
    def __init__(self, parameters, telegram):
        self._parameters = parameters
        self.controller = InstagramController()
        self.telegram = telegram
        self.debug = Debug()
        threading.Thread(target=self.new_posts_handler, args=()).start()

    def new_posts_handler(self):
        threading.Timer(float(self._parameters["newpostscheckinginterval"]), self.new_posts_handler).start()
        self.debug.dump("Checked at", datetime.now().strftime("%H:%M:%S"))
        self.debug.dump(f"Next check after {self._parameters['newpostscheckinginterval']} seconds")
        users_with_new_posts = self.compare_bloggers_information()

        if not users_with_new_posts:
            return

        for blogger_id in users_with_new_posts:
            blogger_data_with_subscribers = self.controller.get_blogger_subscribers(blogger_id)
            self.telegram.send_new_posts_message(blogger_data_with_subscribers)

            self.controller.update_blogger_posts_info(
                users_with_new_posts[blogger_id][0],
                users_with_new_posts[blogger_id][1],
                blogger_id
            )

    def compare_bloggers_information(self):
        bloggers_with_new_posts = {}
        bloggers = self.controller.get_bloggers_with_subscriptions()

        for index, blogger_info in enumerate(
                self.controller.get_main_info_of_many_bloggers([blogger[1] for blogger in bloggers])):
            # If last post id > last saved post id

            if blogger_info == {}:
                self.remove_blogger(bloggers[index][0], bloggers[index][1])
                return {}

            if blogger_info['graphql']['user']['edge_owner_to_timeline_media']['count'] != 0 and \
                    blogger_info['graphql']['user']['edge_owner_to_timeline_media']['edges'][0]['node']['id'] > \
                    bloggers[index][3]:
                bloggers_with_new_posts[(self.controller.get_blogger_id(blogger_data=blogger_info))] = \
                    [
                        blogger_info['graphql']['user']['edge_owner_to_timeline_media']['count'],
                        blogger_info['graphql']['user']['edge_owner_to_timeline_media']['edges'][0]['node']['id']
                    ]

        self.debug.dump("Bloggers with new posts: ", bloggers_with_new_posts)
        return bloggers_with_new_posts

    def remove_blogger(self, blogger_id, blogger_name):
        for blogger_with_subscriber in self.controller.get_blogger_subscribers(blogger_id):
            self.telegram.send_custom_message(
                "Блоггер %s сменил никнейм, переподпишитесь на него с новым ником" % blogger_with_subscriber[1],
                blogger_with_subscriber[4]
            )

        self.controller.delete_blogger(blogger_name)
