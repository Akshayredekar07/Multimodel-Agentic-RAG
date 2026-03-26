FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    API_HOST=0.0.0.0 \
    API_PORT=8000 \
    API_BASE_URL=http://127.0.0.1:8000 \
    STREAMLIT_SERVER_PORT=8501

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    libglib2.0-0 \
    libgl1 \
    libmagic1 \
    tesseract-ocr \
    tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

RUN mkdir -p uploaded_files/extracted_text uploaded_files/chunks data
RUN chmod +x docker-entrypoint.sh

EXPOSE 8000 8501

CMD ["./docker-entrypoint.sh"]
