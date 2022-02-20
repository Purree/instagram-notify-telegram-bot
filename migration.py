from Config import Config
from Database import Database

config = Config()

database_parameters = config.get_all_section_parameters("DATABASE")

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

database.execute_custom_query('CREATE TABLE users ('
                              'telegram_id INT UNSIGNED PRIMARY KEY NOT NULL'
                              ')')

database.execute_custom_query('CREATE TABLE bloggers ('
                              'instagram_id INT UNSIGNED PRIMARY KEY NOT NULL,'
                              'name varchar(6) NOT NULL'
                              ')')

database.execute_custom_query('CREATE TABLE user_subscriptions ('
                              'user_id INT UNSIGNED NOT NULL,'
                              'blogger_id INT UNSIGNED NOT NULL,'
                              'FOREIGN KEY (blogger_id)  REFERENCES bloggers (instagram_id)'
                              'ON DELETE CASCADE,'
                              'FOREIGN KEY (user_id)  REFERENCES users (telegram_id)'
                              'ON DELETE CASCADE'
                              ')')

database.execute_custom_query('CREATE TABLE tariffs ('
                              'id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY NOT NULL,'
                              'count INT UNSIGNED,'  # count of bloggers subscriptions, null = infinitive
                              'cost INT UNSIGNED,'  # cost of tariff, null = free
                              'duration INT(14) UNSIGNED'  # null = infinitive
                              ')')

database.execute_custom_query('CREATE TABLE user_tariffs ('
                              'user_id INT UNSIGNED NOT NULL,'
                              'tariff_id INT UNSIGNED NOT NULL,'
                              'started_at TIMESTAMP NOT NULL,'
                              'duration INT(10),'  # null = infinitive
                              'FOREIGN KEY (tariff_id)  REFERENCES tariffs (id),'
                              'FOREIGN KEY (user_id)  REFERENCES users (telegram_id)'
                              'ON DELETE CASCADE'
                              ')')
