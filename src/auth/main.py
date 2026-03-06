"""
main.py
Auth Service — runs on port 8001
"""

from fastapi import FastAPI
from src.shared.logging import setup_logger
from .routes import router

logger = setup_logger("auth")

app = FastAPI(title="Auth Service", version="1.0.0")


@app.get("/health")
def health():
    return {"status": "ok", "service": "auth"}


app.include_router(router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.auth.main:app", host="0.0.0.0", port=8001, reload=True)
