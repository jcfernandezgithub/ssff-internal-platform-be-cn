from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import uuid
import json
from app.procesar import ejecutar_proceso  # Asegúrate que esta ruta sea correcta

app = FastAPI()

os.makedirs("public", exist_ok=True)
app.mount("/static", StaticFiles(directory="public"), name="static")

@app.post("/procesar-url")
async def procesar_url(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()
    url = data.get("url")
    if not url:
        return {"error": "Falta URL"}

    id = uuid.uuid4().hex
    archivo_salida = f"{id}.json"
    archivo_path = os.path.join("public", archivo_salida)
    estado_path = os.path.join("public", f"estado_{id}.json")

    estado = {
        "status": "procesando",
        "archivo": archivo_salida,
        "progreso": 0,
        "total": 0,
        "procesados": 0
    }

    with open(estado_path, "w") as f:
        json.dump(estado, f)

    def wrapper():
        ejecutar_proceso(url, archivo_path, estado)
        with open(estado_path, "w") as f:
            json.dump(estado, f)

    background_tasks.add_task(wrapper)
    return {"mensaje": "Procesamiento iniciado", "id": id}

@app.get("/estado/{id}")
def obtener_estado(id: str):
    estado_path = os.path.join("public", f"estado_{id}.json")
    if os.path.exists(estado_path):
        with open(estado_path) as f:
            return json.load(f)
    return {"status": "no_encontrado"}

@app.get("/descargar/{id}")
def descargar(id: str):
    archivo_path = os.path.join("public", f"{id}.json")
    if os.path.exists(archivo_path):
        return FileResponse(archivo_path, media_type="application/json", filename="resultado.json")
    return {"error": "Archivo no disponible"}
