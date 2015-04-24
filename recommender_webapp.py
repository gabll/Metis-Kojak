import flask
import numpy as np
import credentials
import json
from RecommendData import RecommendData
from RecommendUser import RecommendUser
from MySQLconnection import MySQLconnection
import logging
import cPickle


#---------- MODEL IN MEMORY ----------#
rd = RecommendData(min_user_reviews=5, min_rest_reviews=5, geo_list=[1])
rd.fit()
ru = RecommendUser(rd, k=7, alpha=0.45, beta=10, pseudo_rating=3.0)
geo_dict = {1:'New York City', 2:'City2', 3:'City3', 4:'City4'}


#---------- URLS AND WEB PAGES ----------#
app = flask.Flask(__name__)
app.logger.addHandler(logging.StreamHandler())

# Homepage
@app.route("/")
def viz_page():
    """ Homepage: serve the homepage, index.html """
    with open("index.html", 'r') as viz_file:
        return viz_file.read()

# Restaurants-MagicSuggest
@app.route("/rest_list", methods=["POST"])
def rest_list_json():
    """ Rest_list in JSON format for MagicSuggest input """
    ids = rd.rest_id_array
    names = rd.rest_name_array
    avg_stars = rd.rest_avg_stars_array
    total_revs = rd.rest_total_rev_array
    geos = rd.rest_geo_array
    cities = rd.rest_city_array
    rest_list = [{"rest_id": ids[i], "rest_name": names[i],
                  "avg_stars": avg_stars[i], "total_revs": total_revs[i],
                  "geo": geo_dict[int(geos[i])], "city": cities[i]}
                  for i in range(len(ids))]
    return flask.Response(json.dumps(rest_list),  mimetype='application/json')

# Restaurant recommendations
@app.route("/recommend", methods=["POST"])
def recomm_rest_id():
    """ Recommended_rest_ids in JSON format """
    data = flask.request.json
    liking_rest_id_list = data["likings"]
    ru.fit(liking_rest_id_list)
    result = ru.printable_result
    result_sorted = sorted(result, key=lambda tup: tup[1], reverse=True)
    returned_list = [{"rest_name":i[7], "pred_stars":round(i[1],1), "tot_revs":i[4],
                    "user_stars":i[2], "overall_stars":i[5], "city":i[8],
                    "geo":geo_dict[int(i[9])], "rest_id":int(i[0]), "price":i[10]}
                    for i in result_sorted]
    return flask.jsonify(suggestions=returned_list)

# Start the server
app.run(host='0.0.0.0', port=80)
