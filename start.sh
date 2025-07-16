 #!/bin/bash

# Instalar playwright (solo si no está instalado)
playwright install --with-deps

# Iniciar servidor
uvicorn app.main:app --host 0.0.0.0 --port 10000
