# Usa slim para menos peso; hoy suele ser Debian 13 (trixie)
FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1

WORKDIR /app

# Paquetes mínimos para que apt funcione bien si --with-deps los usa
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl git && \
    rm -rf /var/lib/apt/lists/*

# Instalar deps Python (aprovecha caché: copiá solo requirements primero)
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt && \
    # Fuerza/asegura versión de Playwright con soporte para trixie
    pip install --no-cache-dir --upgrade "playwright>=1.54.0"

# Instalar navegadores + dependencias del sistema correctas para tu OS
RUN python -m playwright install --with-deps

# Copiá el resto del código
COPY . /app

# Arranque (elegí UNA sola forma; no dupliques CMD)
# Si tu start.sh ya hace el uvicorn, usá esto:
RUN chmod +x start.sh
CMD ["./start.sh"]

# O si preferís invocar uvicorn directo, usá esto y BORRÁ la línea de arriba:
# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

EXPOSE 8000
