"""
main.py
Order Service — runs on port 8004
"""

from fastapi import FastAPI
from src.shared.logging import setup_logger
from .routes import router

logger = setup_logger("order")

app = FastAPI(title="Order Service", version="1.0.0")


@app.get("/health")
def health():
    return {"status": "ok", "service": "order"}


app.include_router(router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.order.main:app", host="0.0.0.0", port=8004, reload=True)
