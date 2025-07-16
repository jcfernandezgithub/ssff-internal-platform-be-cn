from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import uuid
from app.procesar import ejecutar_proceso

app = FastAPI()

os.makedirs("public", exist_ok=True)
app.mount("/static", StaticFiles(directory="public"), name="static")

estado = {
    "status": "esperando",
    "archivo": None,
    "progreso": 0,
    "total": 0,
    "procesados": 0
}

@app.post("/procesar-url")
async def procesar_url(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()
    url = data.get("url")
    if not url:
        return {"error": "Falta URL"}

    archivo_salida = f"{uuid.uuid4().hex}.json"
    archivo_path = os.path.join("public", archivo_salida)
    estado["status"] = "procesando"
    estado["archivo"] = archivo_salida
    estado["progreso"] = 0
    estado["total"] = 0
    estado["procesados"] = 0

    background_tasks.add_task(ejecutar_proceso, url, archivo_path, estado)
    return {"mensaje": "Procesamiento iniciado", "archivo": archivo_salida}

@app.get("/estado")
def obtener_estado():
    return estado

@app.get("/descargar")
def descargar():
    archivo = estado.get("archivo")
    if archivo and os.path.exists(f"public/{archivo}"):
        return FileResponse(f"public/{archivo}", media_type="application/json", filename="resultado.json")
    return {"error": "Archivo no disponible"}
