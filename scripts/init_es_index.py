import os
from elasticsearch import Elasticsearch

ES_HOST = os.getenv('ES_HOST', 'http://localhost:9200')
ES_INDEX = os.getenv('ES_INDEX', 'products')

MAPPING = {
    'mappings': {
        'properties': {
            'mongo_id': {'type': 'keyword'},
            'product_id': {'type': 'keyword'},
            'name': {'type': 'text'},
            'category': {'type': 'keyword'},
            'description': {'type': 'text'},
            'price': {'type': 'float'},
            'available_quantity': {'type': 'integer'},
        }
    }
}


def main():
    es = Elasticsearch(ES_HOST)
    if es.indices.exists(index=ES_INDEX):
        print(f'Index {ES_INDEX} already exists')
        return
    es.indices.create(index=ES_INDEX, **MAPPING)
    print(f'Created index {ES_INDEX}')


if __name__ == '__main__':
    main()
