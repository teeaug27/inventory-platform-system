import os
from pymongo import MongoClient
from elasticsearch import Elasticsearch

MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/inventorydb')
ES_HOST = os.getenv('ES_HOST', 'http://localhost:9200')
ES_INDEX = os.getenv('ES_INDEX', 'products')

sample_products = [
    {
        'product_id': 'SKU-1001',
        'name': 'Wireless Headphones',
        'category': 'Electronics',
        'price': 129.99,
        'available_quantity': 25,
        'description': 'Noise-cancelling wireless headphones with long battery life.',
    },
    {
        'product_id': 'SKU-1002',
        'name': 'Ergonomic Office Chair',
        'category': 'Furniture',
        'price': 249.50,
        'available_quantity': 12,
        'description': 'Adjustable office chair with lumbar support and mesh back.',
    },
    {
        'product_id': 'SKU-1003',
        'name': 'Yoga Mat',
        'category': 'Fitness',
        'price': 32.00,
        'available_quantity': 40,
        'description': 'Non-slip yoga mat for home workouts and stretching sessions.',
    },
    {
        'product_id': 'SKU-1004',
        'name': 'Smart Watch',
        'category': 'Electronics',
        'price': 199.99,
        'available_quantity': 15,
        'description': 'Fitness-focused smart watch with heart rate and sleep tracking.',
    },
]


def main():
    mongo_client = MongoClient(MONGO_URI)
    db = mongo_client.get_default_database()
    collection = db.products
    es = Elasticsearch(ES_HOST)

    collection.delete_many({})
    inserted = collection.insert_many(sample_products)
    docs = list(collection.find({'_id': {'$in': inserted.inserted_ids}}))

    for doc in docs:
        es.index(
            index=ES_INDEX,
            id=str(doc['_id']),
            document={
                'mongo_id': str(doc['_id']),
                'product_id': doc['product_id'],
                'name': doc['name'],
                'category': doc['category'],
                'description': doc['description'],
                'price': float(doc['price']),
                'available_quantity': int(doc['available_quantity']),
            },
            refresh=True,
        )

    print(f'Seeded {len(docs)} products')


if __name__ == '__main__':
    main()
