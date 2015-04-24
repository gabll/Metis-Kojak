import credentials
import pymysql

class MySQLconnection:

    def __init__(self, host, user, pwd, db):
        self.db = pymysql.connect(host=host, user=user, passwd=pwd, db=db)
        self.cursor = self.db.cursor()

    def execute_query(self, query_string):
        """ Execute query and return cursor """
        self.cursor.execute(query_string)
        return self.cursor

    def get_field_value(self, field, table, key_field, key_id):
        """ Return a field from a table given the primary key value """
        self.cursor.execute("""
                               SELECT """ + str(field) + """
                               FROM """ + str(table) + """
                               WHERE """ + str(key_field) + """ = """ + str(key_id) + """
                            """)
        result = self.cursor.fetchall()[0][0]
        return result

    def close(self):
        """ Close active connection """
        self.cursor.close()
        self.db.close()

if __name__ == "__main__":
    conn = MySQLconnection(credentials.mysql_host,
                           credentials.mysql_user,
                           credentials.mysql_pwd,
                           credentials.mysql_db)
    print conn.get_field_value('rest_name', 'restaurants', 'rest_id', 220)
    conn.close()
