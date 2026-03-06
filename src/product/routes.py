"""
routes.py
Product Service endpoints: GET /products, GET /products/{id}, POST /products
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from src.shared.database import get_db
from src.shared.jwt import verify_token
from src.shared.logging import setup_logger
from .agents import recommend
from .models import Product, ProductCreate, RecommendRequest, RecommendResponse

logger = setup_logger("product")

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/", response_model=list[Product])
def list_products(user_id: Annotated[str, Depends(verify_token)]):
    """Return all in-stock products (available_stock > 0)."""
    db = get_db()
    products = list(db.products.find({"available_stock": {"$gt": 0}}, {"_id": 0}))
    logger.info("list_products count=%d user=%s", len(products), user_id)
    return products


@router.get("/{product_id}", response_model=Product)
def get_product(product_id: str, user_id: Annotated[str, Depends(verify_token)]):
    db = get_db()
    product = db.products.find_one({"product_id": product_id}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.post("/recommend", response_model=RecommendResponse)
async def recommend_products(
    body: RecommendRequest,
    user_id: Annotated[str, Depends(verify_token)],
):
    """Semantic product search using multi-agent pipeline.

    Returns structured response per spec section 5:
    query, model_version, top products with image_url + similarity_score.
    """
    logger.info("recommend_request query=%s user=%s", body.query, user_id)
    result = await recommend(body.query)
    return result


@router.post("/", response_model=Product, status_code=status.HTTP_201_CREATED)
def create_product(data: ProductCreate, user_id: Annotated[str, Depends(verify_token)]):
    db = get_db()
    product_id = str(uuid.uuid4())
    doc = {"product_id": product_id, **data.model_dump()}
    db.products.insert_one(doc)
    logger.info("product_created product_id=%s name=%s user=%s", product_id, data.name, user_id)
    return {**doc}
