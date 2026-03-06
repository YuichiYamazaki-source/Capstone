"""
main.py
Product Service — runs on port 8002
"""

from fastapi import FastAPI
from src.shared.logging import setup_logger
from .routes import router

logger = setup_logger("product")

app = FastAPI(title="Product Service", version="1.0.0")


@app.get("/health")
def health():
    return {"status": "ok", "service": "product"}


app.include_router(router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.product.main:app", host="0.0.0.0", port=8002, reload=True)
