FROM python:3.12-slim

# System dependencies aur Tesseract OCR install karein
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Requirements copy karke install karein
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Baaki saara code copy karein
COPY . .

# Flask app ko expose karein
EXPOSE 5000

# Gunicorn se app start karein
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
