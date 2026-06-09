import os
import time

from azure.monitor.opentelemetry import configure_azure_monitor

_conn_str = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
if _conn_str:
    configure_azure_monitor(connection_string=_conn_str)

from database import SessionLocal, createTables
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from repository import SQLCartRepository, SQLProductRepository, SQLUserRepository
from router import createRouter
from service import CartService, ProductService, UserService
from sqlalchemy import text
from utils import logger

app = FastAPI()


@app.exception_handler(HTTPException)
async def httpExceptionHandler(request: Request, exc: HTTPException):
    log = logger.error if exc.status_code >= 500 else logger.warning
    log(
        "http_error method=%s path=%s status=%s detail=%s",
        request.method,
        request.url.path,
        exc.status_code,
        exc.detail,
    )
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(RequestValidationError)
async def validationExceptionHandler(request: Request, exc: RequestValidationError):
    logger.warning(
        "validation_error method=%s path=%s errors=%s",
        request.method,
        request.url.path,
        exc.errors(),
    )
    return JSONResponse(status_code=422, content={"detail": exc.errors()})


@app.exception_handler(Exception)
async def globalExceptionHandler(request: Request, exc: Exception):
    logger.error(
        "unhandled_exception method=%s path=%s error=%s message=%s",
        request.method,
        request.url.path,
        type(exc).__name__,
        str(exc),
        exc_info=True,
    )
    return JSONResponse(status_code=500, content={"detail": "An unexpected error occurred."})


@app.middleware("http")
async def logHttpRequests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration_ms = round((time.time() - start) * 1000)
    logger.info(
        "http method=%s path=%s status=%s duration_ms=%s client=%s",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
        request.client.host if request.client else "unknown",
    )
    return response


@app.get("/health")
def health():
    try:
        session = SessionLocal()
        session.execute(text("SELECT 1"))
        session.close()
        logger.info("health_check status=healthy")
        return {"status": "healthy", "database": "connected"}
    except Exception:
        logger.error("health_check status=unhealthy database=unreachable")
        return JSONResponse(status_code=503, content={"status": "unhealthy", "database": "unreachable"})


createTables()

userRepo = SQLUserRepository(SessionLocal)
productRepo = SQLProductRepository(SessionLocal)
cartRepo = SQLCartRepository(SessionLocal)

userService = UserService(userRepo)
productService = ProductService(productRepo)
cartService = CartService(cartRepo, productRepo, userRepo, SessionLocal)

app.include_router(createRouter(productService, cartService, userService))
