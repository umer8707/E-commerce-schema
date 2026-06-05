import os
import sys

os.environ["DATABASE_URL"] = "sqlite:///./test_cart.db"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi.testclient import TestClient

from database import Base, engine
from main import app


@pytest.fixture(autouse=True)
def resetDatabase():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(resetDatabase):
    c = TestClient(app)
    c.post("/users", json={"name": "Test User", "email": "user@test.com"})
    return c


@pytest.fixture
def product(client):
    r = client.post("/products", json=[{"name": "Shoes", "price": 49.99, "stock": 10}])
    return r.json()[0]


@pytest.fixture
def cart(client):
    r = client.post("/cart/1")
    return r.json()


@pytest.fixture
def cartWithItem(client, product, cart):
    r = client.post("/cart/1/items", json={"product_id": product["id"], "quantity": 2})
    return r.json()
