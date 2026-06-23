# Arquitectura del sistema

## Descripción general

GPU Market Analytics fue diseñado como una solución end-to-end de análisis de datos. La arquitectura integra fuentes heterogéneas, ejecuta un pipeline ETL, almacena datos procesados, expone información mediante una API REST y presenta visualizaciones en un dashboard interactivo.

El objetivo de esta arquitectura es separar responsabilidades, facilitar la reproducibilidad del proyecto y permitir que cada componente pueda ser probado, ejecutado y explicado de forma independiente.

## Diagrama conceptual

```text
┌──────────────────────────────┐
│ CSV Kaggle                   │
│ gpu_specs_v7.csv             │
└───────────────┬──────────────┘
                │
┌───────────────▼──────────────┐
│ API externa GPU              │
│ gpu-info-api                 │
└───────────────┬──────────────┘
                │
┌───────────────▼──────────────┐
│ SQLite Inventario            │
│ inventario_tienda.db         │
└───────────────┬──────────────┘
                │
┌───────────────▼──────────────┐
│ API tipo de cambio           │
│ mindicador.cl                │
└───────────────┬──────────────┘
                │
                ▼
┌──────────────────────────────┐
│ Pipeline ETL                 │
│ extract + transform + load   │
└───────────────┬──────────────┘
                │
                ▼
┌──────────────────────────────┐
│ Dataset final                │
│ gpu_market_analytics.db      │
│ gpu_market_analytics.csv     │
└───────────────┬──────────────┘
                │
       ┌────────┴────────┐
       ▼                 ▼
┌──────────────┐   ┌──────────────┐
│ FastAPI      │   │ Streamlit    │
│ API REST     │   │ Dashboard    │
└──────────────┘   └──────────────┘
       │                 │
       └────────┬────────┘
                ▼
        ┌──────────────┐
        │ Docker       │
        │ Compose      │
        └──────────────┘
```

## Componentes principales

### 1. Fuentes de datos

El sistema integra cuatro fuentes:

#### CSV de especificaciones

Archivo:

```text
data/raw/gpu_specs_v7.csv
```

Contiene datos técnicos de tarjetas gráficas, tales como:

* Marca.
* Modelo.
* Año de lanzamiento.
* Memoria.
* Tipo de memoria.
* Bus de memoria.
* Frecuencia de GPU.
* Shaders.
* Chip gráfico.

#### API externa de GPUs

URL:

```text
https://raw.githubusercontent.com/voidful/gpu-info-api/gpu-data/gpu.json
```

Se utiliza como fuente externa complementaria para enriquecer la información de tarjetas gráficas.

#### Base SQLite de inventario

Archivo:

```text
data/database/inventario_tienda.db
```

Se genera mediante el script:

```text
etl/create_inventory.py
```

Contiene datos simulados de tienda:

* SKU.
* Marca.
* Modelo.
* Stock.
* Estado.
* Proveedor.
* Precio de venta en CLP.

#### API de tipo de cambio

URL:

```text
https://mindicador.cl/api/dolar
```

Permite obtener el valor del dólar observado para convertir valores desde USD a CLP.

## 2. Pipeline ETL

El pipeline se encuentra en la carpeta:

```text
etl/
```

Archivos principales:

```text
create_inventory.py
extract.py
transform.py
load.py
pipeline.py
```

### Extract

Archivo:

```text
etl/extract.py
```

Responsabilidades:

* Leer el CSV de GPUs.
* Leer inventario desde SQLite.
* Consumir API externa de GPUs.
* Consumir API de tipo de cambio.
* Validar existencia de fuentes.
* Manejar errores de conexión o archivos inexistentes.

### Transform

Archivo:

```text
etl/transform.py
```

Responsabilidades:

* Limpiar columnas.
* Normalizar nombres de GPUs.
* Convertir tipos de datos.
* Unir inventario con especificaciones técnicas.
* Integrar datos provenientes de API.
* Calcular precios en CLP.
* Calcular valor total de stock.
* Clasificar GPUs por gama.
* Preparar dataset final para análisis.

### Load

Archivo:

```text
etl/load.py
```

Responsabilidades:

* Validar el dataset final.
* Guardar datos procesados en SQLite.
* Guardar datos procesados en CSV.

Salidas:

```text
data/database/gpu_market_analytics.db
data/processed/gpu_market_analytics.csv
```

## 3. Base de datos final

La base de datos final es:

```text
data/database/gpu_market_analytics.db
```

Tabla principal:

```text
gpu_analytics
```

Contiene datos consolidados listos para consumo por API y dashboard.

Columnas relevantes:

```text
sku
marca
modelo
anio_lanzamiento
stock
estado
proveedor
precio_venta_clp
precio_msrp_usd
precio_msrp_clp
valor_total_stock_clp
gama
memoria_mb
memoria_gb
tipo_memoria
tipo_cambio_usd_clp
```

## 4. API REST

Archivo:

```text
api/main.py
```

Framework utilizado:

```text
FastAPI
```

La API expone los datos procesados mediante endpoints HTTP. Además, FastAPI genera documentación automática mediante Swagger.

URL local:

```text
http://127.0.0.1:8000/docs
```

Endpoints principales:

```text
/
 /health
 /gpus
 /resumen
 /marcas
 /top-precios
 /inventario
 /gamas
```

## 5. Dashboard interactivo

Archivo:

```text
dashboards/app.py
```

Herramientas utilizadas:

```text
Streamlit
Plotly
```

El dashboard permite visualizar los datos procesados con filtros interactivos.

Vistas incluidas:

### Vista ejecutiva

Orientada a indicadores de negocio:

* Valor total del inventario.
* Stock total.
* Precio promedio.
* Top GPUs más caras.
* Valor de inventario por marca.

### Vista técnica

Orientada a análisis de hardware:

* Memoria promedio por año.
* Relación entre memoria y precio.
* Distribución por tipo de memoria.
* Comparación técnica por marca.

### Vista operativa

Orientada a gestión de tienda:

* Stock por marca.
* Stock por estado.
* Productos con bajo stock.
* Inventario detallado.

## 6. Testing

Carpeta:

```text
tests/
```

Herramienta:

```text
pytest
```

Pruebas implementadas:

* Validación de CSV fuente.
* Validación de normalización de nombres.
* Validación de generación de archivos finales.
* Validación de estructura del dataset.
* Validación de endpoints principales de API.

## 7. Docker

Archivos:

```text
Dockerfile
docker-compose.yml
.dockerignore
```

Servicios definidos:

```text
api
dashboard
```

Puertos:

```text
8000 -> API FastAPI
8501 -> Dashboard Streamlit
```

Comando principal:

```powershell
docker compose up --build -d
```

## 8. Justificación de arquitectura

La arquitectura separa responsabilidades:

* El pipeline ETL se encarga de procesar datos.
* SQLite almacena los datos finales.
* FastAPI expone los datos como servicio.
* Streamlit presenta visualizaciones interactivas.
* Docker permite ejecutar el sistema de forma reproducible.
* GitHub permite evidenciar trabajo colaborativo mediante ramas y Pull Requests.

Esta separación permite mantener el proyecto ordenado, escalable y fácil de explicar en una presentación técnica.
