from typing import List

from fastapi import APIRouter, HTTPException

from schemas import AddItemRequest, CreateProductRequest, CreateUserRequest
from service import CartService, ProductService, UserService


def createRouter(
    productService: ProductService,
    cartService: CartService,
    userService: UserService,
) -> APIRouter:
    router = APIRouter()

    # ── Users ─────────────────────────────────────────────────────────────
    @router.post("/users", status_code=201)
    def createUser(payload: CreateUserRequest):
        return userService.create(payload.name, payload.email)

    @router.get("/users")
    def listUsers():
        return userService.listAll()

    @router.get("/users/{userId}")
    def getUser(userId: int):
        return userService.get(userId)

    # ── Products ──────────────────────────────────────────────────────────
    @router.post("/products", status_code=201)
    def createProduct(payload: List[CreateProductRequest]):
        if not payload:
            raise HTTPException(status_code=422, detail="At least one product is required.")
        if len(payload) > 100:
            raise HTTPException(status_code=422, detail="Cannot create more than 100 products per request.")
        return [productService.create(p.name, p.price, p.stock) for p in payload]

    @router.get("/products")
    def listProducts():
        return productService.listAll()

    # ── Cart ──────────────────────────────────────────────────────────────
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
