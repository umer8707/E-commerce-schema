from fastapi import HTTPException

from exceptions import DatabaseConnectionException, DatabaseException, DuplicateRecordException
from repository import CartRepository, ProductRepository, UserRepository
from utils import logDbError, logRequest, logWarning


class UserService:
    def __init__(self, repo: UserRepository):
        self._repo = repo

    def create(self, name: str, email: str):
        try:
            user = self._repo.create(name, email)
            logRequest("create_user", {"id": user["id"], "name": name, "email": email})
            return user
        except DuplicateRecordException:
            logWarning("create_user", "email already exists", {"email": email})
            raise HTTPException(400, "Email already registered.")
        except DatabaseConnectionException as e:
            logDbError("create_user", e)
            raise HTTPException(503, "Database unavailable. Try again later.")
        except DatabaseException as e:
            logDbError("create_user", e)
            raise HTTPException(500, "An unexpected database error occurred.")

    def get(self, userId: int):
        try:
            user = self._repo.get(userId)
            if not user:
                logWarning("get_user", "user not found", {"user_id": userId})
                raise HTTPException(404, "User not found.")
            return user
        except HTTPException:
            raise
        except DatabaseConnectionException as e:
            logDbError("get_user", e)
            raise HTTPException(503, "Database unavailable. Try again later.")
        except DatabaseException as e:
            logDbError("get_user", e)
            raise HTTPException(500, "An unexpected database error occurred.")

    def listAll(self):
        try:
            return self._repo.listAll()
        except DatabaseConnectionException as e:
            logDbError("list_users", e)
            raise HTTPException(503, "Database unavailable. Try again later.")
        except DatabaseException as e:
            logDbError("list_users", e)
            raise HTTPException(500, "An unexpected database error occurred.")


class ProductService:
    def __init__(self, repo: ProductRepository):
        self._repo = repo

    def create(self, name, price, stock):
        try:
            product = self._repo.create(name, price, stock)
            logRequest("create_product", {"id": product["id"], "name": name, "price": price, "stock": stock})
            return product
        except DuplicateRecordException:
            raise HTTPException(409, "Product already exists.")
        except DatabaseConnectionException as e:
            logDbError("create_product", e)
            raise HTTPException(503, "Database unavailable. Try again later.")
        except DatabaseException as e:
            logDbError("create_product", e)
            raise HTTPException(500, "An unexpected database error occurred.")

    def listAll(self):
        try:
            return self._repo.listAll()
        except DatabaseConnectionException as e:
            logDbError("list_products", e)
            raise HTTPException(503, "Database unavailable. Try again later.")
        except DatabaseException as e:
            logDbError("list_products", e)
            raise HTTPException(500, "An unexpected database error occurred.")


class CartService:
    def __init__(
        self, cartRepo: CartRepository, productRepo: ProductRepository,
        userRepo: UserRepository, sessionFactory
    ):
        self._cartRepo = cartRepo
        self._productRepo = productRepo
        self._userRepo = userRepo
        self._sessionFactory = sessionFactory

    def create(self, userId):
        try:
            if not self._userRepo.get(userId):
                logWarning("create_cart", "user not found", {"user_id": userId})
                raise HTTPException(404, "User not found.")
            if self._cartRepo.get(userId):
                logWarning("create_cart", "cart already exists", {"user_id": userId})
                raise HTTPException(400, "Cart already exists.")
            cart = self._cartRepo.create(userId)
            logRequest("create_cart", {"cart_id": cart["id"], "user_id": userId})
            return cart
        except HTTPException:
            raise
        except DuplicateRecordException:
            raise HTTPException(409, "Cart already exists.")
        except DatabaseConnectionException as e:
            logDbError("create_cart", e)
            raise HTTPException(503, "Database unavailable. Try again later.")
        except DatabaseException as e:
            logDbError("create_cart", e)
            raise HTTPException(500, "An unexpected database error occurred.")

    def get(self, userId):
        try:
            cart = self._cartRepo.get(userId)
            if not cart:
                logWarning("get_cart", "cart not found", {"user_id": userId})
                raise HTTPException(404, "Cart not found.")
            cartItems = self._cartRepo.getItems(cart["id"])
            total = round(sum(i["price"] * i["quantity"] for i in cartItems), 2)
            return {"cart": cart, "items": cartItems, "total": total}
        except HTTPException:
            raise
        except DatabaseConnectionException as e:
            logDbError("get_cart", e)
            raise HTTPException(503, "Database unavailable. Try again later.")
        except DatabaseException as e:
            logDbError("get_cart", e)
            raise HTTPException(500, "An unexpected database error occurred.")

    def delete(self, userId):
        try:
            if not self._cartRepo.delete(userId):
                logWarning("delete_cart", "cart not found", {"user_id": userId})
                raise HTTPException(404, "Cart not found.")
            logRequest("delete_cart", {"user_id": userId})
        except HTTPException:
            raise
        except DatabaseConnectionException as e:
            logDbError("delete_cart", e)
            raise HTTPException(503, "Database unavailable. Try again later.")
        except DatabaseException as e:
            logDbError("delete_cart", e)
            raise HTTPException(500, "An unexpected database error occurred.")

    def addItem(self, userId, productId, quantity):
        try:
            cart = self._cartRepo.get(userId)
            if not cart:
                logWarning("add_item", "cart not found", {"user_id": userId})
                raise HTTPException(404, "Cart not found.")
            if cart["status"] == "checked_out":
                logWarning("add_item", "cart already checked out", {"user_id": userId, "cart_status": cart["status"]})
                raise HTTPException(400, "Cannot add items to a checked out cart.")

            product = self._productRepo.get(productId)
            if not product:
                logWarning("add_item", "product not found", {"product_id": productId})
                raise HTTPException(404, "Product not found.")

            existing = next((i for i in self._cartRepo.getItems(cart["id"]) if i["product_id"] == productId), None)

            if existing:
                newQty = existing["quantity"] + quantity
                if newQty > product["stock"]:
                    logWarning("add_item", "insufficient stock",
                               {"product_id": productId, "requested": newQty, "available": product["stock"]})
                    raise HTTPException(400, f"Only {product['stock']} units available.")
                item = self._cartRepo.updateItemQuantity(cart["id"], productId, newQty)
            else:
                if quantity > product["stock"]:
                    logWarning("add_item", "insufficient stock",
                               {"product_id": productId, "requested": quantity, "available": product["stock"]})
                    raise HTTPException(400, f"Only {product['stock']} units available.")
                item = self._cartRepo.addItem(cart["id"], {
                    "product_id": productId,
                    "product_name": product["name"],
                    "quantity": quantity,
                    "price": product["price"],
                    "subtotal": round(product["price"] * quantity, 2),
                })

            logRequest("add_item", {
                "item_id": item["id"], "cart_id": cart["id"], "user_id": userId,
                "product_id": productId, "quantity": item["quantity"], "subtotal": item["subtotal"],
            })
            return item
        except HTTPException:
            raise
        except DatabaseConnectionException as e:
            logDbError("add_item", e)
            raise HTTPException(503, "Database unavailable. Try again later.")
        except DatabaseException as e:
            logDbError("add_item", e)
            raise HTTPException(500, "An unexpected database error occurred.")

    def removeItem(self, userId, itemId):
        try:
            cart = self._cartRepo.get(userId)
            if not cart:
                logWarning("remove_item", "cart not found", {"user_id": userId})
                raise HTTPException(404, "Cart not found.")
            if not self._cartRepo.removeItem(cart["id"], itemId):
                logWarning("remove_item", "item not found", {"user_id": userId, "item_id": itemId})
                raise HTTPException(404, "Item not found.")
            logRequest("remove_item", {"user_id": userId, "item_id": itemId})
        except HTTPException:
            raise
        except DatabaseConnectionException as e:
            logDbError("remove_item", e)
            raise HTTPException(503, "Database unavailable. Try again later.")
        except DatabaseException as e:
            logDbError("remove_item", e)
            raise HTTPException(500, "An unexpected database error occurred.")

    def checkout(self, userId):
        try:
            cart = self._cartRepo.get(userId)
            if not cart:
                logWarning("checkout", "cart not found", {"user_id": userId})
                raise HTTPException(404, "Cart not found.")

            cartItems = self._cartRepo.getItems(cart["id"])
            if not cartItems:
                logWarning("checkout", "cart is empty", {"user_id": userId})
                raise HTTPException(400, "Cart is empty.")

            stockErrors = [
                {
                    "product": i["product_name"], "requested": i["quantity"],
                    "available": self._productRepo.get(i["product_id"])["stock"],
                }
                for i in cartItems
                if i["quantity"] > self._productRepo.get(i["product_id"])["stock"]
            ]
            if stockErrors:
                logWarning("checkout", "insufficient stock", {"user_id": userId, "items": stockErrors})
                raise HTTPException(400, {"message": "Insufficient stock.", "items": stockErrors})

            total = 0.0
            order = []
            session = self._sessionFactory()
            try:
                for i in cartItems:
                    self._productRepo.updateStock(i["product_id"], i["quantity"], session=session)
                    subtotal = round(i["price"] * i["quantity"], 2)
                    total += subtotal
                    order.append({"product": i["product_name"], "quantity": i["quantity"], "subtotal": subtotal})
                self._cartRepo.clearItems(cart["id"], session=session)
                self._cartRepo.updateStatus(cart["id"], "checked_out", session=session)
                session.commit()
            except Exception:
                session.rollback()
                raise
            finally:
                session.close()

            logRequest("checkout", {"user_id": userId, "item_count": len(order), "total": round(total, 2)})
            return {"message": "Checkout successful.", "order": order, "total": round(total, 2)}
        except HTTPException:
            raise
        except DatabaseConnectionException as e:
            logDbError("checkout", e)
            raise HTTPException(503, "Database unavailable. Try again later.")
        except DatabaseException as e:
            logDbError("checkout", e)
            raise HTTPException(500, "An unexpected database error occurred.")
