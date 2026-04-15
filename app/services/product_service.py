from typing import Any, Dict, List, Optional

from bson import ObjectId
from flask import current_app
from pymongo import ASCENDING, ReturnDocument
from pymongo.errors import DuplicateKeyError

from ..utils.extensions import mongo


class ProductService:
    @staticmethod
    def _collection():
        return mongo.db.products

    @classmethod
    def ensure_indexes(cls) -> None:
        cls._collection().create_index([('product_id', ASCENDING)], unique=True, name='uq_product_id')
        cls._collection().create_index([('name', ASCENDING)], name='idx_name')
        cls._collection().create_index([('category', ASCENDING)], name='idx_category')

    @staticmethod
    def serialize(product: Dict[str, Any]) -> Dict[str, Any]:
        if not product:
            return {}
        return {
            'id': str(product.get('_id')),
            'product_id': product.get('product_id'),
            'name': product.get('name'),
            'category': product.get('category'),
            'price': float(product.get('price', 0)),
            'available_quantity': int(product.get('available_quantity', 0)),
            'description': product.get('description', ''),
        }

    @staticmethod
    def _is_blank_string(value: Any) -> bool:
        return not isinstance(value, str) or not value.strip()

    @classmethod
    def validate_payload(cls, payload: Dict[str, Any], partial: bool = False) -> Optional[str]:
        required_fields = ['product_id', 'name', 'category', 'price', 'available_quantity', 'description']
        if not partial:
            missing = [f for f in required_fields if f not in payload]
            if missing:
                return f"Missing required fields: {', '.join(missing)}"

        for field in ['product_id', 'name', 'category', 'description']:
            if field in payload and cls._is_blank_string(payload[field]):
                return f'{field} must be a non-empty string'

        if 'price' in payload:
            if not isinstance(payload['price'], (int, float)):
                return 'price must be a number'
            if float(payload['price']) < 0:
                return 'price must be greater than or equal to 0'

        if 'available_quantity' in payload:
            if not isinstance(payload['available_quantity'], int):
                return 'available_quantity must be an integer'
            if payload['available_quantity'] < 0:
                return 'available_quantity must be greater than or equal to 0'

        return None

    @classmethod
    def list_products(cls) -> List[Dict[str, Any]]:
        docs = cls._collection().find().sort('name', ASCENDING)
        return [cls.serialize(d) for d in docs]

    @classmethod
    def get_product(cls, product_id: str) -> Optional[Dict[str, Any]]:
        doc = cls._collection().find_one({'_id': ObjectId(product_id)})
        return cls.serialize(doc) if doc else None

    @classmethod
    def create_product(cls, payload: Dict[str, Any]) -> Dict[str, Any]:
        cls.ensure_indexes()
        try:
            result = cls._collection().insert_one(payload)
        except DuplicateKeyError as exc:
            raise ValueError('product_id must be unique') from exc
        created = cls._collection().find_one({'_id': result.inserted_id})
        cls.index_document(created)
        return cls.serialize(created)

    @classmethod
    def update_product(cls, product_id: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            updated = cls._collection().find_one_and_update(
                {'_id': ObjectId(product_id)},
                {'$set': payload},
                return_document=ReturnDocument.AFTER,
            )
        except DuplicateKeyError as exc:
            raise ValueError('product_id must be unique') from exc
        if updated:
            cls.index_document(updated)
            return cls.serialize(updated)
        return None

    @classmethod
    def delete_product(cls, product_id: str) -> bool:
        doc = cls._collection().find_one({'_id': ObjectId(product_id)})
        if not doc:
            return False
        cls._collection().delete_one({'_id': ObjectId(product_id)})
        cls.delete_document_from_index(product_id)
        return True

    @staticmethod
    def index_document(doc: Dict[str, Any]) -> None:
        es = current_app.extensions['es']
        index_name = current_app.config['ES_INDEX']
        try:
            es.index(
                index=index_name,
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
        except Exception as exc:  # pragma: no cover
            current_app.logger.warning(
                'Elasticsearch indexing failed for product_id=%s: %s',
                doc.get('product_id'),
                exc,
            )

    @staticmethod
    def delete_document_from_index(product_id: str) -> None:
        es = current_app.extensions['es']
        index_name = current_app.config['ES_INDEX']
        try:
            es.delete(index=index_name, id=product_id, ignore=[404], refresh=True)
        except Exception as exc:  # pragma: no cover
            current_app.logger.warning('Elasticsearch delete failed for mongo_id=%s: %s', product_id, exc)

    @staticmethod
    def search_products(query: str) -> List[Dict[str, Any]]:
        es = current_app.extensions['es']
        index_name = current_app.config['ES_INDEX']
        result = es.search(
            index=index_name,
            query={
                'multi_match': {
                    'query': query,
                    'fields': ['description^3', 'name^2', 'category'],
                    'fuzziness': 'AUTO',
                }
            },
        )
        hits = result.get('hits', {}).get('hits', [])
        return [
            {
                'id': hit['_source']['mongo_id'],
                'product_id': hit['_source']['product_id'],
                'name': hit['_source']['name'],
                'category': hit['_source']['category'],
                'description': hit['_source']['description'],
                'price': hit['_source']['price'],
                'available_quantity': hit['_source']['available_quantity'],
                'score': hit.get('_score'),
            }
            for hit in hits
        ]

    @classmethod
    def analytics(cls) -> Dict[str, Any]:
        pipeline = [
            {
                '$group': {
                    '_id': '$category',
                    'count': {'$sum': 1},
                    'average_price': {'$avg': '$price'},
                    'total_quantity': {'$sum': '$available_quantity'},
                }
            },
            {'$sort': {'count': -1, '_id': 1}},
        ]
        category_stats = list(cls._collection().aggregate(pipeline))
        top_category = category_stats[0]['_id'] if category_stats else None
        total_products = cls._collection().count_documents({})
        avg_result = list(cls._collection().aggregate([{'$group': {'_id': None, 'avg': {'$avg': '$price'}}}]))
        average_price = avg_result[0]['avg'] if avg_result else 0
        return {
            'total_products': total_products,
            'most_popular_category': top_category,
            'average_price': round(float(average_price), 2) if average_price else 0,
            'categories': [
                {
                    'category': item['_id'],
                    'product_count': item['count'],
                    'average_price': round(float(item['average_price']), 2),
                    'total_available_quantity': int(item['total_quantity']),
                }
                for item in category_stats
            ],
        }
