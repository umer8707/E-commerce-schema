import os

from fastapi import FastAPI
from pymongo import MongoClient

from repository import MongoCartRepository, MongoProductRepository
from router import createRouter
from service import CartService, ProductService

app = FastAPI()

client = MongoClient(os.getenv("MONGODB_URL", "mongodb://localhost:27017"))
db = client["cart_db"]

productRepo = MongoProductRepository(db)
cartRepo = MongoCartRepository(db)

productService = ProductService(productRepo)
cartService = CartService(cartRepo, productRepo, client)

app.include_router(createRouter(productService, cartService))
