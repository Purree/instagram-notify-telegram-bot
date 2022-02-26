from Database import Database
from Config import Config
from InstagramController import InstagramController


class UserController:
    def __init__(self):
        self.database = Database(Config().get_all_section_parameters('DATABASE'))
        self.instagram_controller = InstagramController()

    def create_new_user(self, telegram_id):
        return self.database.add_new_user(telegram_id)

    def subscribe_user(self, telegram_id, blogger_short_name):
        user_tariffs = self.get_active_user_tariffs(telegram_id)
        if not user_tariffs:
            self.add_tariff_to_user(1, telegram_id)

            user_tariffs = self.get_active_user_tariffs(telegram_id)

        subscriptions_count = user_tariffs[0][4]

        for tariff in user_tariffs:
            if tariff[4] > subscriptions_count:
                subscriptions_count = tariff[4]

        if len(self.get_user_subscriptions(telegram_id)) >= subscriptions_count:
            return False

        blogger_data = self.database.search_blogger_in_database(blogger_short_name)

        if blogger_data is not None:
            self.database.subscribe_user(telegram_id, blogger_data[0])
        else:
            blogger_info = self.instagram_controller.get_blogger_main_info(blogger_short_name)
            posts_count = blogger_info['graphql']['user']['edge_owner_to_timeline_media']['count']
            last_post_id = blogger_info['graphql']['user']['edge_owner_to_timeline_media']['edges'][0]['node']['id'] \
                if posts_count != 0 else 0

            blogger_data = [
                self.instagram_controller.get_blogger_id(blogger_data=blogger_info),
                blogger_short_name,
                posts_count,
                last_post_id
            ]
            self.database.add_new_blogger(blogger_data)
            self.database.subscribe_user(telegram_id, blogger_data[0])

    def get_active_user_tariffs(self, telegram_id):
        return self.database.get_valid_user_tariffs(telegram_id)

    def get_user_tariffs(self, telegram_id):
        return self.database.get_user_tariffs(telegram_id)

    def get_user_subscriptions(self, telegram_id):
        return self.database.get_user_subscriptions(telegram_id)

    def add_tariff_to_user(self, tariff_id, telegram_id):
        self.database.add_tariff_to_user(tariff_id=tariff_id, telegram_id=telegram_id)
