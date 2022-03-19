import threading

from InstagramController import InstagramController


class Instagram:
    def __init__(self, parameters, telegram):
        self._parameters = parameters
        self.controller = InstagramController()
        self.telegram = telegram
        threading.Thread(target=self.new_posts_handler, args=()).start()
        threading.Timer(float(parameters["newpostscheckinginterval"]), self.compare_bloggers_information).start()

    def new_posts_handler(self):
        users_with_new_posts = self.compare_bloggers_information()

        if not users_with_new_posts:
            return

        for blogger_id in users_with_new_posts:
            self.telegram.send_new_posts_message(self.controller.get_blogger_subscribers(blogger_id))

            # Обновляем posts_count и last_post_id у blogger_id на users_with_new_posts[blogger_id][0] и 1 соответственно

    def compare_bloggers_information(self):
        bloggers_with_new_posts = {}
        bloggers = self.controller.get_bloggers_with_subscriptions()

        for index, blogger_info in enumerate(
                self.controller.get_main_info_of_many_bloggers([blogger[1] for blogger in bloggers])):
            # If last post id > last saved post id

            if blogger_info['graphql']['user']['edge_owner_to_timeline_media']['count'] != 0 and \
                    blogger_info['graphql']['user']['edge_owner_to_timeline_media']['edges'][0]['node']['id'] > \
                    bloggers[index][3]:
                bloggers_with_new_posts[(self.controller.get_blogger_id(blogger_data=blogger_info))] = \
                    [
                        blogger_info['graphql']['user']['edge_owner_to_timeline_media']['count'],
                        blogger_info['graphql']['user']['edge_owner_to_timeline_media']['edges'][0]['node']['id']
                    ]

        return bloggers_with_new_posts
