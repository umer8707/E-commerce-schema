import math

from pydantic import BaseModel, Field, field_validator


class CreateUserRequest(BaseModel):
    name: str = Field(..., max_length=255)
    email: str = Field(..., max_length=255)


class CreateProductRequest(BaseModel):
    name: str = Field(..., max_length=255)
    price: float = Field(..., gt=0, le=999_999.99)
    stock: int = Field(..., ge=0, le=1_000_000)

    @field_validator("price")
    @classmethod
    def price_must_be_finite(cls, v):
        if not math.isfinite(v):
            raise ValueError("price must be a finite number")
        return v


class AddItemRequest(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., ge=1, le=10_000)
