from bson.errors import InvalidId
from flask import Blueprint, jsonify, request

from ..services.product_service import ProductService

products_bp = Blueprint('products', __name__)


@products_bp.get('/products')
def list_products():
    return jsonify(ProductService.list_products()), 200


@products_bp.get('/products/<product_id>')
def get_product(product_id):
    try:
        product = ProductService.get_product(product_id)
    except InvalidId:
        return jsonify({'error': 'Invalid product id'}), 400
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    return jsonify(product), 200


@products_bp.post('/products')
def create_product():
    payload = request.get_json(silent=True) or {}
    error = ProductService.validate_payload(payload)
    if error:
        return jsonify({'error': error}), 400
    try:
        created = ProductService.create_product(payload)
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 409
    return jsonify(created), 201


@products_bp.put('/products/<product_id>')
def update_product(product_id):
    payload = request.get_json(silent=True) or {}
    error = ProductService.validate_payload(payload, partial=True)
    if error:
        return jsonify({'error': error}), 400
    try:
        updated = ProductService.update_product(product_id, payload)
    except InvalidId:
        return jsonify({'error': 'Invalid product id'}), 400
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 409
    if not updated:
        return jsonify({'error': 'Product not found'}), 404
    return jsonify(updated), 200


@products_bp.delete('/products/<product_id>')
def delete_product(product_id):
    try:
        deleted = ProductService.delete_product(product_id)
    except InvalidId:
        return jsonify({'error': 'Invalid product id'}), 400
    if not deleted:
        return jsonify({'error': 'Product not found'}), 404
    return jsonify({'message': 'Product deleted'}), 200


@products_bp.get('/products/search')
def search_products():
    query = request.args.get('query', '').strip()
    if not query:
        return jsonify({'error': 'query parameter is required'}), 400
    results = ProductService.search_products(query)
    return jsonify({'query': query, 'count': len(results), 'results': results}), 200


@products_bp.get('/products/analytics')
def analytics():
    return jsonify(ProductService.analytics()), 200
