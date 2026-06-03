from abc import ABC, abstractmethod
from datetime import datetime, timezone

from pymongo import ReturnDocument
from pymongo.errors import ConnectionFailure, DuplicateKeyError, OperationFailure, PyMongoError

from exceptions import (
    DatabaseConnectionException,
    DatabaseOperationException,
    DuplicateRecordException,
    RecordNotFoundException,
)


class ProductRepository(ABC):
    @abstractmethod
    def create(self, name, price, stock): ...

    @abstractmethod
    def get(self, productId): ...

    @abstractmethod
    def listAll(self): ...

    @abstractmethod
    def updateStock(self, productId, quantity): ...


class CartRepository(ABC):
    @abstractmethod
    def create(self, userId): ...

    @abstractmethod
    def get(self, userId): ...

    @abstractmethod
    def delete(self, userId): ...

    @abstractmethod
    def getItems(self, cartId): ...

    @abstractmethod
    def addItem(self, cartId, item): ...

    @abstractmethod
    def updateItemQuantity(self, cartId, productId, quantity): ...

    @abstractmethod
    def removeItem(self, cartId, itemId): ...

    @abstractmethod
    def clearItems(self, cartId): ...

    @abstractmethod
    def updateStatus(self, cartId, status, session=None): ...


class MongoProductRepository(ProductRepository):
    def __init__(self, db):
        self._col = db["products"]
        self._counters = db["counters"]

    def _nextId(self):
        try:
            return self._counters.find_one_and_update(
                {"_id": "products"},
                {"$inc": {"seq": 1}},
                upsert=True,
                return_document=ReturnDocument.AFTER,
            )["seq"]
        except ConnectionFailure as e:
            raise DatabaseConnectionException(str(e))
        except PyMongoError as e:
            raise DatabaseOperationException(str(e))

    def create(self, name, price, stock):
        try:
            product = {"id": self._nextId(), "name": name, "price": price, "stock": stock}
            self._col.insert_one({**product, "_id": product["id"]})
            return product
        except (DatabaseConnectionException, DatabaseOperationException):
            raise
        except DuplicateKeyError as e:
            raise DuplicateRecordException(str(e))
        except ConnectionFailure as e:
            raise DatabaseConnectionException(str(e))
        except PyMongoError as e:
            raise DatabaseOperationException(str(e))

    def get(self, productId):
        try:
            return self._col.find_one({"_id": productId}, {"_id": 0})
        except ConnectionFailure as e:
            raise DatabaseConnectionException(str(e))
        except PyMongoError as e:
            raise DatabaseOperationException(str(e))

    def listAll(self):
        try:
            return list(self._col.find({}, {"_id": 0}))
        except ConnectionFailure as e:
            raise DatabaseConnectionException(str(e))
        except PyMongoError as e:
            raise DatabaseOperationException(str(e))

    def updateStock(self, productId, quantity, session=None):
        try:
            self._col.update_one({"_id": productId}, {"$inc": {"stock": -quantity}}, session=session)
        except ConnectionFailure as e:
            raise DatabaseConnectionException(str(e))
        except PyMongoError as e:
            raise DatabaseOperationException(str(e))


class MongoCartRepository(CartRepository):
    def __init__(self, db):
        self._col = db["carts"]
        self._counters = db["counters"]

    def _nextId(self, name):
        try:
            return self._counters.find_one_and_update(
                {"_id": name},
                {"$inc": {"seq": 1}},
                upsert=True,
                return_document=ReturnDocument.AFTER,
            )["seq"]
        except ConnectionFailure as e:
            raise DatabaseConnectionException(str(e))
        except PyMongoError as e:
            raise DatabaseOperationException(str(e))

    def create(self, userId):
        try:
            cart = {"id": self._nextId("carts"), "user_id": userId, "created_at": datetime.now(timezone.utc), "status": "active", "items": []}
            self._col.insert_one({**cart, "_id": cart["id"]})
            cart.pop("items")
            return cart
        except (DatabaseConnectionException, DatabaseOperationException):
            raise
        except DuplicateKeyError as e:
            raise DuplicateRecordException(str(e))
        except ConnectionFailure as e:
            raise DatabaseConnectionException(str(e))
        except PyMongoError as e:
            raise DatabaseOperationException(str(e))

    def get(self, userId):
        try:
            return self._col.find_one({"user_id": userId}, {"_id": 0, "items": 0})
        except ConnectionFailure as e:
            raise DatabaseConnectionException(str(e))
        except PyMongoError as e:
            raise DatabaseOperationException(str(e))

    def delete(self, userId):
        try:
            return self._col.find_one_and_delete({"user_id": userId}, {"_id": 0, "items": 0})
        except ConnectionFailure as e:
            raise DatabaseConnectionException(str(e))
        except PyMongoError as e:
            raise DatabaseOperationException(str(e))

    def getItems(self, cartId):
        try:
            doc = self._col.find_one({"_id": cartId}, {"_id": 0, "items": 1})
            return doc["items"] if doc else []
        except ConnectionFailure as e:
            raise DatabaseConnectionException(str(e))
        except PyMongoError as e:
            raise DatabaseOperationException(str(e))

    def addItem(self, cartId, item):
        try:
            item["id"] = self._nextId("items")
            self._col.update_one({"_id": cartId}, {"$push": {"items": item}})
            return item
        except (DatabaseConnectionException, DatabaseOperationException):
            raise
        except ConnectionFailure as e:
            raise DatabaseConnectionException(str(e))
        except PyMongoError as e:
            raise DatabaseOperationException(str(e))

    def updateItemQuantity(self, cartId, productId, quantity):
        try:
            doc = self._col.find_one({"_id": cartId, "items.product_id": productId}, {"_id": 0, "items.$": 1})
            if not doc:
                return None
            item = doc["items"][0]
            newSubtotal = round(item["price"] * quantity, 2)
            self._col.update_one(
                {"_id": cartId, "items.product_id": productId},
                {"$set": {"items.$.quantity": quantity, "items.$.subtotal": newSubtotal}},
            )
            item["quantity"] = quantity
            item["subtotal"] = newSubtotal
            return item
        except ConnectionFailure as e:
            raise DatabaseConnectionException(str(e))
        except PyMongoError as e:
            raise DatabaseOperationException(str(e))

    def removeItem(self, cartId, itemId):
        try:
            doc = self._col.find_one({"_id": cartId}, {"_id": 0, "items": 1})
            item = next((i for i in doc["items"] if i["id"] == itemId), None) if doc else None
            if item:
                self._col.update_one({"_id": cartId}, {"$pull": {"items": {"id": itemId}}})
            return item
        except ConnectionFailure as e:
            raise DatabaseConnectionException(str(e))
        except PyMongoError as e:
            raise DatabaseOperationException(str(e))

    def clearItems(self, cartId, session=None):
        try:
            self._col.update_one({"_id": cartId}, {"$set": {"items": []}}, session=session)
        except ConnectionFailure as e:
            raise DatabaseConnectionException(str(e))
        except PyMongoError as e:
            raise DatabaseOperationException(str(e))

    def updateStatus(self, cartId, status, session=None):
        try:
            self._col.update_one({"_id": cartId}, {"$set": {"status": status}}, session=session)
        except ConnectionFailure as e:
            raise DatabaseConnectionException(str(e))
        except PyMongoError as e:
            raise DatabaseOperationException(str(e))
