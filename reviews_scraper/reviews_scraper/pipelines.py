# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html


from twisted.enterprise import adbapi
import datetime
import MySQLdb.cursors
from scrapy import log
from reviews_scraper.items import *
from reviews_scraper.credentials import *


class ReviewsScraperPipeline(object):

    def __init__(self):
        self.dbpool = adbapi.ConnectionPool('MySQLdb', db=mysql_db,
                user=mysql_user, passwd=mysql_pwd, cursorclass=MySQLdb.cursors.DictCursor,
                charset='utf8', use_unicode=True)

    def process_item(self, item, spider):
        query = self.dbpool.runInteraction(self._conditional_insert, item)
        query.addErrback(self.handle_error)
        return item

    def _conditional_insert(self, tx, item):
        rest = (str(item['url']), str(item['name']), str(item['avg_stars']), str(item['geo']), str(item['more']), str(item['price']),
                str(item['street']), str(item['zipcode']), str(item['city']), str(item['neighb']), str(item['country']))
        tx.execute("select rest_id from restaurants where rest_url = %s", item['url'])
        result = tx.fetchone()
        if result:
            log.msg("Rest already stored in db", level=log.DEBUG)
        else:
            tx.execute(\
                "insert into restaurants (rest_url, rest_name, rest_avg_stars, rest_geo, rest_more, rest_price, rest_street, rest_zipcode, rest_city, rest_neighb, rest_country) "
                "values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (rest)
            )
            log.msg("Item stored in db", level=log.DEBUG)

        for rev in item['reviews']:
            user = (str(rev['user']['username']), str(rev['user']['location']), str(rev['user']['total_thanks']), str(rev['user']['total_reviews']))
            tx.execute("select * from users where username = %s and location = %s and total_thanks = %s and total_reviews = %s", user)
            result = tx.fetchone()
            if result:
                log.msg("Item already stored in db", level=log.DEBUG)
            else:
                tx.execute(\
                    "insert into users (username, location, total_thanks, total_reviews) "
                    "values (%s, %s, %s, %s)",
                    (user)
                )
                log.msg("Item stored in db", level=log.DEBUG)
            tx.execute("select user_id from users where username = %s and location = %s and total_thanks = %s and total_reviews = %s", user)
            get_user_id = tx.fetchone()
            tx.execute("select rest_id from restaurants where rest_url = %s", item['url'])
            get_rest_id = tx.fetchone()
            if get_user_id and get_rest_id:
                user_id = get_user_id['user_id']
                rest_id = get_rest_id['rest_id']
                review = (str(user_id), str(rest_id), str(rev['date']), str(rev['title']), 'no_desc', str(rev['stars']), str(rev['thanks']))
                tx.execute("select * from reviews where user_id = %s and rest_id = %s and rev_date = %s and rev_title = %s and rev_stars = %s", (str(user_id), str(rest_id), str(rev['date']), str(rev['title']), str(rev['stars'])))
                result = tx.fetchone()
                if result:
                    log.msg("Review already stored in db", level=log.DEBUG)
                else:
                    print review
                    tx.execute(\
                        'insert into reviews (user_id, rest_id, rev_date, rev_title, rev_desc, rev_stars, rev_thanks) '
                        'values (' + str(user_id) + ',' + str(rest_id) + ',"' + str(rev['date']) + '","notitle", "nodesc", "'+ str(rev['stars']) + '","' + str(rev['thanks']) + '")'
                    )
                    log.msg("Review stored in db", level=log.DEBUG)
            else:
                log.msg("Problem, username missing", level=log.DEBUG)

    def handle_error(self, e):
        log.err(e)
