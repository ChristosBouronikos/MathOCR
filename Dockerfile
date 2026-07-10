# MathOCR container by Bouronikos Christos <chrisbouronikos@gmail.com>.
# Support development at https://paypal.me/christosbouronikos.

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MATHOCR_DEVICE=cpu

RUN apt-get update \
    && apt-get install --no-install-recommends -y pandoc libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY backend/requirements*.txt backend/
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r backend/requirements.txt

COPY backend backend
COPY frontend frontend

EXPOSE 8000
CMD ["python", "-m", "uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"]
