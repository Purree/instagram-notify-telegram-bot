from datetime import datetime

import mysql.connector

from FunctionResult import FunctionResult


def _use_one_time_connection(function_to_decorate):
    def wrapper_function(self, *params):
        self.connect_and_set_cursors(self._parameters)
        decorated_function_result = function_to_decorate(self, *params)
        self.connection.close()
        return decorated_function_result

    return wrapper_function


class Database:
    def __init__(self, parameters):
        self._parameters = parameters
        self.connection = None
        self.cursor = None

    def connect_and_set_cursors(self, parameters):
        connection_result = self.connect(parameters)
        self.connection = connection_result['connection']
        self.cursor = connection_result['cursor']

    # Connect to database
    def connect(self, parameters):
        connection = mysql.connector.connect(
            host=parameters['databasehost'],
            port=parameters['databaseport'],
            database=parameters['databasename'],
            user=parameters['databaselogin'],
            password=parameters['databasepassword']
        )

        return {"connection": connection, "cursor": connection.cursor(prepared=True)}

    # Method what will be called if table isn't exists
    # Method must be called only from places where user cannot change something
    @_use_one_time_connection
    def execute_custom_query(self, command, commit=False):
        print(self.cursor)
        self.cursor.execute(command)
        if commit:
            self.connection.commit()

        return self.cursor.fetchall()

    @_use_one_time_connection
    def add_new_user(self, telegram_id):
        self.cursor.execute("""SELECT * FROM users WHERE telegram_id = %s""", [telegram_id])

        if self.cursor.fetchone() is None:
            self.cursor.execute("""INSERT INTO users VALUES (%s)""", [telegram_id])

            self.connection.commit()
            return True

        return False

    """
    :param blogger_short_name: short instagram blogger name 
    :param blogger_id: id of blogger what were given by api 
    :returns: blogger by its short name if has been set
    :returns: blogger by its id if has been set
    :returns: blogger by both of these values if both are given
    :exception: if no argument were passed
    """

    @_use_one_time_connection
    def search_blogger_in_database(self, blogger_short_name=None, blogger_id=None):
        if blogger_short_name is None and blogger_id is None:
            raise Exception('One of arguments must be given')

        if blogger_short_name is not None and blogger_id is not None:
            self.cursor.execute("""SELECT * FROM bloggers WHERE short_name = %s AND instagram_id = %s""",
                                [blogger_short_name, blogger_id])

            return self.cursor.fetchone()

        if blogger_short_name is not None:
            self.cursor.execute("""SELECT * FROM bloggers WHERE short_name = %s""", [blogger_short_name])

            return self.cursor.fetchone()

        self.cursor.execute("""SELECT * FROM bloggers WHERE instagram_id = %s""", [blogger_id])

        return self.cursor.fetchone()

    @_use_one_time_connection
    def check_is_user_subscribe_for_blogger(self, telegram_id, blogger_short_name):
        self.cursor.execute("""SELECT * FROM user_subscriptions WHERE user_id = %s AND blogger_id = %s""",
                            [telegram_id, blogger_short_name])

        return self.cursor.fetchone() is not None

    @_use_one_time_connection
    def subscribe_user(self, telegram_id, blogger_short_name):
        if self.check_is_user_subscribe_for_blogger(telegram_id, blogger_short_name):
            return FunctionResult.error('Вы уже подписаны этого пользователя')

        self.cursor.execute("""INSERT INTO user_subscriptions VALUES (%s, %s)""", [telegram_id, blogger_short_name])

        self.connection.commit()

        return FunctionResult.success()

    # blogger_data - array of blogger id, blogger short name, posts count, last post id
    @_use_one_time_connection
    def add_new_blogger(self, blogger_data):
        if self.search_blogger_in_database(blogger_id=blogger_data[0]) is not None:
            return False

        self.cursor.execute("""INSERT INTO bloggers VALUES (%s, %s, %s, %s)""", blogger_data)

        self.connection.commit()
        return True

    @_use_one_time_connection
    def add_tariff_to_user(self, tariff_id, telegram_id, started_at=datetime.now()):
        self.cursor.execute("""INSERT INTO user_tariffs VALUES (%s, %s, %s)""", [telegram_id, tariff_id, started_at])

        self.connection.commit()

    @_use_one_time_connection
    def get_valid_user_tariffs(self, telegram_id):
        self.cursor.execute("""SELECT * FROM user_tariffs 
                                       INNER JOIN tariffs ON tariff_id = tariffs.id 
                                       WHERE user_id = %s AND (tariffs.duration IS NULL 
                                       OR UNIX_TIMESTAMP(started_at) + tariffs.duration >= UNIX_TIMESTAMP(now()))""",
                            [telegram_id])

        tariffs = self.cursor.fetchall()

        return tariffs

    @_use_one_time_connection
    def get_user_tariffs(self, telegram_id):
        self.cursor.execute("""SELECT * FROM user_tariffs 
                               INNER JOIN tariffs ON tariff_id = tariffs.id WHERE user_id = %s""",
                            [telegram_id])

        tariffs = self.cursor.fetchall()

        return tariffs

    @_use_one_time_connection
    def get_user_subscriptions(self, telegram_id):
        self.cursor.execute("""SELECT user_id, CONVERT(`blogger_id`, char), bloggers.short_name, 
                               bloggers.posts_count, CONVERT(bloggers.last_post_id, char) 
                               FROM user_subscriptions 
                               INNER JOIN bloggers ON blogger_id = instagram_id 
                               WHERE user_id = %s""", [telegram_id])

        return self.cursor.fetchall()

    @_use_one_time_connection
    def unsubscribe_user(self, telegram_id, blogger_id):
        self.cursor.execute("""DELETE
                               FROM user_subscriptions
                               WHERE user_id = %s
                               AND blogger_id = %s""", [telegram_id, blogger_id])

        self.connection.commit()

        if self.cursor.rowcount > 0:
            return FunctionResult.success()

        return FunctionResult.error("Вы не подписаны на этого пользователя")
