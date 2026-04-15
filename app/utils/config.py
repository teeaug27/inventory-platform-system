import os


class Config:
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://mongo:27017/inventorydb')
    ES_HOST = os.getenv('ES_HOST', 'http://elasticsearch:9200')
    ES_INDEX = os.getenv('ES_INDEX', 'products')
    JSON_SORT_KEYS = False
