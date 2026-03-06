"""
models.py
Pydantic models for Order Service.
"""

from datetime import datetime
from pydantic import BaseModel


class OrderItem(BaseModel):
    product_id: str
    name: str
    price: float
    quantity: int


class Order(BaseModel):
    order_id: str
    user_id: str
    items: list[OrderItem]
    total: float
    status: str
    payment_status: str
    created_at: datetime
