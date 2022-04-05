import inspect

import mysql.connector

from FunctionResult import FunctionResult


def _use_one_time_connection(function_to_decorate):
    def wrapper_function(self, *params, connection=None, cursor=None):
        function_arguments = inspect.getfullargspec(function_to_decorate).args
        if "connection" not in function_arguments or "cursor" not in function_arguments:
            raise Exception("Connection(or cursor) parameters isn't exists in function")

        connection_index = function_arguments.index("connection")
        cursor_index = function_arguments.index("cursor")

        is_connection_need_to_close = False

        if len(params) < connection_index or params[connection_index - 1] is None \
                or not isinstance(params[connection_index - 1], mysql.connector.connection_cext.CMySQLConnection):
            # Fill all params with None while count of params less than count need to have
            while len(params) < connection_index - 1:
                params += (None,)

            new_connection = self.connect(self._parameters)
            connection = new_connection["connection"]
            params = params[0:connection_index] + (connection,) + params[connection_index:]

            while len(params) < cursor_index - 1:
                params += (None,)

            params = params[0:cursor_index] + (new_connection['cursor'],) + params[cursor_index:]

            is_connection_need_to_close = True

        decorated_function_result = function_to_decorate(self, *params)

        if is_connection_need_to_close:
            connection.close()

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

        return {"connection": connection, "cursor": self.get_cursor(connection)}

    def get_cursor(self, connection):
        return connection.cursor(prepared=True)

    # Method what will be called if table isn't exists
    # Method must be called only from places where user cannot change something
    @_use_one_time_connection
    def execute_custom_query(self, command, commit=False, connection=None, cursor=None):
        cursor.execute(command)
        if commit:
            connection.commit()

        return cursor.fetchall()

    @_use_one_time_connection
    def add_new_user(self, telegram_id, connection=None, cursor=None):
        cursor.execute("""SELECT * FROM users WHERE telegram_id = %s""", [telegram_id])

        if cursor.fetchone() is None:
            cursor.execute("""INSERT INTO users VALUES (%s)""", [telegram_id])

            connection.commit()
            return True

        return False

    @_use_one_time_connection
    def get_bloggers_with_subscriptions(self, connection=None, cursor=None):
        cursor.execute("""SELECT CONVERT(instagram_id, char), short_name, posts_count, CONVERT(last_post_id, char),
                          CONVERT(last_story_id, char)
                                      FROM bloggers INNER JOIN user_subscriptions ON instagram_id = blogger_id""")

        return cursor.fetchall()

    @_use_one_time_connection
    def get_all_blogger_subscribers(self, blogger_id, connection=None, cursor=None):
        cursor.execute("""SELECT CONVERT(instagram_id, char), short_name, posts_count, CONVERT(last_post_id, char),  
                                      user_subscriptions.user_id
                                      FROM bloggers INNER JOIN user_subscriptions ON instagram_id = blogger_id 
                                      WHERE instagram_id = %s""", [f'{blogger_id}'])

        return cursor.fetchall()

    """
    :param blogger_short_name: short instagram blogger name
    :param blogger_id: id of blogger what were given by api
    :returns: blogger by its short name if has been set
    :returns: blogger by its id if has been set
    :returns: blogger by both of these values if both are given
    :exception: if no argument were passed
    """

    @_use_one_time_connection
    def search_blogger_in_database(self, blogger_short_name=None, blogger_id=None, connection=None, cursor=None):
        if blogger_short_name is None and blogger_id is None:
            raise Exception('One of arguments must be given')

        if blogger_short_name is not None and blogger_id is not None:
            cursor.execute("""SELECT CONVERT(instagram_id, char), short_name, posts_count, CONVERT(last_post_id, char) 
                              FROM bloggers WHERE short_name = %s AND instagram_id = %s""",
                           [blogger_short_name, f'{blogger_id}'])

            return cursor.fetchone()

        if blogger_short_name is not None:
            cursor.execute("""SELECT CONVERT(instagram_id, char), short_name, posts_count, CONVERT(last_post_id, char)
                              FROM bloggers WHERE short_name = %s""", [blogger_short_name])

            return cursor.fetchone()

        cursor.execute("""SELECT CONVERT(instagram_id, char), short_name, posts_count, CONVERT(last_post_id, char)
                          FROM bloggers WHERE instagram_id = %s""", [f'{blogger_id}'])

        return cursor.fetchone()

    @_use_one_time_connection
    def check_is_user_subscribe_for_blogger(self, telegram_id, blogger_short_name, connection=None, cursor=None):
        cursor.execute("""SELECT * FROM user_subscriptions WHERE user_id = %s AND blogger_id = %s""",
                       [telegram_id, blogger_short_name])

        return cursor.fetchone() is not None

    @_use_one_time_connection
    def subscribe_user(self, telegram_id, blogger_short_name, connection=None, cursor=None):
        if self.check_is_user_subscribe_for_blogger(telegram_id, blogger_short_name, connection=connection,
                                                    cursor=cursor):
            return FunctionResult.error('Вы уже подписаны этого пользователя')

        cursor.execute("""INSERT INTO user_subscriptions VALUES (%s, %s)""", [telegram_id, blogger_short_name])

        connection.commit()

        return FunctionResult.success()

    # blogger_data - array of blogger id, blogger short name, posts count, last post id
    @_use_one_time_connection
    def add_new_blogger(self, blogger_data, connection=None, cursor=None):
        if self.search_blogger_in_database(None, blogger_data[0], connection=connection,
                                           cursor=cursor) is not None:
            return False

        cursor.execute("""INSERT INTO bloggers VALUES (%s, %s, %s, %s, %s)""",
                       [f'{blogger_data[0]}', f'{blogger_data[1]}', f'{blogger_data[2]}', f'{blogger_data[3]}',
                        f'{blogger_data[4]}'])

        connection.commit()

        if blogger_data[5] is not {}:
            for album_id in blogger_data[5]:
                self.add_reel_to_blogger(blogger_data[0], album_id, blogger_data[5][album_id], connection, cursor)

        return True

    @_use_one_time_connection
    def add_tariff_to_user(self, tariff_id, telegram_id, started_at, connection=None, cursor=None):
        cursor.execute("""INSERT INTO user_tariffs VALUES (%s, %s, %s)""", [telegram_id, tariff_id, started_at])

        connection.commit()

    @_use_one_time_connection
    def get_valid_user_tariffs(self, telegram_id, connection=None, cursor=None):
        cursor.execute("""SELECT * FROM user_tariffs 
                                       INNER JOIN tariffs ON tariff_id = tariffs.id 
                                       WHERE user_id = %s AND (tariffs.duration IS NULL 
                                       OR UNIX_TIMESTAMP(started_at) + tariffs.duration >= UNIX_TIMESTAMP(now()))""",
                       [telegram_id])

        tariffs = cursor.fetchall()

        return tariffs

    @_use_one_time_connection
    def get_user_tariffs(self, telegram_id, connection=None, cursor=None):
        cursor.execute("""SELECT * FROM user_tariffs 
                               INNER JOIN tariffs ON tariff_id = tariffs.id WHERE user_id = %s""",
                       [telegram_id])

        tariffs = cursor.fetchall()

        return tariffs

    @_use_one_time_connection
    def get_user_subscriptions(self, telegram_id, connection=None, cursor=None):
        cursor.execute("""SELECT user_id, CONVERT(`blogger_id`, char), bloggers.short_name, 
                               bloggers.posts_count, CONVERT(bloggers.last_post_id, char) 
                               FROM user_subscriptions 
                               INNER JOIN bloggers ON blogger_id = instagram_id 
                               WHERE user_id = %s""", [telegram_id])

        return cursor.fetchall()

    @_use_one_time_connection
    def unsubscribe_user(self, telegram_id, blogger_id, connection=None, cursor=None):
        cursor.execute("""DELETE
                               FROM user_subscriptions
                               WHERE user_id = %s
                               AND blogger_id = %s""", [telegram_id, f'{blogger_id}'])

        connection.commit()

        if cursor.rowcount > 0:
            return FunctionResult.success()

        return FunctionResult.error("Вы не подписаны на этого пользователя")

    @_use_one_time_connection
    def update_blogger_posts_info(self, posts_count, last_post_id, blogger_id, connection=None, cursor=None):
        cursor.execute("""UPDATE instagram_notify.bloggers
            SET posts_count  = %s,
            last_post_id = %s
            WHERE instagram_id = %s;""", [posts_count, last_post_id, f'{blogger_id}'])

        connection.commit()
        return cursor.rowcount

    @_use_one_time_connection
    def delete_blogger(self, blogger_short_name, connection=None, cursor=None):
        cursor.execute("""DELETE FROM bloggers WHERE short_name = %s""", [blogger_short_name])

        connection.commit()
        return cursor.rowcount

    @_use_one_time_connection
    def update_blogger_stories_info(self, last_story_id, blogger_id, connection=None, cursor=None):
        cursor.execute("""UPDATE instagram_notify.bloggers
            SET last_story_id = %s
            WHERE instagram_id = %s;""", [last_story_id, f'{blogger_id}'])

        connection.commit()
        return cursor.rowcount

    @_use_one_time_connection
    def add_reel_to_blogger(self, blogger_id, album_id, reel_id, connection=None, cursor=None):
        cursor.execute("""INSERT INTO blogger_reels VALUES (%s, %s, %s)""",
                       [f'{blogger_id}', f'{album_id}', f'{reel_id}'])

        connection.commit()

    @_use_one_time_connection
    def update_reel_id_in_album(self, blogger_id, album_id, reel_id, connection=None, cursor=None):
        cursor.execute("""UPDATE blogger_reels
                    SET last_reel_id = %s
                    WHERE album_id = %s AND blogger_id = %s;""", [f'{reel_id}', f'{album_id}', f'{blogger_id}'])

        connection.commit()
        return cursor.rowcount

    @_use_one_time_connection
    def delete_reels_album(self, album_id, connection=None, cursor=None):
        cursor.execute("""DELETE FROM blogger_reels WHERE album_id = %s;""",
                       [f'{album_id}'])

        connection.commit()
        return cursor.rowcount

    @_use_one_time_connection
    def get_blogger_reels(self, blogger_id, connection=None, cursor=None):
        cursor.execute(
            """SELECT CONVERT(`blogger_id`, char), CONVERT(`album_id`, char), CONVERT(`last_reel_id`, char) 
               FROM blogger_reels WHERE blogger_id = %s""",
            [blogger_id])

        raw_reels = cursor.fetchall()
        reels = {}

        for reel in raw_reels:
            reels[int(reel[1])] = int(reel[2])

        return reels
