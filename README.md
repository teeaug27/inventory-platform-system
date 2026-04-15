# Inventory Management System with Product Analytics and Search

This project implements the requirements using Flask, MongoDB, Elasticsearch, Docker, and Kubernetes. MongoDB is the system of record for product data, while Elasticsearch is used as the search engine for fast full-text search over product descriptions.

This solution covers the requirements,  CRUD product APIs, full-text search on descriptions, aggregated analytics, Dockerized deployment, Kubernetes manifests for Minikube, sample data, and documentation explaining the structure and run flow. fileciteturn0file0

- MongoDB remains the source of truth and Elasticsearch is treated as a search index.
- Search indexing failures do not block writes to the operational database.
- Readiness and liveness endpoints support Kubernetes health checks.
- MongoDB indexes enforce uniqueness on `product_id` and improve read performance.
- Resource limits and probes are included in Kubernetes manifests.
- The API remains stateless so it can scale horizontally.

## Architecture

- **Flask API**: Handles CRUD, search, and analytics endpoints.
- **MongoDB**: Stores product inventory data.
- **Elasticsearch**: Stores indexed product documents for full-text search.
- **Kubernetes**: Runs the API, MongoDB, Elasticsearch, and one-time initialization jobs.

### Data flow

1. Product create and update requests are written to MongoDB.
2. The same product document is indexed into Elasticsearch.
3. Product delete requests remove the product from MongoDB and Elasticsearch.
4. Analytics are derived from MongoDB aggregation pipelines.
5. Search results are served from Elasticsearch.

## Product schema

```json
{
  "product_id": "SKU-1001",
  "name": "Wireless Headphones",
  "category": "Electronics",
  "price": 129.99,
  "available_quantity": 25,
  "description": "Noise-cancelling wireless headphones with long battery life."
}
```

## API endpoints

### Product inventory CRUD

- `GET /products` - List all products
- `GET /products/<id>` - Fetch a specific product by MongoDB document id
- `POST /products` - Add a new product
- `PUT /products/<id>` - Update an existing product
- `DELETE /products/<id>` - Delete a product

### Search

- `GET /products/search?query=<keywords>` - Full-text search on descriptions, names, and categories

### Analytics

- `GET /products/analytics` - Returns:
  - total product count
  - most popular product category
  - average price
  - per-category breakdown

### Operational endpoints

- `GET /healthz` - Liveness endpoint
- `GET /readyz` - Readiness endpoint that verifies MongoDB and Elasticsearch connectivity


## Project structure

```text
inventory-platform-solution/
├── app/
│   ├── routes/
│   │   └── products.py
│   ├── services/
│   │   └── product_service.py
│   └── utils/
│       ├── config.py
│       └── extensions.py
├── k8s/
├── scripts/
├── tests/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── README.md
└── wsgi.py
```