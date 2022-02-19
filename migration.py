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

