from datetime import datetime

import mysql.connector


class Database:
    def __init__(self, parameters):
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
    def execute_custom_query(self, command, commit=False):
        print(self.cursor)
        self.cursor.execute(command)
        if commit:
            self.connection.commit()

        return self.cursor.fetchall()

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

    def check_is_user_subscribe_for_blogger(self, telegram_id, blogger_short_name):
        self.cursor.execute("""SELECT * FROM user_subscriptions WHERE user_id = %s AND blogger_id = %s""",
                            [telegram_id, blogger_short_name])

        return self.cursor.fetchone() is not None

    def subscribe_user(self, telegram_id, blogger_short_name):
        if self.check_is_user_subscribe_for_blogger(telegram_id, blogger_short_name):
            return False

        self.cursor.execute("""INSERT INTO user_subscriptions VALUES (%s, %s)""", [telegram_id, blogger_short_name])

        self.connection.commit()

        return True

    # blogger_data - array of blogger id, blogger short name, posts count, last post id
    def add_new_blogger(self, blogger_data):
        if self.search_blogger_in_database(blogger_id=blogger_data[0]) is not None:
            return False

        self.cursor.execute("""INSERT INTO bloggers VALUES (%s, %s, %s, %s)""", blogger_data)

        self.connection.commit()
        return True

    def add_tariff_to_user(self, tariff_id, telegram_id, started_at=datetime.now()):
        self.cursor.execute("""INSERT INTO user_tariffs VALUES (%s, %s, %s)""", [telegram_id, tariff_id, started_at])

        self.connection.commit()

    def get_valid_user_tariffs(self, telegram_id):
        self.cursor.execute("""SELECT * FROM user_tariffs 
                                       INNER JOIN tariffs ON tariff_id = tariffs.id 
                                       WHERE user_id = %s AND (tariffs.duration IS NULL 
                                       OR UNIX_TIMESTAMP(started_at) + tariffs.duration >= UNIX_TIMESTAMP(now()))""",
                            [telegram_id])

        tariffs = self.cursor.fetchall()

        return tariffs

    def get_user_tariffs(self, telegram_id):
        self.cursor.execute("""SELECT * FROM user_tariffs 
                               INNER JOIN tariffs ON tariff_id = tariffs.id WHERE user_id = %s""",
                            [telegram_id])

        tariffs = self.cursor.fetchall()

        return tariffs

    def get_user_subscriptions(self, telegram_id):
        self.cursor.execute("""SELECT * FROM user_subscriptions WHERE user_id = %s""", [telegram_id])

        return self.cursor.fetchall()
