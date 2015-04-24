import credentials
import numpy as np
import math
from sklearn.neighbors import NearestNeighbors
from RecommendData import RecommendData
from pprint import pprint

class RecommendUser():

    def __init__(self, rec_data, k=5, alpha=0.45, beta=10, pseudo_rating=3.0):
        # Model parameters
        self.data = rec_data
        self.k = k
        self.alpha = alpha
        self.beta = beta
        self.pseudo_rating = pseudo_rating
        # Recommendations
        self.like_rest_id_list = None
        self.like_rev_vector = None
        self.nearest_users_id_list = None
        self.nearest_users_dist_array = None
        self.nearest_users_common_rest_array = None
        self.unrated_rest_id_list = None
        self.user_weight_array = None
        self.predicted_stars_list = None
        self.printable_result = None
        # Nearest Neighbors model
        self.nn_model = NearestNeighbors(n_neighbors=k,
                                         metric='correlation',
                                         algorithm='brute')
        self.nn_model.fit(self.data.rev_matrix_pca)

    def index_to_id(self, index_list, full_id_list):
        """ Converts list of index (row or column) to list of ids (user_id or rest_id) """
        return [full_id_list[i] for i in index_list]

    def id_to_index(self, id_list, full_id_list):
        """ Converts list of ids (user_id or rest_id) to list of index (row or column) """
        return [full_id_list.index(x) for x in id_list]

    def get_like_rev_vector(self):
        """ Given list of liked restaurant ids, returns vector
        for computing similarity, e.g. [0, 0, 5, 0, ..., 0, 5, 0] """
        rest_list = list(self.data.rest_id_array)
        user_stars = [0 for i in range(len(rest_list))]
        for i in self.like_rest_id_list:
            if i in rest_list:
                user_stars[rest_list.index(i)] = 5
        self.like_rev_vector = user_stars

    def get_nearest_users(self):
        """ Compute nearest neighbors and update nearest users """
        like_pca = self.data.pca_model.transform(self.like_rev_vector)
        kneigh = self.nn_model.kneighbors(like_pca)
        nearest_users_index = kneigh[1][0]
        self.nearest_users_id_list = self.index_to_id(nearest_users_index,
                                                      self.data.user_id_array)
        self.nearest_users_dist_array = kneigh[0][0]

    def get_suggested_rest_list(self):
        """ Create a list of unrated rest_ids basing on
        the reviews of the nearest users """
        like_rest_ix_list = self.id_to_index(self.like_rest_id_list,
                                             list(self.data.rest_id_array))
        nearest_users_ix_list = self.id_to_index(self.nearest_users_id_list,
                                                 list(self.data.user_id_array))
        unrated_rest_id_list = []
        self.nearest_users_common_rest_array = np.array([], dtype=np.int16)
        for user in nearest_users_ix_list:
            common_rest = [i for i in
                list(np.nonzero(np.array(self.data.rev_matrix[user]))[0])
                if i in like_rest_ix_list]
            not_common_rest = [i for i in
                list(np.nonzero(np.array(self.data.rev_matrix[user]))[0])
                if i not in like_rest_ix_list]
            self.nearest_users_common_rest_array =\
                np.append(self.nearest_users_common_rest_array, len(common_rest))
            unrated_rest_id_list.append(not_common_rest)
        unrated_rest_id_list = [item for sublist in unrated_rest_id_list for item in sublist]
        unrated_rest_id_list = list(set(unrated_rest_id_list))
        self.unrated_rest_id_list = self.index_to_id(unrated_rest_id_list,
                                                    list(self.data.rest_id_array))

    def get_user_weight_array(self):
        """ Create an array of weights for the nearest users """
        nearest_users_ix_list = self.id_to_index(self.nearest_users_id_list,
                                                 list(self.data.user_id_array))
        nearest_users_total_reviews_list =\
                        [i for n, i in enumerate(self.data.user_total_rev_array)\
                         if n in nearest_users_ix_list]
        nearest_users_total_thanks_list =\
                        [i for n, i in enumerate(self.data.user_total_thanks_array)\
                         if n in nearest_users_ix_list]
        weights = []
        for n in range(len(nearest_users_ix_list)):
            weight = self.nearest_users_dist_array[n]*\
                math.sqrt(self.nearest_users_common_rest_array[n])*\
                math.log(nearest_users_total_reviews_list[n]+1)*\
                math.log(nearest_users_total_thanks_list[n]+1)
            weight = float(weight)
            weights.append(weight)
        self.user_weight_array = np.array(weights)

    def get_predicted_stars_list(self):
        """ Compute the predicted stars for the unrated restaurants basing
        on the weights array """
        unrated_rest_ix_list = self.id_to_index(self.unrated_rest_id_list,
                                             list(self.data.rest_id_array))
        nearest_users_ix_list = self.id_to_index(self.nearest_users_id_list,
                                                 list(self.data.user_id_array))
        predicted_rest_list = []
        printable_result = []
        user_rated_this_list = []
        for m, rest in enumerate(unrated_rest_ix_list):
            predicted_stars = 0
            norm = 0
            user_rated_this = []
            # posterior: stars given by nearest users
            for n, user in enumerate(nearest_users_ix_list):
                stars = self.data.rev_matrix[user][rest]
                if stars:
                    predicted_stars += stars * self.user_weight_array[n]
                    norm += self.user_weight_array[n]
                    user_rated_this.append(self.nearest_users_id_list[n])
                    mystars = stars #tracking purpose only
                    dist = self.nearest_users_dist_array[n]# tracking purpose only
            user_rated_this_list.append(user_rated_this)
            # add the prior: avg_stars and smoothing with total restaurant reviews
            avg_stars = float(self.data.rest_avg_stars_array[rest])
            total_reviews = float(self.data.rest_total_rev_array[rest])
            predicted_stars += self.alpha*(math.sqrt(total_reviews+self.beta))*\
                                (avg_stars*total_reviews+self.pseudo_rating*self.beta)/\
                                (total_reviews+self.beta)
            norm += self.alpha*(math.sqrt(total_reviews+self.beta))
            predicted_stars = float(predicted_stars) / norm
            predicted_rest_list.append(predicted_stars)
            printable_result.append((rest, predicted_stars, mystars,
                                     user_rated_this, total_reviews, avg_stars, dist,
                                     self.data.rest_name_array[rest],
                                     self.data.rest_city_array[rest],
                                     self.data.rest_geo_array[rest],
                                     self.data.rest_price_array[rest]))
        self.predicted_stars_list = predicted_rest_list
        self.printable_result = printable_result

    def fit(self, like_rest_id_list):
        """ Compute recommendations given a list of liked rest_ids """
        # Store the list of liked rest_ids
        self.like_rest_id_list = like_rest_id_list
        # Update stars vector for the like_list
        self.get_like_rev_vector()
        # Update nearest users
        self.get_nearest_users()
        # Update restaurants suggested
        self.get_suggested_rest_list()
        # Update nearest user "trustability"
        self.get_user_weight_array()
        # Predict stars for restaurants suggested
        self.get_predicted_stars_list()

if __name__ == "__main__":
    rec_d = RecommendData()
    rec_d.fit()
    print 'Matrix fitted'
    rec_u = RecommendUser(rec_d, k=5)
    rec_u.fit([757, 464, 699, 2352, 3486, 1128])
    print 'Nearest user_id:', rec_u.nearest_users_id_list
    print 'Unrated rest_id:', rec_u.unrated_rest_id_list
    print 'User weights', rec_u.user_weight_array
    print 'Commonality', rec_u.nearest_users_common_rest_array
    print 'Result: rest, predicted_stars, user_stars, user_rated_this, total_reviews, avg_stars, dist, name, city, geo, price'
    result = rec_u.printable_result
    sort = sorted(result, key=lambda tup: tup[1], reverse=True)
    for i in sort:
        print i
    print "All tests passed."
