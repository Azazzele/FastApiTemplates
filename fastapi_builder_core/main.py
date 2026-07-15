import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles 
from .models import EndpointModel
from .generator import write_generated_code, get_preview_code
import sys
import os 

app = FastAPI(title="FastAPI Endpoint Builder")

# --- ЖЕЛЕЗОБЕТОННЫЙ РАСЧЕТ ПУТЕЙ СИСТЕМЫ ---
# Находим абсолютный путь к папке, где лежит САМ этот файл main.py
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# Принудительно связываем путь с внутренней папкой templates
TEMPLATES_DIR = os.path.join(CURRENT_DIR, "templates")

# Монтируем статику и шаблоны по абсолютным путям
app.mount("/static", StaticFiles(directory=TEMPLATES_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)
# Хак для совместимости кэша Jinja2 с Python 3.14
templates.env.cache = None 


@app.get("/", response_class=HTMLResponse)
async def root_ui(request: Request):
    return templates.TemplateResponse(
        request,
        name="index.html",
        context={"request": request}
    )

@app.post("/api/preview")
async def preview_endpoint(data: EndpointModel):
    try:
        return get_preview_code(data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate")
async def generate_endpoint(data: EndpointModel):
    try:
        write_generated_code(data)
        return {"status": "success", "message": f"Эндпоинт {data.method} {data.path} успешно добавлен в модуль {data.module}! Файл main.py обновлен."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def start_cli():
    """Функция запуска конструктора через батник с поддержкой путей"""
    # Считываем путь к целевому проекту, переданный из батника
    if len(sys.argv) > 1:
        target_dir = sys.argv[1]
        os.chdir(target_dir)
        
    print("\n" + "="*50)
    print("🚀 FastAPI Эндпоинт Конструктор успешно запущен!")
    print("📁 Код будет генерироваться в: ", os.getcwd())
    print("🔗 Открой в браузере: http://127.0.0.1:8000")
    print("="*50 + "\n")
    uvicorn.run("fastapi_builder_core.main:app", host="127.0.0.1", port=8000, log_level="info")

if __name__ == "__main__":
    start_cli()
