FROM python:3.11-slim

WORKDIR /app

# Instalar curl para el healthcheck
RUN apt-get update && apt-get install -y curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar y instalar requerimientos
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto de la aplicación
COPY . .

# Exponer el puerto que usará la aplicación
EXPOSE $PORT

# Healthcheck
HEALTHCHECK CMD curl --fail http://localhost:$PORT/_stcore/health

# Comando para ejecutar la aplicación
CMD gunicorn --worker-class uvicorn.workers.UvicornWorker --bind :$PORT app:app 