"""
main.py
Cart Service — runs on port 8003
"""

from fastapi import FastAPI
from src.shared.logging import setup_logger
from .routes import router

logger = setup_logger("cart")

app = FastAPI(title="Cart Service", version="1.0.0")


@app.get("/health")
def health():
    return {"status": "ok", "service": "cart"}


app.include_router(router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.cart.main:app", host="0.0.0.0", port=8003, reload=True)
