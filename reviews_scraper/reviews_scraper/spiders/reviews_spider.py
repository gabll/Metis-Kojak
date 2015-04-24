import re
import time
import scrapy

from reviews_scraper.items import *
from reviews_scraper.spiders.crawlerhelper import *
import reviews_scraper.credentials

# Global parameters
PAGINATION = credentials.sp
LAST_PAGE = credentials.lp
AREA = credentials.area

class ReviewsScraper(scrapy.Spider):
    name = "reviews_spider"
    allowed_domains = credentials.allowed_domains
    base_url = credentials.base_url
    start_urls = [base_url + "/RestaurantSearch-geo=%i-oa%i" % (AREA, i) for i in range(0,LAST_PAGE + 1,30)]

    def parse(self, response):
        """parse search page with the list of restaurants"""
        restaurants_list = []
        xps = response.xpath("//div[@id=\"EATERY_SEARCH_RESULTS\"]/div[starts-with(@class, \"listing\")]")
        for xp in xps:
            restaurant = RestaurantItem()
            restaurant['url'] = self.base_url + clean_parsed_string(get_parsed_string(xp, 'div[@class="quality easyClear"]/span/a[@class="property_title "]/@href'))
            restaurant['name'] = clean_parsed_string(get_parsed_string(xp, 'div[@class="quality easyClear"]/span/a[@class="property_title "]/text()'))
            restaurant_item_avg_stars = clean_parsed_string(get_parsed_string(xp, 'div[@class="wrap"]/div[@class="entry wrap"]/div[@class="description"]/div[@class="wrap"]/div[@class="rs rating"]/span[starts-with(@class, "rate")]/img[@class="sprite-ratings"]/@alt'))
            if isinstance(restaurant_item_avg_stars, basestring):
                restaurant['avg_stars'] = re.match(r'(\S+)', restaurant_item_avg_stars).group()
            else:
                restaurant['avg_stars'] = None
            restaurant['geo'] = AREA
            price = clean_parsed_string(get_parsed_string(xp, 'div[@class="wrap"]/div[@class="entry wrap"]/div[@class="description"]/div[@class="information price"]/span[@class="price_range"]/span/text()'))
            if isinstance(price, basestring):
                restaurant['price'] = price
            else:
                restaurant['price'] = None
            yield scrapy.http.Request(url=restaurant['url'],
                            meta={'restaurant': restaurant},
                            callback=self.parse_restaurant_page)

    def parse_restaurant_page(self, response):
        """from restaurant page go to reviews pages"""
        restaurant = response.meta['restaurant']
        restaurant['street'] = clean_parsed_string(get_parsed_string(response, '//span[@class="street-address"]/text()'))
        restaurant['zipcode'] = clean_parsed_string(get_parsed_string(response, '//span[@property="v:postal-code"]/text()'))
        restaurant['city'] = clean_parsed_string(get_parsed_string(response, '//span[@property="v:municipality"]/text()'))
        restaurant['neighb'] = clean_parsed_string(get_parsed_string(response, '//span[@property="v:locality"]/text()'))
        restaurant['country'] = clean_parsed_string(get_parsed_string(response, '//span[@class="country-name"]/text()'))
        restaurant['reviews'] = []
        more_review_url = None
        revid = clean_parsed_string(get_parsed_string(response, '//div[contains(@class, "basic_review")]//span[contains(@class, "taLnk")]/@onclick'))
        if isinstance(revid, basestring):
            revid = re.findall("event, this, (\d+)\)", revid)[0]
            more_review_url = restaurant['url'].replace("Restaurant_Review", "ShowUserReviews").replace("-Reviews", "-r%s" % revid)
        if more_review_url:
            restaurant['more'] = more_review_url
            yield scrapy.http.Request(url=more_review_url,
                            meta={'restaurant': restaurant,
                                  'splash': {'endpoint': 'render.html', 'args': {'wait': 1}}
                                  },
                            callback=self.parse_reviews)
        else:
            print 'Review_more_link not found!'
            print restaurant['name']
            yield restaurant

    def parse_reviews(self, response):
        """parse reviews pages"""
        restaurant = response.meta['restaurant']
        xps = response.xpath('//div[@id="REVIEWS"]/div/div[contains(@class, "review")]')

        for xp in xps:
            xp11 = xp.xpath('div[@class="col1of2"]')
            xp22 = xp.xpath('div[@class="col2of2"]/div[@class="innerBubble"]')
            review_item = ReviewItem()
            user = UserItem()
            ask_user = clean_parsed_string(get_parsed_string(xp, '//div[@class="askQuestion"]//span/@onclick'))
            if isinstance(ask_user, basestring):
                re1='.*?'
                re2='\\\'.*?\\\''
                re3='.*?'
                re4='\\\'.*?\\\''
                re5='.*?'
                re6='\\\'.*?\\\''
                re7='.*?'
                re8='\\\'.*?\\\''
                re9='.*?'
                re10='(\\\'.*?\\\')'
                m = re.findall(re1+re2+re3+re4+re5+re6+re7+re8+re9+re10, ask_user)
                if m:
                    user['username'] = m[0].replace('\'','')
                else:
                    user['username'] = None
            else:
                user['username'] = None
            user['location'] = clean_parsed_string(get_parsed_string(xp11, 'div[@class="member_info"]/div[@class="location"]/text()'))
            total_rev = clean_parsed_string(get_parsed_string(xp11, 'div[@class="memberBadging"]/div[@class="totalReviewBadge badge no_cpu"]/div[@class="contributionReviewBadge"]/span/text()'))
            if isinstance(total_rev, basestring):
                user['total_reviews'] = re.match('[0-9]+', total_rev).group()
            else:
                user['total_reviews'] = None
            total_thanks = clean_parsed_string(get_parsed_string(xp11, 'div[@class="memberBadging"]/div[@class="helpfulVotesBadge badge no_cpu"]/span[@class="badgeText"]/text()'))
            if isinstance(total_thanks, basestring):
                user['total_thanks'] = re.match('[0-9]+', total_thanks).group()
            else:
                user['total_thanks'] = None

            review_item['user'] = user
            review_item['title'] = clean_parsed_string(get_parsed_string(xp22, 'div[@class="quote"]/text()'))
            review_item['description'] = get_parsed_string_multiple(xp22, 'div[@class="entry"]/p/text()')
            xp_item_stars = clean_parsed_string(get_parsed_string(xp22, 'div[@class="rating reviewItemInline"]/span[starts-with(@class, "rate")]/img/@alt'))
            if isinstance(xp_item_stars, basestring):
                review_item['stars'] = re.match(r'(\S+)', xp_item_stars).group()
            else:
                review_item['stars'] = None
            xp_item_date = clean_parsed_string(get_parsed_string(xp22, 'div[@class="rating reviewItemInline"]/span[@class="ratingDate"]/text()'))
            if isinstance(xp_item_date, basestring):
                xp_item_date = re.sub(r'Reviewed ', '', xp_item_date, flags=re.IGNORECASE)
                xp_item_date = time.strptime(xp_item_date, '%B %d, %Y') if xp_item_date else None
                review_item['date'] = time.strftime('%Y-%m-%d', xp_item_date) if xp_item_date else None
            else:
                review_item['date'] = None
            thanks = clean_parsed_string(get_parsed_string(xp22, '//span[@class="numHlpIn"]/text()'))
            if isinstance(thanks, basestring):
                review_item['thanks'] = re.match('[1-9]+', thanks).group()
            else:
                review_item['thanks'] = None
            restaurant['reviews'].append(review_item)

        # Request and parse the next page if it exists
        next_page = clean_parsed_string(get_parsed_string(response, '//span[@class="pageNum current"]/following-sibling::a/@href'))
        if next_page and len(next_page)>0:
            yield scrapy.http.Request(url=self.base_url + next_page,
                            meta={'restaurant': restaurant,
                                  'splash': {'endpoint': 'render.html', 'args': {'wait': 1}}
                                  },
                            callback=self.parse_reviews)
        else:
            #try with old layout
            next_page_old = clean_parsed_string(get_parsed_string(response, '//a[contains(@class,"guiArw sprite-pageNext ")]/@href'))
            if next_page_old and len(next_page_old)>0:
                yield scrapy.Request(self.base_url + next_page_old, self.parse_reviews,
                                meta={'restaurant': restaurant,
                                      'splash': {'endpoint': 'render.html', 'args': {'wait': 1}}
                                      })
            else:
                yield restaurant
