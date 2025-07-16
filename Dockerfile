FROM python:3.10

# Establecer directorio de trabajo
WORKDIR /app

# Copiar archivos
COPY . /app/

# Instalar dependencias del sistema necesarias para Playwright
RUN apt-get update && \
    apt-get install -y wget gnupg ca-certificates curl && \
    apt-get clean

# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# Instalar navegadores de Playwright
RUN playwright install --with-deps

# Exponer el puerto
EXPOSE 8000

RUN chmod +x start.sh
CMD ["./start.sh"]

# Comando de inicio
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
