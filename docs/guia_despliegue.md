# Guía de despliegue

## Objetivo

Esta guía explica cómo instalar, configurar y ejecutar el proyecto GPU Market Analytics en un entorno local y mediante Docker.

El proyecto puede ejecutarse de dos formas:

1. Ejecución local con Python.
2. Ejecución containerizada con Docker Compose.

## Requisitos previos

Para ejecutar el proyecto se requiere tener instalado:

* Python 3.12 o superior.
* Git.
* Docker Desktop.
* Visual Studio Code, opcional pero recomendado.
* Navegador web.

## 1. Clonar el repositorio

```powershell
git clone https://github.com/Abraham1439/GPU-Market-Analytics.git
cd GPU-Market-Analytics
```

## 2. Configuración local con Python

### Crear entorno virtual

```powershell
python -m venv venv
```

### Activar entorno virtual

En Windows PowerShell:

```powershell
.\venv\Scripts\Activate
```

### Instalar dependencias

```powershell
pip install -r requirements.txt
```

## 3. Configurar variables de entorno

Crear un archivo `.env` en la raíz del proyecto.

Se puede copiar el contenido desde `.env.example`.

```env
GPU_CSV_PATH=data/raw/gpu_specs_v7.csv
DATABASE_DIR=data/database
PROCESSED_DIR=data/processed

INVENTORY_DB_PATH=data/database/inventario_tienda.db
FINAL_DB_PATH=data/database/gpu_market_analytics.db

GPU_INFO_API_URL=https://raw.githubusercontent.com/voidful/gpu-info-api/gpu-data/gpu.json
EXCHANGE_RATE_API_URL=https://mindicador.cl/api/dolar

LOG_LEVEL=INFO
```

## 4. Ejecutar pipeline ETL

El pipeline debe ejecutarse antes de levantar la API o el dashboard, ya que genera la base de datos final.

```powershell
python -m etl.pipeline
```

Archivos generados:

```text
data/database/inventario_tienda.db
data/database/gpu_market_analytics.db
data/processed/gpu_market_analytics.csv
```

## 5. Ejecutar API localmente

```powershell
uvicorn api.main:app --reload --port 8000
```

Acceso a documentación Swagger:

```text
http://127.0.0.1:8000/docs
```

Endpoints de prueba:

```text
http://127.0.0.1:8000/health
http://127.0.0.1:8000/resumen
http://127.0.0.1:8000/marcas
http://127.0.0.1:8000/top-precios
http://127.0.0.1:8000/inventario
```

## 6. Ejecutar dashboard localmente

En otra terminal con el entorno virtual activo:

```powershell
streamlit run dashboards/app.py
```

Acceso al dashboard:

```text
http://localhost:8501
```

## 7. Ejecutar tests

```powershell
pytest -v
```

Resultado esperado:

```text
13 passed
```

## 8. Despliegue con Docker

Docker permite ejecutar la API y el dashboard sin instalar manualmente todas las dependencias en el sistema anfitrión.

### Construir y levantar contenedores

```powershell
docker compose up --build -d
```

### Verificar servicios

```powershell
docker compose ps
```

Resultado esperado:

```text
gpu_market_api          Up      0.0.0.0:8000->8000/tcp
gpu_market_dashboard    Up      0.0.0.0:8501->8501/tcp
```

### Acceder a los servicios

API:

```text
http://localhost:8000/docs
```

Dashboard:

```text
http://localhost:8501
```

### Ver logs

```powershell
docker compose logs
```

Logs solo de API:

```powershell
docker compose logs api
```

Logs solo de dashboard:

```powershell
docker compose logs dashboard
```

### Detener servicios

```powershell
docker compose down
```

## 9. Evidencias recomendadas para la entrega

Se recomienda tomar capturas de:

1. Ejecución del pipeline ETL.
2. Resultado de `pytest -v`.
3. API funcionando en `/docs`.
4. Endpoint `/resumen` respondiendo correctamente.
5. Dashboard abierto en Streamlit.
6. `docker compose ps` mostrando contenedores activos.
7. Historial de Pull Requests en GitHub.
8. Ramas utilizadas en GitHub.

## 10. Problemas comunes

### Error: no existe la base de datos

Solución:

```powershell
python -m etl.pipeline
```

### Error: puerto ocupado

Si el puerto 8000 o 8501 está ocupado, detener procesos anteriores o cambiar el puerto.

### Error: Docker no inicia

Verificar que Docker Desktop esté abierto.

### Error: contenedores se detienen con code 137

Puede deberse a falta de memoria. Se recomienda cerrar aplicaciones pesadas o asignar más memoria a Docker Desktop.

## 11. Comandos principales resumidos

```powershell
git clone https://github.com/Abraham1439/GPU-Market-Analytics.git
cd GPU-Market-Analytics

python -m venv venv
.\venv\Scripts\Activate
pip install -r requirements.txt

python -m etl.pipeline
uvicorn api.main:app --reload --port 8000
streamlit run dashboards/app.py
pytest -v

docker compose up --build -d
docker compose ps
docker compose down
```
