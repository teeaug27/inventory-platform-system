import logging

from flask import Flask

from .routes.products import products_bp
from .services.product_service import ProductService
from .utils.config import Config
from .utils.extensions import init_elasticsearch, mongo


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    app.logger.setLevel(logging.INFO)

    mongo.init_app(app)
    init_elasticsearch(app)

    with app.app_context():
        try:
            ProductService.ensure_indexes()
        except Exception as exc:  # pragma: no cover
            app.logger.warning('MongoDB index initialization skipped: %s', exc)

    app.register_blueprint(products_bp)

    @app.get('/healthz')
    def healthz():
        return {'status': 'ok'}, 200

    @app.get('/readyz')
    def readyz():
        try:
            mongo.cx.admin.command('ping')
            es = app.extensions['es']
            es.info()
            return {'status': 'ready'}, 200
        except Exception as exc:  # pragma: no cover
            return {'status': 'not_ready', 'error': str(exc)}, 503

    return app
