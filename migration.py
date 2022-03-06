from Config import Config
from Database import Database

config = Config()

database_parameters = config.get_all_section_parameters("DATABASE")

if database_parameters['databasename'] == '':
    raise Exception('Cannot use empty database')

try:
    database_parameters_without_database = database_parameters.copy()
    database_parameters_without_database['databasename'] = ''

    full_access_database = Database(database_parameters_without_database)
    full_access_database.execute_custom_query('CREATE DATABASE IF NOT EXISTS ' + database_parameters['databasename'])
except Exception as e:
    print('Cannot create database:', e)
else:
    del full_access_database, database_parameters_without_database

database = Database(database_parameters)

connection_parameters = database.connect(database_parameters)
connection = connection_parameters["connection"]
cursor = connection_parameters["cursor"]

if database.execute_custom_query(f'SELECT count(*) AS TOTALNUMBEROFTABLES '
                                 f'FROM INFORMATION_SCHEMA.TABLES '
                                 f'WHERE TABLE_SCHEMA = \'{database_parameters["databasename"]}\'',
                                 )[0][0] != 0:
    clear_database = input("In database already exists tables. Delete all tables? (y/n) ")
    if clear_database == 'y':
        database.execute_custom_query('SET FOREIGN_KEY_CHECKS=0;', False, connection, cursor)
        all_tables = database.execute_custom_query(f'SELECT table_schema AS database_name, table_name '
                                                   f'FROM INFORMATION_SCHEMA.TABLES '
                                                   f'WHERE TABLE_SCHEMA = \'{database_parameters["databasename"]}\'',
                                                   False, connection, cursor)

        for table in all_tables:
            database.execute_custom_query('DROP TABLE ' + table[1],
                                          False, connection, cursor)
            print(table[1], 'in', table[0], 'deleted')

        database.execute_custom_query('SET FOREIGN_KEY_CHECKS=1;', False,
                                      connection, cursor)

database.execute_custom_query('CREATE TABLE users ('
                              'telegram_id INT UNSIGNED PRIMARY KEY NOT NULL'
                              ')')

database.execute_custom_query('CREATE TABLE bloggers ('
                              'instagram_id BIGINT UNSIGNED PRIMARY KEY NOT NULL,'
                              'short_name varchar(30) NOT NULL UNIQUE,'  # unique identifier that the user uses 
                              'posts_count int(6) DEFAULT 0 NOT NULL,'
                              'last_post_id BIGINT NOT NULL'
                              ')')

database.execute_custom_query('CREATE TABLE user_subscriptions ('
                              'user_id INT UNSIGNED NOT NULL,'
                              'blogger_id BIGINT UNSIGNED NOT NULL,'
                              'FOREIGN KEY (blogger_id)  REFERENCES bloggers (instagram_id)'
                              'ON DELETE CASCADE,'
                              'FOREIGN KEY (user_id)  REFERENCES users (telegram_id)'
                              'ON DELETE CASCADE'
                              ')')

database.execute_custom_query('CREATE TABLE tariffs ('
                              'id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY NOT NULL,'
                              'count INT UNSIGNED,'  # count of bloggers subscriptions, null = infinitive
                              'cost INT UNSIGNED,'  # cost of tariff, null = free
                              'duration INT(14) UNSIGNED,'  # null = infinitive, value - seconds
                              'name varchar(255) NOT NULL ,'
                              'description text'
                              ')')

database.execute_custom_query('CREATE TABLE user_tariffs ('
                              'user_id INT UNSIGNED NOT NULL,'
                              'tariff_id INT UNSIGNED NOT NULL,'
                              'started_at TIMESTAMP NOT NULL,'
                              'FOREIGN KEY (tariff_id)  REFERENCES tariffs (id),'
                              'FOREIGN KEY (user_id)  REFERENCES users (telegram_id)'
                              'ON DELETE CASCADE'
                              ')')

database.execute_custom_query('INSERT INTO tariffs (count, cost, duration, name) VALUES (5, null, null, "default");',
                              True)
