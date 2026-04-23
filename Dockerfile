FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

# Carpeta de datos persistentes
RUN mkdir -p /data

EXPOSE 8080

CMD ["python", "main.py"]
