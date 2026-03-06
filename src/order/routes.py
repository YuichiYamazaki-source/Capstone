"""
routes.py
Order Service endpoints: POST /orders
Flow: validate cart stock → mock payment → create order → decrement stock → clear cart
"""

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from src.shared.database import get_db
from src.shared.jwt import verify_token
from src.shared.logging import setup_logger

logger = setup_logger("order")

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_order(user_id: Annotated[str, Depends(verify_token)]):
    db = get_db()

    cart = db.carts.find_one({"user_id": user_id})
    if not cart or not cart.get("items"):
        raise HTTPException(status_code=400, detail="Cart is empty")

    # Validate stock for all items before committing
    for item in cart["items"]:
        product = db.products.find_one({"product_id": item["product_id"]})
        if not product:
            raise HTTPException(status_code=400, detail=f"Product {item['product_id']} not found")
        if product["available_stock"] < item["quantity"]:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock for '{item['name']}'",
            )

    total = sum(item["price"] * item["quantity"] for item in cart["items"])

    # Mock payment — always succeeds
    order_doc = {
        "user_id": user_id,
        "items": cart["items"],
        "total": total,
        "status": "confirmed",
        "payment_status": "paid",
        "created_at": datetime.now(timezone.utc),
    }
    result = db.orders.insert_one(order_doc)

    # Decrement stock
    for item in cart["items"]:
        db.products.update_one(
            {"product_id": item["product_id"]},
            {"$inc": {"available_stock": -item["quantity"]}},
        )

    # Clear cart
    db.carts.delete_one({"user_id": user_id})

    logger.info("order_created order_id=%s total=%.2f items=%d user=%s",
                result.inserted_id, total, len(cart["items"]), user_id)
    return {
        "order_id": str(result.inserted_id),
        "total": total,
        "status": "confirmed",
        "payment_status": "paid",
    }


@router.get("/", status_code=status.HTTP_200_OK)
def list_orders(user_id: Annotated[str, Depends(verify_token)]):
    db = get_db()
    orders = list(db.orders.find({"user_id": user_id}, {"_id": 0}))
    logger.info("list_orders count=%d user=%s", len(orders), user_id)
    return orders
