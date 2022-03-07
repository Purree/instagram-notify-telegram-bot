import threading

from InstagramController import InstagramController


class Instagram:
    def __init__(self):
        self.controller = InstagramController()
        self.get_bloggers_info()

    def get_bloggers_info(self, interval=5):
        threading.Timer(interval, self.get_bloggers_info).start()
        info = []
        for blogger in self.controller.get_bloggers_with_subscriptions():
            info = self.controller.get_blogger_main_info(blogger[1])

        return info
