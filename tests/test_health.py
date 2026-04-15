from app import create_app
from app.services.product_service import ProductService


class TestConfig:
    TESTING = True
    MONGO_URI = 'mongodb://localhost:27017/testdb'
    ES_HOST = 'http://localhost:9200'
    ES_INDEX = 'products'
    JSON_SORT_KEYS = False


def test_healthz():
    app = create_app(TestConfig)
    client = app.test_client()
    response = client.get('/healthz')
    assert response.status_code == 200
    assert response.get_json()['status'] == 'ok'


def test_create_product_validation_error():
    app = create_app(TestConfig)
    client = app.test_client()
    response = client.post('/products', json={'name': 'Keyboard'})
    assert response.status_code == 400
    assert 'Missing required fields' in response.get_json()['error']


def test_create_product_duplicate_conflict(monkeypatch):
    app = create_app(TestConfig)
    client = app.test_client()

    monkeypatch.setattr(ProductService, 'create_product', lambda payload: (_ for _ in ()).throw(ValueError('product_id must be unique')))

    payload = {
        'product_id': 'SKU-1001',
        'name': 'Keyboard',
        'category': 'Electronics',
        'price': 99.99,
        'available_quantity': 10,
        'description': 'Mechanical keyboard',
    }
    response = client.post('/products', json=payload)
    assert response.status_code == 409
    assert response.get_json()['error'] == 'product_id must be unique'


def test_validation_rules():
    assert ProductService.validate_payload({'price': -1}, partial=True) == 'price must be greater than or equal to 0'
    assert ProductService.validate_payload({'available_quantity': -2}, partial=True) == 'available_quantity must be greater than or equal to 0'
    assert ProductService.validate_payload({'description': '   '}, partial=True) == 'description must be a non-empty string'
