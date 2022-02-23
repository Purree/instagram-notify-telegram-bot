from Database import Database
from Config import Config
from InstagramController import InstagramController


class UserController:
    def __init__(self):
        self.database = Database(Config().get_all_section_parameters('DATABASE'))
        self.instagram_controller = InstagramController()

    def create_new_user(self, telegram_id):
        self.database.add_new_user(telegram_id)

    def subscribe_user(self, telegram_id, blogger_short_name):
        blogger_data = self.database.search_blogger_in_database(blogger_short_name)

        if blogger_data is not None:
            self.database.subscribe_user(telegram_id, blogger_data['instagram_id'])
        else:
            blogger_info = self.instagram_controller.get_blogger_main_info(blogger_short_name)
            blogger_data = [
                self.instagram_controller.get_blogger_id(blogger_data=blogger_info),
                blogger_short_name,
                blogger_info['graphql']['user']['edge_owner_to_timeline_media']['count'],
                blogger_info['graphql']['user']['edge_owner_to_timeline_media']['edges'][0]['node']['id']
            ]
            self.database.add_new_blogger(blogger_data)
            self.database.subscribe_user(telegram_id, blogger_data[0])

