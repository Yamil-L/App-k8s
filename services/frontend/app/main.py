from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
async def root():
    return "<h1>Frontend activo 🚀</h1>"

@app.post("/procesar")
async def procesar_datos(data: dict):
    # Simula envío al backend o IA
    resultado = {"respuesta": f"Tu elección fue: {data.get('eleccion', 'N/A')}"}
    return JSONResponse(resultado)
