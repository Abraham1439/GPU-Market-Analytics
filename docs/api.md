# Documentación de API

## Descripción general

El proyecto GPU Market Analytics incluye una API REST propia desarrollada con FastAPI. Esta API permite consultar los datos procesados por el pipeline ETL y acceder a información relacionada con tarjetas gráficas, precios, stock, marcas, gamas y resumen general del inventario.

La API consume la base de datos SQLite final generada por el pipeline:

```text
data/database/gpu_market_analytics.db
```

La tabla principal utilizada es:

```text
gpu_analytics
```

## Tecnología utilizada

La API fue desarrollada con:

```text
FastAPI
Uvicorn
Pandas
SQLite
```

FastAPI permite generar documentación automática mediante Swagger, lo cual facilita la prueba y revisión de los endpoints.

## Ejecución local

Antes de ejecutar la API, se debe generar la base final mediante el pipeline ETL:

```powershell
python -m etl.pipeline
```

Luego se puede levantar la API con:

```powershell
uvicorn api.main:app --reload --port 8000
```

La API quedará disponible en:

```text
http://127.0.0.1:8000
```

La documentación Swagger queda disponible en:

```text
http://127.0.0.1:8000/docs
```

## Endpoints disponibles

### GET /

Endpoint principal de la API.

#### URL

```text
http://127.0.0.1:8000/
```

#### Descripción

Devuelve información general de la API, versión y endpoints disponibles.

#### Ejemplo de respuesta

```json
{
  "message": "GPU Market Analytics API",
  "version": "1.0.0",
  "docs": "/docs",
  "endpoints": [
    "/health",
    "/gpus",
    "/resumen",
    "/marcas",
    "/top-precios",
    "/inventario",
    "/gamas",
    "/predict/tdp",
    "/predict/gama",
    "/clusters/summary",
    "/clusters/gpus",
    "/models/info"
  ]
}
```

## GET /health

### URL

```text
http://127.0.0.1:8000/health
```

### Descripción

Verifica si la API está activa y si la base de datos final existe.

### Ejemplo de respuesta

```json
{
  "status": "ok",
  "database_exists": true,
  "database_path": "data/database/gpu_market_analytics.db",
  "table_name": "gpu_analytics"
}
```

### Uso en el proyecto

Este endpoint sirve para comprobar rápidamente que la API puede acceder a la base SQLite generada por el pipeline ETL.

## GET /gpus

### URL

```text
http://127.0.0.1:8000/gpus
```

### Descripción

Devuelve un listado de tarjetas gráficas disponibles en el dataset final.

### Parámetros opcionales

| Parámetro  | Tipo    | Descripción                                          |
| ---------- | ------- | ---------------------------------------------------- |
| `marca`    | string  | Filtra por marca, por ejemplo NVIDIA, AMD o Intel.   |
| `gama`     | string  | Filtra por gama, por ejemplo Gama alta o Gama media. |
| `anio_min` | integer | Año mínimo de lanzamiento.                           |
| `anio_max` | integer | Año máximo de lanzamiento.                           |
| `limit`    | integer | Cantidad máxima de registros a devolver.             |

### Ejemplos

```text
http://127.0.0.1:8000/gpus
```

```text
http://127.0.0.1:8000/gpus?limit=10
```

```text
http://127.0.0.1:8000/gpus?marca=NVIDIA&limit=10
```

```text
http://127.0.0.1:8000/gpus?anio_min=2015&anio_max=2025
```

### Ejemplo de respuesta

```json
{
  "total": 10,
  "data": [
    {
      "sku": "GPU-0001",
      "marca": "AMD",
      "modelo": "Radeon HD 7310 IGP",
      "anio_lanzamiento": 2012,
      "stock": 21,
      "precio_venta_clp": 450000
    }
  ]
}
```

## GET /resumen

### URL

```text
http://127.0.0.1:8000/resumen
```

### Descripción

Devuelve indicadores generales del inventario. Está orientado a una vista ejecutiva del negocio.

### Indicadores incluidos

```text
total_gpus
modelos_unicos
marcas_unicas
stock_total
valor_total_inventario_clp
precio_promedio_clp
anio_minimo
anio_maximo
tipo_cambio_usd_clp
```

### Ejemplo de respuesta

```json
{
  "total_gpus": 120,
  "modelos_unicos": 120,
  "marcas_unicas": 5,
  "stock_total": 1845,
  "valor_total_inventario_clp": 1250000000,
  "precio_promedio_clp": 680000,
  "anio_minimo": 1999,
  "anio_maximo": 2025,
  "tipo_cambio_usd_clp": 900.6
}
```

## GET /marcas

### URL

```text
http://127.0.0.1:8000/marcas
```

### Descripción

Devuelve información agrupada por marca de tarjeta gráfica.

### Datos entregados

```text
cantidad_modelos
stock_total
precio_promedio_clp
valor_total_inventario_clp
memoria_promedio_gb
```

### Uso en el proyecto

Este endpoint permite comparar marcas según inventario, precio promedio, valor total y memoria promedio.

## GET /top-precios

### URL

```text
http://127.0.0.1:8000/top-precios
```

### Descripción

Devuelve las tarjetas gráficas con mayor precio de venta.

### Parámetros opcionales

| Parámetro | Tipo    | Descripción                 |
| --------- | ------- | --------------------------- |
| `limit`   | integer | Cantidad de GPUs a mostrar. |

### Ejemplos

```text
http://127.0.0.1:8000/top-precios
```

```text
http://127.0.0.1:8000/top-precios?limit=5
```

### Uso en el proyecto

Este endpoint es útil para identificar los productos de mayor valor comercial dentro del inventario.

## GET /inventario

### URL

```text
http://127.0.0.1:8000/inventario
```

### Descripción

Devuelve información operativa del inventario de la tienda simulada.

### Parámetros opcionales

| Parámetro      | Tipo    | Descripción                                          |
| -------------- | ------- | ---------------------------------------------------- |
| `bajo_stock`   | boolean | Si es `true`, muestra solo productos con bajo stock. |
| `limite_stock` | integer | Define el límite para considerar bajo stock.         |

### Ejemplos

```text
http://127.0.0.1:8000/inventario
```

```text
http://127.0.0.1:8000/inventario?bajo_stock=true&limite_stock=5
```

### Uso en el proyecto

Este endpoint permite detectar productos que requieren reposición o revisión de stock.

## GET /gamas

### URL

```text
http://127.0.0.1:8000/gamas
```

### Descripción

Agrupa las tarjetas gráficas por gama.

### Gamas utilizadas

```text
Gama entrada
Gama media
Gama alta
Entusiasta
```

### Uso en el proyecto

Permite analizar cómo se distribuye el inventario según segmento de producto.

## Endpoints de Machine Learning

Estos endpoints requieren que los modelos hayan sido entrenados previamente:

```powershell
python -m models.train_regression
python -m models.train_classification
python -m models.train_clustering
```

Si no se han entrenado, la API responde con error 404 indicando qué comando ejecutar.

## POST /predict/tdp

### URL

```text
http://127.0.0.1:8000/predict/tdp
```

### Descripción

Predice el consumo eléctrico (TDP, en watts) de una GPU a partir de sus especificaciones técnicas, usando el mejor modelo de regresión entrenado (Random Forest, R² = 0.87 en el set de test).

### Body de ejemplo

```json
{
  "marca": "NVIDIA",
  "tipo_memoria": "GDDR6",
  "bus_interfaz": "PCIe 4.0 x16",
  "memoria_gb": 8.0,
  "bus_memoria_bits": 256.0,
  "gpu_clock_mhz": 1500.0,
  "mem_clock_mhz": 14000.0,
  "shaders": 4000.0,
  "tmu": 200.0,
  "rop": 80.0,
  "anio_lanzamiento": 2023
}
```

### Ejemplo de respuesta

```json
{
  "tdp_watts_predicho": 251.4,
  "modelo_usado": "random_forest",
  "mae_esperado_watts": 24.32,
  "r2_modelo": 0.8708
}
```

## POST /predict/gama

### URL

```text
http://127.0.0.1:8000/predict/gama
```

### Descripción

Predice la gama (Gama entrada / Gama media / Gama alta / Entusiasta) de una GPU a partir de sus specs técnicas y precio de venta. Si no se entrega `tdp_watts`, se estima automáticamente encadenando el modelo de regresión antes de clasificar.

### Body de ejemplo (sin tdp_watts, se autoestima)

```json
{
  "marca": "NVIDIA",
  "tipo_memoria": "GDDR6",
  "bus_interfaz": "PCIe 4.0 x16",
  "memoria_gb": 8.0,
  "bus_memoria_bits": 256.0,
  "gpu_clock_mhz": 1500.0,
  "mem_clock_mhz": 14000.0,
  "shaders": 4000.0,
  "tmu": 200.0,
  "rop": 80.0,
  "anio_lanzamiento": 2023,
  "precio_venta_clp": 900000
}
```

### Ejemplo de respuesta

```json
{
  "gama_predicha": "Gama alta",
  "tdp_watts_usado": 251.4,
  "tdp_estimado_automaticamente": true,
  "probabilidades_por_clase": {
    "Entusiasta": 0.0001,
    "Gama alta": 0.9999,
    "Gama entrada": 0.0,
    "Gama media": 0.0
  },
  "modelo_usado": "logistic_regression",
  "accuracy_esperado": 0.75
}
```

### Nota importante (transparencia del modelo)

`gama` se define parcialmente por precio, y `precio_venta_clp` en este proyecto es simulado aleatoriamente (ver `etl/create_inventory.py`). Por eso el modelo incluye el precio como feature — es información de negocio disponible al catalogar un producto, no un dato "prohibido". Ver `models/train_classification.py` para el detalle completo de esta decisión.

## GET /clusters/summary

### URL

```text
http://127.0.0.1:8000/clusters/summary
```

### Descripción

Devuelve el resultado del análisis de clustering (K-Means): K óptimo según silhouette score, tamaño de cada cluster, comparación cruzada contra las 4 gamas de negocio, y el perfil técnico promedio de cada cluster.

### Uso en el proyecto

Este endpoint respalda el hallazgo central del análisis de clustering: los grupos que forman las GPUs según sus specs reales **no coinciden** con las 4 gamas definidas manualmente, porque `gama` está dominada por el precio aleatorio del inventario simulado, no por las especificaciones técnicas.

## GET /clusters/gpus

### URL

```text
http://127.0.0.1:8000/clusters/gpus
```

### Descripción

Aplica el modelo de clustering entrenado sobre el inventario actual y devuelve a qué cluster pertenece cada GPU.

### Parámetros opcionales

| Parámetro | Tipo    | Descripción                          |
| --------- | ------- | ------------------------------------- |
| `cluster` | integer | Filtra solo las GPUs de ese cluster. |

### Ejemplos

```text
http://127.0.0.1:8000/clusters/gpus
```

```text
http://127.0.0.1:8000/clusters/gpus?cluster=1
```

## GET /models/info

### URL

```text
http://127.0.0.1:8000/models/info
```

### Descripción

Devuelve un resumen consolidado del estado y desempeño de los 3 modelos del portafolio ML (regresión, clasificación, clustering). Útil para poblar la sección de ML del dashboard y para el informe técnico ejecutivo.

## Pruebas desde Swagger

Para probar la API visualmente:

1. Ejecutar la API.
2. Abrir `http://127.0.0.1:8000/docs`.
3. Seleccionar un endpoint.
4. Presionar `Try it out`.
5. Presionar `Execute`.
6. Revisar la respuesta JSON.

## Manejo de errores

La API contempla errores comunes:

### Base de datos inexistente

Si la base final no existe, se devuelve un error indicando que se debe ejecutar el pipeline ETL.

Solución:

```powershell
python -m etl.pipeline
```

### Dataset vacío

Si la tabla `gpu_analytics` no tiene registros, la API responde con un mensaje indicando que la tabla está vacía.

### Error interno de lectura

Si ocurre un problema al leer SQLite, la API devuelve un error 500 con el detalle correspondiente.

## Ejecución con Docker

Cuando se ejecuta con Docker Compose, la API queda disponible en:

```text
http://localhost:8000/docs
```

Comando:

```powershell
docker compose up --build -d
```

Verificación:

```powershell
docker compose ps
```

## Importancia dentro de la arquitectura

La API cumple el rol de capa intermedia entre los datos procesados y los consumidores de información. Permite desacoplar la lógica de análisis de los sistemas que consumen los datos, facilitando una arquitectura más profesional y escalable.
