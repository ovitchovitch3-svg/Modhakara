FROM python:3.13-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils \
    tesseract-ocr \
    tesseract-ocr-fra \
    tesseract-ocr-ara \
    libreoffice-impress \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

ENV PORT=10000
EXPOSE 10000

CMD ["python3", "server.py"]