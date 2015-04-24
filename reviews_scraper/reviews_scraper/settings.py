# -*- coding: utf-8 -*-

# Scrapy settings for reviews_scraper project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#

import reviews_scraper.credentials

BOT_NAME = 'reviews_scraper'

SPIDER_MODULES = ['reviews_scraper.spiders']
NEWSPIDER_MODULE = 'reviews_scraper.spiders'

# Settings for working with Splash Server
SPLASH_URL = credentials.splash_ip
DOWNLOADER_MIDDLEWARES = {
    'scrapyjs.SplashMiddleware': 725,
    'scrapy.contrib.downloadermiddleware.retry.RetryMiddleware': 500,
}
DUPEFILTER_CLASS = 'scrapyjs.SplashAwareDupeFilter'
HTTPCACHE_STORAGE = 'scrapyjs.SplashAwareFSCacheStorage'

# Retry more than 2 times in case splash server restarts
RETRY_TIMES = 35

ITEM_PIPELINES = {
    'reviews_scraper.pipelines.ReviewsScraperPipeline': 500,
}
