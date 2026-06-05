import pytest


# ─────────────────────────────────────────────
# USERS (8)
# ─────────────────────────────────────────────

def test_01_create_user_success(client):
    r = client.post("/users", json={"name": "Alice", "email": "alice@test.com"})
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "Alice"
    assert data["email"] == "alice@test.com"
    assert "id" in data


def test_02_create_user_duplicate_email_rejected(client):
    client.post("/users", json={"name": "Bob", "email": "bob@test.com"})
    r = client.post("/users", json={"name": "Bob2", "email": "bob@test.com"})
    assert r.status_code == 400
    assert "already registered" in r.json()["detail"].lower()


def test_03_create_user_missing_name_rejected(client):
    r = client.post("/users", json={"email": "x@test.com"})
    assert r.status_code == 422


def test_04_create_user_missing_email_rejected(client):
    r = client.post("/users", json={"name": "X"})
    assert r.status_code == 422


def test_05_get_user_success(client):
    r = client.get("/users/1")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == 1
    assert "name" in data
    assert "email" in data


def test_06_get_user_not_found(client):
    r = client.get("/users/999")
    assert r.status_code == 404
    assert "not found" in r.json()["detail"].lower()


def test_07_list_users_returns_all(client):
    client.post("/users", json={"name": "Bob", "email": "bob@test.com"})
    r = client.get("/users")
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_08_list_users_empty():
    # resetDatabase autouse fixture has already cleared the DB for this test,
    # so no user was seeded — use a plain TestClient without the client fixture
    from fastapi.testclient import TestClient
    from main import app
    c = TestClient(app)
    r = c.get("/users")
    assert r.status_code == 200
    assert r.json() == []


# ─────────────────────────────────────────────
# PRODUCTS (10)
# ─────────────────────────────────────────────

def test_09_create_single_product(client):
    r = client.post("/products", json=[{"name": "Shoes", "price": 49.99, "stock": 10}])
    assert r.status_code == 201
    data = r.json()[0]
    assert data["name"] == "Shoes"
    assert data["price"] == 49.99
    assert data["stock"] == 10
    assert "id" in data


def test_10_create_multiple_products_bulk(client):
    r = client.post("/products", json=[
        {"name": "Shoes", "price": 49.99, "stock": 10},
        {"name": "Shirt", "price": 19.99, "stock": 20},
    ])
    assert r.status_code == 201
    assert len(r.json()) == 2


def test_11_create_product_price_zero_rejected(client):
    r = client.post("/products", json=[{"name": "Free", "price": 0, "stock": 5}])
    assert r.status_code == 422


def test_12_create_product_negative_price_rejected(client):
    r = client.post("/products", json=[{"name": "Bad", "price": -10.0, "stock": 5}])
    assert r.status_code == 422


def test_13_create_product_negative_stock_rejected(client):
    r = client.post("/products", json=[{"name": "Bad", "price": 10.0, "stock": -1}])
    assert r.status_code == 422


def test_14_create_product_missing_name_rejected(client):
    r = client.post("/products", json=[{"price": 10.0, "stock": 5}])
    assert r.status_code == 422


def test_15_create_product_missing_price_rejected(client):
    r = client.post("/products", json=[{"name": "Bad", "stock": 5}])
    assert r.status_code == 422


def test_16_list_products_returns_all(client, product):
    r = client.get("/products")
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["name"] == "Shoes"


def test_17_list_products_empty_db(client):
    r = client.get("/products")
    assert r.status_code == 200
    assert r.json() == []


def test_18_create_product_string_price_rejected(client):
    r = client.post("/products", json=[{"name": "Bad", "price": "abc", "stock": 5}])
    assert r.status_code == 422


# ─────────────────────────────────────────────
# CART (10)
# ─────────────────────────────────────────────

def test_19_create_cart_success(client):
    r = client.post("/cart/1")
    assert r.status_code == 201
    data = r.json()
    assert data["user_id"] == 1
    assert data["status"] == "active"
    assert "id" in data


def test_20_create_cart_nonexistent_user_rejected(client):
    r = client.post("/cart/999")
    assert r.status_code == 404
    assert "user not found" in r.json()["detail"].lower()


def test_21_create_duplicate_cart_rejected(client, cart):
    r = client.post("/cart/1")
    assert r.status_code == 400
    assert "already exists" in r.json()["detail"].lower()


def test_22_get_cart_with_items(client, cartWithItem):
    r = client.get("/cart/1")
    assert r.status_code == 200
    data = r.json()
    assert "cart" in data
    assert "items" in data
    assert "total" in data
    assert len(data["items"]) == 1


def test_23_get_cart_after_checkout_shows_checked_out(client, cartWithItem):
    client.post("/cart/1/checkout")
    r = client.get("/cart/1")
    assert r.status_code == 200
    assert r.json()["cart"]["status"] == "checked_out"
    assert r.json()["items"] == []


def test_24_get_cart_not_found(client):
    r = client.get("/cart/1")
    assert r.status_code == 404
    assert "not found" in r.json()["detail"].lower()


def test_25_delete_cart_success(client, cart):
    r = client.delete("/cart/1")
    assert r.status_code == 204


def test_26_delete_cart_not_found(client):
    r = client.delete("/cart/999")
    assert r.status_code == 404


def test_27_cart_status_active_on_creation(client):
    r = client.post("/cart/1")
    assert r.json()["status"] == "active"


def test_28_each_user_has_own_cart(client):
    client.post("/users", json={"name": "User2", "email": "user2@test.com"})
    r1 = client.post("/cart/1")
    r2 = client.post("/cart/2")
    assert r1.status_code == 201
    assert r2.status_code == 201
    assert r1.json()["user_id"] != r2.json()["user_id"]


# ─────────────────────────────────────────────
# ADD ITEM (12)
# ─────────────────────────────────────────────

def test_29_add_item_success(client, product, cart):
    r = client.post("/cart/1/items", json={"product_id": product["id"], "quantity": 2})
    assert r.status_code == 201
    data = r.json()
    assert data["product_id"] == product["id"]
    assert data["quantity"] == 2


def test_30_add_same_product_twice_merges_quantity(client, product, cart):
    client.post("/cart/1/items", json={"product_id": product["id"], "quantity": 2})
    client.post("/cart/1/items", json={"product_id": product["id"], "quantity": 3})
    items = client.get("/cart/1").json()["items"]
    assert len(items) == 1
    assert items[0]["quantity"] == 5


def test_31_add_item_cart_not_found(client, product):
    r = client.post("/cart/1/items", json={"product_id": product["id"], "quantity": 1})
    assert r.status_code == 404
    assert "cart not found" in r.json()["detail"].lower()


def test_32_add_nonexistent_product(client, cart):
    r = client.post("/cart/1/items", json={"product_id": 9999, "quantity": 1})
    assert r.status_code == 404
    assert "product not found" in r.json()["detail"].lower()


def test_33_add_item_to_checked_out_cart_rejected(client, cartWithItem):
    client.post("/cart/1/checkout")
    r = client.post("/cart/1/items", json={"product_id": 1, "quantity": 1})
    assert r.status_code == 400
    assert "checked out" in r.json()["detail"].lower()


def test_34_add_item_exceeds_stock_rejected(client, product, cart):
    r = client.post("/cart/1/items", json={"product_id": product["id"], "quantity": 999})
    assert r.status_code == 400
    assert "units available" in r.json()["detail"].lower()


def test_35_add_item_quantity_zero_rejected(client, product, cart):
    r = client.post("/cart/1/items", json={"product_id": product["id"], "quantity": 0})
    assert r.status_code == 422


def test_36_add_item_negative_quantity_rejected(client, product, cart):
    r = client.post("/cart/1/items", json={"product_id": product["id"], "quantity": -1})
    assert r.status_code == 422


def test_37_add_item_subtotal_calculated_correctly(client, product, cart):
    r = client.post("/cart/1/items", json={"product_id": product["id"], "quantity": 3})
    assert r.status_code == 201
    assert r.json()["subtotal"] == round(product["price"] * 3, 2)


def test_38_merged_quantity_exceeds_stock_rejected(client, product, cart):
    client.post("/cart/1/items", json={"product_id": product["id"], "quantity": 8})
    r = client.post("/cart/1/items", json={"product_id": product["id"], "quantity": 5})
    assert r.status_code == 400
    assert "units available" in r.json()["detail"].lower()


def test_39_add_multiple_different_products(client, cart):
    client.post("/products", json=[
        {"name": "Shirt", "price": 19.99, "stock": 20},
        {"name": "Cap", "price": 9.99, "stock": 15},
    ])
    products = client.get("/products").json()
    client.post("/cart/1/items", json={"product_id": products[0]["id"], "quantity": 1})
    client.post("/cart/1/items", json={"product_id": products[1]["id"], "quantity": 2})
    assert len(client.get("/cart/1").json()["items"]) == 2


def test_40_add_item_missing_product_id_rejected(client, cart):
    r = client.post("/cart/1/items", json={"quantity": 1})
    assert r.status_code == 422


# ─────────────────────────────────────────────
# REMOVE ITEM (6)
# ─────────────────────────────────────────────

def test_41_remove_item_success(client, cartWithItem):
    items = client.get("/cart/1").json()["items"]
    r = client.delete(f"/cart/1/items/{items[0]['id']}")
    assert r.status_code == 204


def test_42_remove_item_cart_not_found(client):
    r = client.delete("/cart/999/items/1")
    assert r.status_code == 404
    assert "cart not found" in r.json()["detail"].lower()


def test_43_remove_nonexistent_item(client, cart):
    r = client.delete("/cart/1/items/9999")
    assert r.status_code == 404
    assert "item not found" in r.json()["detail"].lower()


def test_44_item_count_decreases_after_removal(client, cartWithItem):
    items = client.get("/cart/1").json()["items"]
    client.delete(f"/cart/1/items/{items[0]['id']}")
    assert client.get("/cart/1").json()["items"] == []


def test_45_remove_item_string_item_id_rejected(client, cart):
    r = client.delete("/cart/1/items/abc")
    assert r.status_code == 422


def test_46_remove_one_item_others_remain(client, cart):
    client.post("/products", json=[
        {"name": "Shirt", "price": 19.99, "stock": 20},
        {"name": "Cap", "price": 9.99, "stock": 15},
    ])
    products = client.get("/products").json()
    client.post("/cart/1/items", json={"product_id": products[0]["id"], "quantity": 1})
    client.post("/cart/1/items", json={"product_id": products[1]["id"], "quantity": 1})
    items = client.get("/cart/1").json()["items"]
    client.delete(f"/cart/1/items/{items[0]['id']}")
    assert len(client.get("/cart/1").json()["items"]) == 1


# ─────────────────────────────────────────────
# CHECKOUT (12)
# ─────────────────────────────────────────────

def test_47_checkout_single_item_success(client, cartWithItem):
    r = client.post("/cart/1/checkout")
    assert r.status_code == 200
    data = r.json()
    assert data["message"] == "Checkout successful."
    assert len(data["order"]) == 1


def test_48_checkout_multiple_items_correct_total(client, cart):
    client.post("/products", json=[
        {"name": "Shirt", "price": 20.00, "stock": 10},
        {"name": "Cap", "price": 10.00, "stock": 10},
    ])
    products = client.get("/products").json()
    client.post("/cart/1/items", json={"product_id": products[0]["id"], "quantity": 2})
    client.post("/cart/1/items", json={"product_id": products[1]["id"], "quantity": 1})
    r = client.post("/cart/1/checkout")
    assert r.status_code == 200
    assert r.json()["total"] == 50.0


def test_49_cart_items_empty_after_checkout(client, cartWithItem):
    client.post("/cart/1/checkout")
    assert client.get("/cart/1").json()["items"] == []


def test_50_cart_status_checked_out_after_checkout(client, cartWithItem):
    client.post("/cart/1/checkout")
    assert client.get("/cart/1").json()["cart"]["status"] == "checked_out"


def test_51_product_stock_decremented_after_checkout(client, product, cart):
    client.post("/cart/1/items", json={"product_id": product["id"], "quantity": 3})
    client.post("/cart/1/checkout")
    p = next(p for p in client.get("/products").json() if p["id"] == product["id"])
    assert p["stock"] == 7


def test_52_checkout_cart_not_found(client):
    r = client.post("/cart/999/checkout")
    assert r.status_code == 404
    assert "not found" in r.json()["detail"].lower()


def test_53_checkout_empty_cart_rejected(client, cart):
    r = client.post("/cart/1/checkout")
    assert r.status_code == 400
    assert "empty" in r.json()["detail"].lower()


def test_54_checkout_insufficient_stock_rejected(client):
    # Two users both add the last unit of the same product; first checkout depletes
    # stock so the second checkout hits the race-condition guard in checkout().
    client.post("/products", json=[{"name": "LimitedItem", "price": 5.00, "stock": 1}])
    products = client.get("/products").json()
    limited_id = products[0]["id"]
    client.post("/users", json={"name": "User2", "email": "user2@test.com"})
    client.post("/cart/1")
    client.post("/cart/2")
    client.post("/cart/1/items", json={"product_id": limited_id, "quantity": 1})
    client.post("/cart/2/items", json={"product_id": limited_id, "quantity": 1})
    client.post("/cart/1/checkout")
    r = client.post("/cart/2/checkout")
    assert r.status_code == 400


def test_55_checkout_order_summary_correct(client, cartWithItem, product):
    r = client.post("/cart/1/checkout")
    assert r.status_code == 200
    order = r.json()["order"]
    assert order[0]["product"] == product["name"]
    assert order[0]["quantity"] == 2
    assert order[0]["subtotal"] == round(product["price"] * 2, 2)


def test_56_add_item_after_checkout_blocked(client, cartWithItem, product):
    client.post("/cart/1/checkout")
    r = client.post("/cart/1/items", json={"product_id": product["id"], "quantity": 1})
    assert r.status_code == 400
    assert "checked out" in r.json()["detail"].lower()


def test_57_create_new_cart_after_deleting_checked_out(client, cartWithItem):
    client.post("/cart/1/checkout")
    client.delete("/cart/1")
    r = client.post("/cart/1")
    assert r.status_code == 201
    assert r.json()["status"] == "active"


def test_58_checkout_checked_out_cart_again_rejected(client, cartWithItem):
    client.post("/cart/1/checkout")
    r = client.post("/cart/1/checkout")
    assert r.status_code == 400
    assert "empty" in r.json()["detail"].lower()
