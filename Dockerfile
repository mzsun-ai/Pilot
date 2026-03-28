# Web UI + Python stack (openEMS falls back to mock unless you extend this image).
# For full FDTD in production, build openEMS into the image or mount a prebuilt env.
FROM python:3.10-slim-bookworm

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1
EXPOSE 8765

CMD ["uvicorn", "web.app:app", "--host", "0.0.0.0", "--port", "8765"]
