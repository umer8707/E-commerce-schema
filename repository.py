from abc import ABC, abstractmethod

from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError

from exceptions import (
    DatabaseConnectionException,
    DatabaseOperationException,
    DuplicateRecordException,
)
from models import Cart, CartItem, Product, User


class ProductRepository(ABC):
    @abstractmethod
    def create(self, name, price, stock): ...

    @abstractmethod
    def get(self, productId): ...

    @abstractmethod
    def listAll(self): ...

    @abstractmethod
    def updateStock(self, productId, quantity, session=None): ...


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
    def clearItems(self, cartId, session=None): ...

    @abstractmethod
    def updateStatus(self, cartId, status, session=None): ...


class UserRepository(ABC):
    @abstractmethod
    def create(self, name: str, email: str): ...

    @abstractmethod
    def get(self, userId: int): ...

    @abstractmethod
    def listAll(self): ...


class SQLUserRepository(UserRepository):
    def __init__(self, sessionFactory):
        self._sessionFactory = sessionFactory

    def _toDict(self, user):
        return {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "created_at": user.created_at,
        }

    def create(self, name: str, email: str):
        session = self._sessionFactory()
        try:
            user = User(name=name, email=email)
            session.add(user)
            session.commit()
            session.refresh(user)
            return self._toDict(user)
        except IntegrityError as e:
            session.rollback()
            raise DuplicateRecordException(str(e))
        except OperationalError as e:
            session.rollback()
            raise DatabaseConnectionException(str(e))
        except SQLAlchemyError as e:
            session.rollback()
            raise DatabaseOperationException(str(e))
        finally:
            session.close()

    def get(self, userId: int):
        session = self._sessionFactory()
        try:
            user = session.query(User).filter(User.id == userId).first()
            return self._toDict(user) if user else None
        except OperationalError as e:
            raise DatabaseConnectionException(str(e))
        except SQLAlchemyError as e:
            raise DatabaseOperationException(str(e))
        finally:
            session.close()

    def listAll(self):
        session = self._sessionFactory()
        try:
            return [self._toDict(u) for u in session.query(User).all()]
        except OperationalError as e:
            raise DatabaseConnectionException(str(e))
        except SQLAlchemyError as e:
            raise DatabaseOperationException(str(e))
        finally:
            session.close()


class SQLProductRepository(ProductRepository):
    def __init__(self, sessionFactory):
        self._sessionFactory = sessionFactory

    def _toDict(self, product):
        return {
            "id": product.id,
            "name": product.name,
            "price": float(product.price),
            "stock": product.stock,
        }

    def create(self, name, price, stock):
        session = self._sessionFactory()
        try:
            product = Product(name=name, price=price, stock=stock)
            session.add(product)
            session.commit()
            session.refresh(product)
            return self._toDict(product)
        except IntegrityError as e:
            session.rollback()
            raise DuplicateRecordException(str(e))
        except OperationalError as e:
            session.rollback()
            raise DatabaseConnectionException(str(e))
        except SQLAlchemyError as e:
            session.rollback()
            raise DatabaseOperationException(str(e))
        finally:
            session.close()

    def get(self, productId):
        session = self._sessionFactory()
        try:
            product = session.query(Product).filter(Product.id == productId).first()
            return self._toDict(product) if product else None
        except OperationalError as e:
            raise DatabaseConnectionException(str(e))
        except SQLAlchemyError as e:
            raise DatabaseOperationException(str(e))
        finally:
            session.close()

    def listAll(self):
        session = self._sessionFactory()
        try:
            products = session.query(Product).all()
            return [self._toDict(p) for p in products]
        except OperationalError as e:
            raise DatabaseConnectionException(str(e))
        except SQLAlchemyError as e:
            raise DatabaseOperationException(str(e))
        finally:
            session.close()

    def updateStock(self, productId, quantity, session=None):
        ownSession = session is None
        s = session or self._sessionFactory()
        try:
            product = s.query(Product).filter(Product.id == productId).first()
            if product:
                product.stock -= quantity
            if ownSession:
                s.commit()
        except OperationalError as e:
            if ownSession:
                s.rollback()
            raise DatabaseConnectionException(str(e))
        except SQLAlchemyError as e:
            if ownSession:
                s.rollback()
            raise DatabaseOperationException(str(e))
        finally:
            if ownSession:
                s.close()


class SQLCartRepository(CartRepository):
    def __init__(self, sessionFactory):
        self._sessionFactory = sessionFactory

    def _cartToDict(self, cart):
        return {
            "id": cart.id,
            "user_id": cart.user_id,
            "status": cart.status,
            "created_at": cart.created_at,
        }

    def _itemToDict(self, item):
        return {
            "id": item.id,
            "cart_id": item.cart_id,
            "product_id": item.product_id,
            "product_name": item.product_name,
            "quantity": item.quantity,
            "price": float(item.price),
            "subtotal": float(item.subtotal),
        }

    def create(self, userId):
        session = self._sessionFactory()
        try:
            cart = Cart(user_id=userId, status="active")
            session.add(cart)
            session.commit()
            session.refresh(cart)
            return self._cartToDict(cart)
        except IntegrityError as e:
            session.rollback()
            raise DuplicateRecordException(str(e))
        except OperationalError as e:
            session.rollback()
            raise DatabaseConnectionException(str(e))
        except SQLAlchemyError as e:
            session.rollback()
            raise DatabaseOperationException(str(e))
        finally:
            session.close()

    def get(self, userId):
        session = self._sessionFactory()
        try:
            cart = session.query(Cart).filter(Cart.user_id == userId).first()
            return self._cartToDict(cart) if cart else None
        except OperationalError as e:
            raise DatabaseConnectionException(str(e))
        except SQLAlchemyError as e:
            raise DatabaseOperationException(str(e))
        finally:
            session.close()

    def delete(self, userId):
        session = self._sessionFactory()
        try:
            cart = session.query(Cart).filter(Cart.user_id == userId).first()
            if not cart:
                return None
            cartDict = self._cartToDict(cart)
            session.delete(cart)
            session.commit()
            return cartDict
        except OperationalError as e:
            session.rollback()
            raise DatabaseConnectionException(str(e))
        except SQLAlchemyError as e:
            session.rollback()
            raise DatabaseOperationException(str(e))
        finally:
            session.close()

    def getItems(self, cartId):
        session = self._sessionFactory()
        try:
            items = session.query(CartItem).filter(CartItem.cart_id == cartId).all()
            return [self._itemToDict(i) for i in items]
        except OperationalError as e:
            raise DatabaseConnectionException(str(e))
        except SQLAlchemyError as e:
            raise DatabaseOperationException(str(e))
        finally:
            session.close()

    def addItem(self, cartId, item):
        session = self._sessionFactory()
        try:
            cartItem = CartItem(
                cart_id=cartId,
                product_id=item["product_id"],
                product_name=item["product_name"],
                quantity=item["quantity"],
                price=item["price"],
                subtotal=item["subtotal"],
            )
            session.add(cartItem)
            session.commit()
            session.refresh(cartItem)
            return self._itemToDict(cartItem)
        except OperationalError as e:
            session.rollback()
            raise DatabaseConnectionException(str(e))
        except SQLAlchemyError as e:
            session.rollback()
            raise DatabaseOperationException(str(e))
        finally:
            session.close()

    def updateItemQuantity(self, cartId, productId, quantity):
        session = self._sessionFactory()
        try:
            item = session.query(CartItem).filter(
                CartItem.cart_id == cartId,
                CartItem.product_id == productId,
            ).first()
            if not item:
                return None
            item.quantity = quantity
            item.subtotal = round(float(item.price) * quantity, 2)
            session.commit()
            session.refresh(item)
            return self._itemToDict(item)
        except OperationalError as e:
            session.rollback()
            raise DatabaseConnectionException(str(e))
        except SQLAlchemyError as e:
            session.rollback()
            raise DatabaseOperationException(str(e))
        finally:
            session.close()

    def removeItem(self, cartId, itemId):
        session = self._sessionFactory()
        try:
            item = session.query(CartItem).filter(
                CartItem.cart_id == cartId,
                CartItem.id == itemId,
            ).first()
            if not item:
                return None
            itemDict = self._itemToDict(item)
            session.delete(item)
            session.commit()
            return itemDict
        except OperationalError as e:
            session.rollback()
            raise DatabaseConnectionException(str(e))
        except SQLAlchemyError as e:
            session.rollback()
            raise DatabaseOperationException(str(e))
        finally:
            session.close()

    def clearItems(self, cartId, session=None):
        ownSession = session is None
        s = session or self._sessionFactory()
        try:
            s.query(CartItem).filter(CartItem.cart_id == cartId).delete()
            if ownSession:
                s.commit()
        except OperationalError as e:
            if ownSession:
                s.rollback()
            raise DatabaseConnectionException(str(e))
        except SQLAlchemyError as e:
            if ownSession:
                s.rollback()
            raise DatabaseOperationException(str(e))
        finally:
            if ownSession:
                s.close()

    def updateStatus(self, cartId, status, session=None):
        ownSession = session is None
        s = session or self._sessionFactory()
        try:
            cart = s.query(Cart).filter(Cart.id == cartId).first()
            if cart:
                cart.status = status
            if ownSession:
                s.commit()
        except OperationalError as e:
            if ownSession:
                s.rollback()
            raise DatabaseConnectionException(str(e))
        except SQLAlchemyError as e:
            if ownSession:
                s.rollback()
            raise DatabaseOperationException(str(e))
        finally:
            if ownSession:
                s.close()
