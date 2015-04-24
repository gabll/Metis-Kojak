import credentials
from MySQLconnection import MySQLconnection
from sklearn.decomposition import IncrementalPCA
import numpy as np

class RecommendData():

    def __init__(self, min_user_reviews=5, min_rest_reviews=5, geo_list=[1]):
        # Model parameters
        self.min_user_reviews = min_user_reviews
        self.min_rest_reviews = min_rest_reviews
        self.geo_list = geo_list
        # Lists for users
        self.user_id_array = None
        self.user_total_thanks_array = None
        self.user_total_rev_array = None
        self.user_geo_array = None
        # List for restaurants
        self.rest_id_array = None
        self.rest_name_array = None
        self.rest_avg_stars_array = None
        self.rest_total_rev_array = None
        self.rest_geo_array = None
        self.rest_city_array = None
        self.rest_price_array = None
        # Reviews matrix
        self.rev_matrix = None
        self.rev_matrix_pca = None
        self.pca_model = None

    def fit(self):
        # Lists for users
        self.user_id_array = self.get_user_id_array(self.min_user_reviews, self.geo_list)
        self.user_total_thanks_array = self.get_user_total_thanks_array(self.user_id_array)
        self.user_total_rev_array = self.get_user_total_rev_array(self.user_id_array)
        # List for restaurants
        self.rest_id_array = self.get_rest_id_array(self.user_id_array, self.min_rest_reviews, self.geo_list)
        self.rest_name_array = self.get_rest_name_array(self.rest_id_array)
        self.rest_avg_stars_array = self.get_rest_avg_stars_array(self.rest_id_array)
        self.rest_total_rev_array = self.get_rest_total_rev_array(self.rest_id_array)
        self.rest_geo_array = self.get_rest_geo_array(self.rest_id_array)
        self.rest_city_array = self.get_rest_city_array(self.rest_id_array)
        self.rest_price_array = self.get_rest_price_array(self.rest_id_array)
        # Reviews matrix
        self.rev_matrix = self.build_rev_matrix(self.user_id_array, self.rest_id_array)
        self.fit_pca(self.rev_matrix)
        # self.get_user_geo_array()

    def _list_to_sql(self, values_list):
        """ Convert a list to a string that can be used in a WHERE clause """
        return '(' + ','.join([str(int(i)) for i in list(values_list)]) + ')'

    def _toint(self, string_value):
        """ Converts to int a string value of a field (e.g. numb. of stars)"""
        try:
            return int(string_value)
        except:
            return 0

    def _tofloat(self, string_value):
        """ Converts to float a string value of a field (e.g. avg_stars)"""
        try:
            return float(string_value)
        except:
            return 0

    def get_user_id_array(self, min_reviews, geo_list):
        """ Return an array of user_id,
        where each user has at least min_reviews reviews """
        relevant_users = np.array([], dtype=np.int16)
        geo_list_sql = self._list_to_sql(geo_list)
        conn = MySQLconnection(credentials.mysql_host,
                               credentials.mysql_user,
                               credentials.mysql_pwd,
                               credentials.mysql_db)
        cursor = conn.execute_query("""
                                       SELECT reviews.user_id
                                       FROM reviews, restaurants
                                       WHERE reviews.rest_id = restaurants.rest_id
                                         AND restaurants.rest_geo IN """ + str(geo_list_sql) + """
                                       GROUP BY reviews.user_id
                                       HAVING count(reviews.user_id)>=""" + str(min_reviews)
                                   )
        for row in cursor.fetchall():
            relevant_users = np.append(relevant_users, [row[0]])
        conn.close()
        return relevant_users

    def get_user_total_thanks_array(self, user_id_array):
        """ Return an array of total thanks value for the user_id list """
        thanks = np.array([], dtype=np.int16)
        user_id_sql = self._list_to_sql(user_id_array)
        conn = MySQLconnection(credentials.mysql_host,
                               credentials.mysql_user,
                               credentials.mysql_pwd,
                               credentials.mysql_db)
        cursor = conn.execute_query("""
                                       SELECT total_thanks
                                       FROM users
                                       WHERE user_id IN """ + str(user_id_sql)
                                   )
        for row in cursor.fetchall():
            thanks = np.append(thanks, [self._toint(row[0])])
        conn.close()
        return thanks

    def get_user_total_rev_array(self, user_id_array):
        """ Return an array of total reviews value for the user_id list """
        total_rev = np.array([], dtype=np.int16)
        user_id_sql = self._list_to_sql(user_id_array)
        conn = MySQLconnection(credentials.mysql_host,
                               credentials.mysql_user,
                               credentials.mysql_pwd,
                               credentials.mysql_db)
        cursor = conn.execute_query("""
                                       SELECT total_reviews
                                       FROM users
                                       WHERE user_id IN """ + str(user_id_sql)
                                   )
        for row in cursor.fetchall():
            total_rev = np.append(total_rev, [self._toint(row[0])])
        conn.close()
        return total_rev

    def get_rest_id_array(self, user_id_array, min_reviews, geo_list):
        """ Return an array of user_id,
        where each user has at least min_reviews reviews """
        relevant_rests = np.array([], dtype=np.int16)
        user_id_sql = self._list_to_sql(user_id_array)
        geo_list_sql = self._list_to_sql(geo_list)
        conn = MySQLconnection(credentials.mysql_host,
                               credentials.mysql_user,
                               credentials.mysql_pwd,
                               credentials.mysql_db)
        cursor = conn.execute_query("""
                                       SELECT DISTINCT reviews.rest_id
                                       FROM reviews, restaurants
                                       WHERE reviews.user_id IN """ + str(user_id_sql) + """
                                         AND reviews.rest_id = restaurants.rest_id
                                         AND restaurants.rest_geo IN """ + str(geo_list_sql) + """
                                       GROUP BY reviews.rest_id
                                       HAVING count(reviews.rest_id)>=""" + str(min_reviews)
                                   )
        for row in cursor.fetchall():
            relevant_rests = np.append(relevant_rests, [row[0]])
        conn.close()
        return relevant_rests

    def get_rest_name_array(self, rest_id_array):
        """ Return list of rest names """
        rest_names = np.array([])
        rest_id_sql = self._list_to_sql(rest_id_array)
        conn = MySQLconnection(credentials.mysql_host,
                               credentials.mysql_user,
                               credentials.mysql_pwd,
                               credentials.mysql_db)
        cursor = conn.execute_query("""
                                       SELECT rest_name
                                       FROM restaurants
                                       WHERE rest_id IN """ + str(rest_id_sql)
                                   )
        for row in cursor.fetchall():
            rest_names = np.append(rest_names, [row[0]])
        conn.close()
        return rest_names

    def get_rest_avg_stars_array(self, rest_id_array):
        """ Return list of avg_stars for rest_id_array """
        rest_avg_stars = np.array([])
        rest_id_sql = self._list_to_sql(rest_id_array)
        conn = MySQLconnection(credentials.mysql_host,
                               credentials.mysql_user,
                               credentials.mysql_pwd,
                               credentials.mysql_db)
        cursor = conn.execute_query("""
                                       SELECT rest_avg_stars
                                       FROM restaurants
                                       WHERE rest_id IN """ + str(rest_id_sql)
                                   )
        for row in cursor.fetchall():
            rest_avg_stars = np.append(rest_avg_stars, [self._tofloat(row[0])])
        conn.close()
        return rest_avg_stars

    def get_rest_total_rev_array(self, rest_id_array):
        """ Return list of total_reviews for rest_id_array """
        rest_total_rev = np.array([])
        rest_id_sql = self._list_to_sql(rest_id_array)
        conn = MySQLconnection(credentials.mysql_host,
                               credentials.mysql_user,
                               credentials.mysql_pwd,
                               credentials.mysql_db)
        cursor = conn.execute_query("""
                                       SELECT count(*)
                                       FROM reviews
                                       WHERE rest_id IN """ + str(rest_id_sql) + """
                                       GROUP BY rest_id
                                   """)
        for row in cursor.fetchall():
            rest_total_rev = np.append(rest_total_rev, [row[0]])
        conn.close()
        return rest_total_rev

    def get_rest_geo_array(self, rest_id_array):
        """ Return list of geo for rest_id_array """
        rest_geo = np.array([])
        rest_id_sql = self._list_to_sql(rest_id_array)
        conn = MySQLconnection(credentials.mysql_host,
                               credentials.mysql_user,
                               credentials.mysql_pwd,
                               credentials.mysql_db)
        cursor = conn.execute_query("""
                                       SELECT rest_geo
                                       FROM restaurants
                                       WHERE rest_id IN """ + str(rest_id_sql)
                                   )
        for row in cursor.fetchall():
            rest_geo = np.append(rest_geo, [row[0]])
        conn.close()
        return rest_geo

    def get_rest_city_array(self, rest_id_array):
        """ Return list of cities for rest_id_array """
        rest_city = np.array([])
        rest_id_sql = self._list_to_sql(rest_id_array)
        conn = MySQLconnection(credentials.mysql_host,
                               credentials.mysql_user,
                               credentials.mysql_pwd,
                               credentials.mysql_db)
        cursor = conn.execute_query("""
                                       SELECT rest_city
                                       FROM restaurants
                                       WHERE rest_id IN """ + str(rest_id_sql)
                                   )
        for row in cursor.fetchall():
            rest_city = np.append(rest_city, [row[0]])
        conn.close()
        return rest_city

    def get_rest_price_array(self, rest_id_array):
        """ Return list of prices for rest_id_array """
        rest_price = np.array([])
        rest_id_sql = self._list_to_sql(rest_id_array)
        conn = MySQLconnection(credentials.mysql_host,
                               credentials.mysql_user,
                               credentials.mysql_pwd,
                               credentials.mysql_db)
        cursor = conn.execute_query("""
                                       SELECT rest_price
                                       FROM restaurants
                                       WHERE rest_id IN """ + str(rest_id_sql)
                                   )
        for row in cursor.fetchall():
            rest_price = np.append(rest_price, [row[0]])
        conn.close()
        return rest_price

    def build_rev_matrix(self, user_id_array, rest_id_array):
        """ Returns a reviews matrix (0=unrated) in a dense format
        and lists of user and restaurant attributes. """
        user_id_sql = self._list_to_sql(user_id_array)
        rest_id_sql = self._list_to_sql(rest_id_array)
        reviews_matrix = np.empty((len(user_id_array),len(rest_id_array),))
        reviews_matrix[:] = 0
        conn = MySQLconnection(credentials.mysql_host,
                               credentials.mysql_user,
                               credentials.mysql_pwd,
                               credentials.mysql_db)
        cursor = conn.execute_query("""
                                       SELECT user_id, rest_id, rev_stars
                                       FROM reviews
                                       WHERE user_id IN """ + user_id_sql + """
                                         AND rest_id IN """ + rest_id_sql + """
                                       ORDER BY user_id ASC
                                    """)
        row_counter = 0
        old_row = -1
        for n, row in enumerate(cursor.fetchall()):
            current_row = row[0]
            if (current_row != old_row) and (n != 0):
                row_counter += 1
            old_row = current_row
            reviews_matrix[row_counter][np.where(rest_id_array==row[1])] = self._toint(row[2])
        conn.close()
        return reviews_matrix

    def fit_pca(self, matrix):
        """Fit pca matrix and save sklearn model """
        reducer = IncrementalPCA(n_components=800, batch_size=2500)
        reduced_matrix = reducer.fit_transform(matrix)
        self.rev_matrix_pca = reduced_matrix
        self.pca_model = reducer

if __name__ == "__main__":
    rec = RecommendData()
    rec.fit()
    print rec.user_total_rev_array
    print rec.user_total_thanks_array
    print rec.rest_id_array
    print rec.rest_avg_stars_array
    print rec.rest_name_array
    print rec.rest_total_rev_array
    print rec.rest_geo_array
    print rec.rest_city_array
    print rec.rest_price_array
    mx = rec.rev_matrix
    print "Matrix dimension:", len(mx), 'rows x', len(mx[0]), 'columns.'
    print 'All tests passed.'
