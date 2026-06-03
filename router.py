from typing import List

from fastapi import APIRouter

from schemas import AddItemRequest, CreateProductRequest
from service import CartService, ProductService


def createRouter(productService: ProductService, cartService: CartService) -> APIRouter:
    router = APIRouter()

    @router.post("/products", status_code=201)
    def createProduct(payload: List[CreateProductRequest]):
        return [productService.create(p.name, p.price, p.stock) for p in payload]

    @router.get("/products")
    def listProducts():
        return productService.listAll()

    @router.post("/cart/{userId}", status_code=201)
    def createCart(userId: int):
        return cartService.create(userId)

    @router.get("/cart/{userId}")
    def getCart(userId: int):
        return cartService.get(userId)

    @router.delete("/cart/{userId}", status_code=204)
    def deleteCart(userId: int):
        cartService.delete(userId)

    @router.post("/cart/{userId}/items", status_code=201)
    def addItem(userId: int, payload: AddItemRequest):
        return cartService.addItem(userId, payload.product_id, payload.quantity)

    @router.delete("/cart/{userId}/items/{itemId}", status_code=204)
    def removeItem(userId: int, itemId: int):
        cartService.removeItem(userId, itemId)

    @router.post("/cart/{userId}/checkout")
    def checkout(userId: int):
        return cartService.checkout(userId)

    return router
