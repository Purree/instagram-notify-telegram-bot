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
