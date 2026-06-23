# GPU Market Analytics

## Descripción del proyecto

GPU Market Analytics es una solución de análisis de datos end-to-end orientada al estudio de tarjetas gráficas. El proyecto integra información técnica, precios, stock simulado de tienda y conversión monetaria USD a CLP para construir una plataforma de análisis que permite observar el comportamiento del inventario, precios por marca, evolución por año y características técnicas de GPUs.

El sistema fue desarrollado como parte de una evaluación de Programación para la Ciencia de Datos, incorporando prácticas profesionales de desarrollo como uso de Git, ramas, Pull Requests, testing automatizado, dashboard interactivo, API REST y despliegue con Docker.

## Objetivo general

Construir una solución integral de análisis de datos que integre múltiples fuentes de información sobre tarjetas gráficas, aplique un pipeline ETL automatizado, almacene datos procesados en SQLite, exponga información mediante una API REST, visualice resultados en un dashboard interactivo y permita ejecutar el proyecto mediante Docker.

## Fuentes de datos utilizadas

El proyecto integra cuatro fuentes de datos:

1. **CSV de Kaggle**

   * Archivo: `data/raw/gpu_specs_v7.csv`
   * Contiene especificaciones técnicas de tarjetas gráficas como marca, modelo, año de lanzamiento, memoria, tipo de memoria, bus, clocks y shaders.

2. **API externa de GPUs**

   * URL: `https://raw.githubusercontent.com/voidful/gpu-info-api/gpu-data/gpu.json`
   * Entrega información complementaria de tarjetas gráficas en formato JSON.

3. **Base de datos SQLite de inventario**

   * Archivo generado: `data/database/inventario_tienda.db`
   * Contiene inventario simulado de una tienda, incluyendo stock, estado, proveedor, SKU y precio de venta en CLP.

4. **API de tipo de cambio**

   * URL: `https://mindicador.cl/api/dolar`
   * Permite obtener el valor del dólar observado para convertir precios desde USD a pesos chilenos.

## Arquitectura general

El flujo general del proyecto es:

```text
CSV Kaggle + API GPU + SQLite Inventario + API Dólar
                         ↓
                    Pipeline ETL
                         ↓
        Base SQLite final + CSV procesado
                         ↓
              API FastAPI + Dashboard Streamlit
                         ↓
                    Docker Compose
```

## Estructura del proyecto

```text
GPU-Market-Analytics/
│
├── api/
│   └── main.py
│
├── dashboards/
│   └── app.py
│
├── data/
│   ├── raw/
│   │   └── gpu_specs_v7.csv
│   ├── processed/
│   └── database/
│
├── docs/
│   ├── arquitectura.md
│   ├── manual_usuario.md
│   ├── guia_despliegue.md
│   ├── api.md
│   └── testing.md
│
├── etl/
│   ├── create_inventory.py
│   ├── extract.py
│   ├── transform.py
│   ├── load.py
│   └── pipeline.py
│
├── tests/
│   ├── test_api.py
│   └── test_etl.py
│
├── .dockerignore
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── pytest.ini
├── requirements.txt
└── README.md
```

## Tecnologías utilizadas

* Python 3.12
* Pandas
* NumPy
* Requests
* SQLite
* Streamlit
* Plotly
* FastAPI
* Uvicorn
* Pytest
* Docker
* Docker Compose
* Git y GitHub

## Instalación local

### 1. Clonar el repositorio

```powershell
git clone https://github.com/Abraham1439/GPU-Market-Analytics.git
cd GPU-Market-Analytics
```

### 2. Crear entorno virtual

```powershell
python -m venv venv
.\venv\Scripts\Activate
```

### 3. Instalar dependencias

```powershell
pip install -r requirements.txt
```

### 4. Crear archivo `.env`

Crear un archivo `.env` en la raíz del proyecto usando como base `.env.example`.

Contenido esperado:

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

## Ejecución del pipeline ETL

Para generar el inventario simulado, integrar las fuentes y crear el dataset final:

```powershell
python -m etl.pipeline
```

El pipeline genera:

```text
data/database/inventario_tienda.db
data/database/gpu_market_analytics.db
data/processed/gpu_market_analytics.csv
```

## Ejecución de la API

```powershell
uvicorn api.main:app --reload --port 8000
```

Documentación Swagger:

```text
http://127.0.0.1:8000/docs
```

Endpoints principales:

```text
GET /
GET /health
GET /gpus
GET /resumen
GET /marcas
GET /top-precios
GET /inventario
GET /gamas
```

## Ejecución del dashboard

```powershell
streamlit run dashboards/app.py
```

URL local:

```text
http://localhost:8501
```

## Ejecución con Docker

Construir y levantar los servicios:

```powershell
docker compose up --build -d
```

Verificar contenedores:

```powershell
docker compose ps
```

Accesos:

```text
API FastAPI: http://localhost:8000/docs
Dashboard Streamlit: http://localhost:8501
```

Detener servicios:

```powershell
docker compose down
```

## Testing automatizado

Ejecutar pruebas:

```powershell
pytest -v
```

Resultado esperado:

```text
17 passed
```

Las pruebas validan:

* Existencia y estructura del CSV fuente.
* Normalización de nombres de GPU.
* Generación de archivos finales.
* Estructura del dataset procesado.
* Funcionamiento de endpoints principales de la API.

## Flujo de trabajo con Git

El proyecto se desarrolló usando ramas por funcionalidad:

```text
main
feature/1-pipeline-etl
feature/2-dashboard-streamlit
feature/3-api-fastapi
feature/4-tests
feature/5-docker
feature/6-documentacion
```

Cada rama fue integrada a `main` mediante Pull Request, permitiendo evidenciar trabajo colaborativo, revisión de cambios, commits claros y merges controlados.

## Componentes principales

### Pipeline ETL

Ubicación:

```text
etl/
```

Funciones principales:

* Crear inventario simulado.
* Extraer datos desde CSV.
* Extraer datos desde APIs externas.
* Leer inventario desde SQLite.
* Limpiar y transformar datos.
* Calcular precios en CLP.
* Clasificar GPUs por gama.
* Guardar dataset final en SQLite y CSV.

### Dashboard interactivo

Ubicación:

```text
dashboards/app.py
```

Incluye tres vistas:

* Vista ejecutiva.
* Vista técnica.
* Vista operativa.

### API REST

Ubicación:

```text
api/main.py
```

Permite consultar los datos procesados mediante endpoints HTTP.

### Docker

Archivos:

```text
Dockerfile
docker-compose.yml
.dockerignore
```

Permite ejecutar API y dashboard en contenedores.

## Valor de negocio

El proyecto permite apoyar decisiones comerciales en una tienda tecnológica simulada, entregando información sobre:

* Valor total del inventario.
* Stock disponible por marca.
* Productos con bajo stock.
* Precio promedio por marca.
* Evolución de precios por año.
* Segmentación de GPUs por gama.
* Conversión de precios desde USD a CLP.

## Lecciones aprendidas

Durante el desarrollo del proyecto se reforzaron conocimientos sobre integración de datos, consumo de APIs, limpieza y transformación con Pandas, creación de dashboards interactivos, desarrollo de APIs REST, testing automatizado, uso profesional de Git y despliegue reproducible con Docker.

## Mejoras futuras

Algunas mejoras posibles son:

* Incorporar una base PostgreSQL en lugar de SQLite.
* Automatizar el pipeline con tareas programadas.
* Publicar el dashboard en la nube.
* Agregar autenticación a la API.
* Mejorar el matching entre nombres de GPUs de distintas fuentes.
* Incorporar datos reales de precios de mercado actual.
