from flask_pymongo import PyMongo
from elasticsearch import Elasticsearch

mongo = PyMongo()


def init_elasticsearch(app):
    es = Elasticsearch(app.config['ES_HOST'])
    app.extensions['es'] = es
