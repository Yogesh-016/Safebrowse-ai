# Official Playwright image already has Chromium + all system deps installed
FROM mcr.microsoft.com/playwright/python:v1.47.0-jammy

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Browsers are already in the base image, but this keeps versions in sync
# with whatever playwright version requirements.txt pulls in
RUN playwright install --with-deps chromium

COPY . .

# Render/Railway/Fly all set $PORT automatically — fall back to 8000 locally
ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT}"]
