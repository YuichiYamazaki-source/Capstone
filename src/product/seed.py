"""
seed.py
Inserts sample fashion products and a demo user into MongoDB.
Idempotent — safe to run multiple times (skips existing records).

Usage (inside Docker container):
    python -m src.product.seed
"""

from passlib.context import CryptContext

from src.shared.database import get_db
from src.shared.logging import setup_logger

logger = setup_logger("seed")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

PRODUCTS = [
    {
        "product_id": "p-001",
        "name": "Classic White Linen Shirt",
        "description": "A breathable, lightweight white linen shirt perfect for casual and smart-casual occasions.",
        "category": "tops",
        "price": 4800.0,
        "available_stock": 50,
        "image_url": "/static/images/white-linen-shirt.jpg",
    },
    {
        "product_id": "p-002",
        "name": "Slim-Fit Chino Pants",
        "description": "Versatile slim-fit chino pants in beige. Great for both office and outdoor settings.",
        "category": "bottoms",
        "price": 6500.0,
        "available_stock": 35,
        "image_url": "/static/images/chino-pants.jpg",
    },
    {
        "product_id": "p-003",
        "name": "Floral Summer Dress",
        "description": "A light floral-print dress ideal for summer outings, garden parties, and temple visits.",
        "category": "dresses",
        "price": 7200.0,
        "available_stock": 20,
        "image_url": "/static/images/floral-dress.jpg",
    },
    {
        "product_id": "p-004",
        "name": "Navy Blazer",
        "description": "A structured navy blazer that elevates any outfit. Suitable for formal and business occasions.",
        "category": "outerwear",
        "price": 14800.0,
        "available_stock": 15,
        "image_url": "/static/images/navy-blazer.jpg",
    },
    {
        "product_id": "p-005",
        "name": "Casual Denim Jacket",
        "description": "A classic denim jacket for layering in spring and autumn. Pairs well with dresses and jeans.",
        "category": "outerwear",
        "price": 8900.0,
        "available_stock": 25,
        "image_url": "/static/images/denim-jacket.jpg",
    },
    {
        "product_id": "p-006",
        "name": "Pleated Midi Skirt",
        "description": "An elegant pleated midi skirt in soft blush pink. Perfect for semi-formal events.",
        "category": "bottoms",
        "price": 5600.0,
        "available_stock": 30,
        "image_url": "/static/images/pleated-skirt.jpg",
    },
    {
        "product_id": "p-007",
        "name": "Striped Cotton T-Shirt",
        "description": "A Breton-striped cotton t-shirt for everyday casual wear. Lightweight and comfortable.",
        "category": "tops",
        "price": 2800.0,
        "available_stock": 60,
        "image_url": "/static/images/striped-tshirt.jpg",
    },
    {
        "product_id": "p-008",
        "name": "Leather Ankle Boots",
        "description": "Genuine leather ankle boots with a low block heel. Stylish and comfortable for all-day wear.",
        "category": "shoes",
        "price": 18500.0,
        "available_stock": 12,
        "image_url": "/static/images/ankle-boots.jpg",
    },
    {
        "product_id": "p-009",
        "name": "Knit Turtleneck Sweater",
        "description": "A cozy ribbed turtleneck sweater in cream. Ideal for autumn and winter layering.",
        "category": "tops",
        "price": 6800.0,
        "available_stock": 40,
        "image_url": "/static/images/turtleneck-sweater.jpg",
    },
    {
        "product_id": "p-010",
        "name": "Wide-Leg Linen Trousers",
        "description": "Relaxed wide-leg linen trousers in olive green. Comfortable and stylish for summer.",
        "category": "bottoms",
        "price": 7400.0,
        "available_stock": 22,
        "image_url": "/static/images/wide-leg-trousers.jpg",
    },
]


DEMO_USER = {
    "email": "demo@example.com",
    "name": "Demo User",
    "password": "demo1234",
}


def seed():
    db = get_db()

    # ── Products ──
    collection = db.products
    collection.create_index("product_id", unique=True, background=True)

    inserted = 0
    skipped = 0
    for product in PRODUCTS:
        existing = collection.find_one({"product_id": product["product_id"]})
        if existing:
            skipped += 1
        else:
            collection.insert_one(product)
            inserted += 1

    logger.info("products_seeded inserted=%d skipped=%d", inserted, skipped)

    # ── Demo user ──
    if db.users.find_one({"email": DEMO_USER["email"]}):
        logger.info("demo_user_exists email=%s", DEMO_USER["email"])
    else:
        db.users.insert_one({
            "email": DEMO_USER["email"],
            "name": DEMO_USER["name"],
            "hashed_password": pwd_context.hash(DEMO_USER["password"]),
        })
        logger.info("demo_user_created email=%s", DEMO_USER["email"])


if __name__ == "__main__":
    seed()
