from pydantic import BaseModel, Field


class CreateProductRequest(BaseModel):
    name: str
    price: float = Field(..., gt=0)
    stock: int = Field(..., ge=0)


class AddItemRequest(BaseModel):
    product_id: int
    quantity: int = Field(..., ge=1)
