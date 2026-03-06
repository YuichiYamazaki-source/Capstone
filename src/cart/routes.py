"""
routes.py
Cart Service endpoints: GET /cart, POST /cart/items, DELETE /cart/items/{product_id}
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from src.shared.database import get_db
from src.shared.jwt import verify_token
from src.shared.logging import setup_logger
from .models import Cart, CartItemAdd

logger = setup_logger("cart")

router = APIRouter(prefix="/cart", tags=["cart"])


@router.get("/", response_model=Cart)
def get_cart(user_id: Annotated[str, Depends(verify_token)]):
    db = get_db()
    cart = db.carts.find_one({"user_id": user_id}, {"_id": 0})
    return cart or {"user_id": user_id, "items": []}


@router.post("/items", status_code=status.HTTP_201_CREATED)
def add_item(item: CartItemAdd, user_id: Annotated[str, Depends(verify_token)]):
    db = get_db()

    product = db.products.find_one({"product_id": item.product_id}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if product["available_stock"] < item.quantity:
        raise HTTPException(status_code=400, detail="Insufficient stock")

    cart = db.carts.find_one({"user_id": user_id})
    item_in_cart = cart and any(
        i["product_id"] == item.product_id for i in cart.get("items", [])
    )

    if item_in_cart:
        db.carts.update_one(
            {"user_id": user_id, "items.product_id": item.product_id},
            {"$inc": {"items.$.quantity": item.quantity}},
        )
    else:
        db.carts.update_one(
            {"user_id": user_id},
            {
                "$push": {
                    "items": {
                        "product_id": item.product_id,
                        "name": product["name"],
                        "price": product["price"],
                        "quantity": item.quantity,
                    }
                }
            },
            upsert=True,
        )

    logger.info("item_added product_id=%s quantity=%d user=%s", item.product_id, item.quantity, user_id)
    return {"message": "Item added to cart"}


@router.delete("/items/{product_id}")
def remove_item(product_id: str, user_id: Annotated[str, Depends(verify_token)]):
    db = get_db()
    result = db.carts.update_one(
        {"user_id": user_id},
        {"$pull": {"items": {"product_id": product_id}}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Cart not found")
    logger.info("item_removed product_id=%s user=%s", product_id, user_id)
    return {"message": "Item removed from cart"}
