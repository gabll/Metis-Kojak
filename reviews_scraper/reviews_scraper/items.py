# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html


from scrapy.item import Item, Field

class RestaurantItem(Item):
    url = Field()
    name = Field()
    avg_stars = Field()
    reviews = Field()
    geo = Field()
    more = Field()
    price = Field()
    street = Field()
    zipcode = Field()
    city = Field()
    neighb = Field()
    country = Field()

class ReviewItem(Item):
    date = Field()
    title = Field()
    description = Field()
    stars = Field()
    user = Field()
    thanks = Field()

class UserItem(Item):
    username = Field()
    location = Field()
    total_reviews = Field()
    total_thanks = Field()
