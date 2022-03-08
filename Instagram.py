import threading

from InstagramController import InstagramController


class Instagram:
    def __init__(self, parameters):
        self._parameters = parameters
        self.controller = InstagramController()
        threading.Timer(parameters["newPostsCheckingInterval"], self.compare_bloggers_information).start()

    def compare_bloggers_information(self):
        ids_of_bloggers_with_new_posts = []
        for blogger in self.controller.get_bloggers_with_subscriptions():
            blogger_info = self.controller.get_blogger_main_info(blogger[1])
            # If last post id > last saved post id
            if blogger_info['graphql']['user']['edge_owner_to_timeline_media']['edges'][0]['node']['id'] > blogger[3]:
                ids_of_bloggers_with_new_posts += self.controller.get_blogger_id(blogger_data=blogger_info)

        return ids_of_bloggers_with_new_posts
