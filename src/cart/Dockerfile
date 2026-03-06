FROM python:3.12-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/__init__.py /app/src/__init__.py
COPY src/shared/ /app/src/shared/
COPY src/cart/ /app/src/cart/

ENV PYTHONPATH=/app

EXPOSE 8003

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8003/health')" || exit 1

CMD ["uvicorn", "src.cart.main:app", "--host", "0.0.0.0", "--port", "8003"]
