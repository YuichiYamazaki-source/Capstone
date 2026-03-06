"""
models.py
Pydantic models for Cart Service.
"""

from pydantic import BaseModel, Field


class CartItemAdd(BaseModel):
    product_id: str
    quantity: int = Field(..., gt=0)


class CartItem(BaseModel):
    product_id: str
    name: str
    price: float
    quantity: int


class Cart(BaseModel):
    user_id: str
    items: list[CartItem] = []
