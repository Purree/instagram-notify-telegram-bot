import threading

from InstagramController import InstagramController


class Instagram:
    def __init__(self, parameters):
        self._parameters = parameters
        self.controller = InstagramController()

        threading.Thread(target=self.compare_bloggers_information, args=()).start()
        threading.Timer(float(parameters["newpostscheckinginterval"]), self.compare_bloggers_information).start()

    def compare_bloggers_information(self):
        ids_of_bloggers_with_new_posts = []
        bloggers = self.controller.get_bloggers_with_subscriptions()

        for index, blogger_info in enumerate(self.controller.get_main_info_of_many_bloggers([blogger[1] for blogger in bloggers])):
            # If last post id > last saved post id

            if blogger_info['graphql']['user']['edge_owner_to_timeline_media']['count'] != 0 and \
                    blogger_info['graphql']['user']['edge_owner_to_timeline_media']['edges'][0]['node']['id'] > bloggers[index][3]:
                ids_of_bloggers_with_new_posts += self.controller.get_blogger_id(blogger_data=blogger_info)

        return ids_of_bloggers_with_new_posts
