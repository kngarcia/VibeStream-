FROM python:3.11-slim

ARG SERVICE_NAME
ARG SERVICE_PORT

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de requisitos
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY . .

# Exponer puerto
EXPOSE ${SERVICE_PORT}

# Variables de entorno
ENV SERVICE_NAME=${SERVICE_NAME}
ENV SERVICE_PORT=${SERVICE_PORT}
ENV PYTHONUNBUFFERED=1

# Comando de inicio
CMD uvicorn main:app --host 0.0.0.0 --port ${SERVICE_PORT}
