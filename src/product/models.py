"""
models.py
Pydantic models for Product Service.
"""

from pydantic import BaseModel, Field


class Product(BaseModel):
    product_id: str
    name: str
    description: str
    category: str
    price: float = Field(..., gt=0)
    available_stock: int = Field(..., ge=0)
    image_url: str = ""


class RecommendRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Natural language search query")


class RecommendProduct(BaseModel):
    """A single product returned by the recommend endpoint."""

    product_id: str
    name: str
    category: str
    price: float
    image_url: str = ""
    description: str = ""
    available_stock: int = 0
    similarity_score: float = 0.0


class RecommendResponse(BaseModel):
    """Structured response from POST /products/recommend (spec section 5)."""

    query: str
    model_version: str
    recommendations: str
    products: list[RecommendProduct]


class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    category: str = Field(..., min_length=1)
    price: float = Field(..., gt=0)
    available_stock: int = Field(..., ge=0)
    image_url: str = ""
