# Documentación de testing

## Descripción general

El proyecto GPU Market Analytics incorpora pruebas automatizadas utilizando Pytest. Estas pruebas permiten validar que el pipeline ETL, el dataset final y la API funcionen correctamente.

El objetivo del testing es asegurar que los componentes principales del proyecto puedan ejecutarse de manera confiable y que los datos procesados cumplan con la estructura esperada.

## Herramienta utilizada

La herramienta utilizada para las pruebas es:

```text
pytest
```

También se utiliza:

```text
fastapi.testclient
```

para probar los endpoints de la API sin necesidad de levantar manualmente el servidor con Uvicorn.

## Estructura de pruebas

Las pruebas se encuentran en la carpeta:

```text
tests/
```

Archivos principales:

```text
tests/test_etl.py
tests/test_api.py
```

Además, se utiliza el archivo:

```text
pytest.ini
```

para configurar la detección de pruebas.

## Configuración de pytest

Archivo:

```text
pytest.ini
```

Contenido:

```ini
[pytest]
pythonpath = .
testpaths = tests
```

Esta configuración permite que Pytest encuentre correctamente los módulos del proyecto, como `etl` y `api`.

## Ejecución de pruebas

Para ejecutar las pruebas:

```powershell
pytest
```

Para ver más detalle:

```powershell
pytest -v
```

Resultado esperado:

```text
17 passed
```

Durante la ejecución puede aparecer una advertencia relacionada con `TestClient` o `httpx`. Esta advertencia no afecta el funcionamiento del proyecto mientras las pruebas aparezcan como aprobadas.

## Pruebas del ETL

Archivo:

```text
tests/test_etl.py
```

Este archivo valida el funcionamiento del pipeline ETL y la estructura del dataset final.

### Prueba 1: existencia y estructura del CSV

Valida que el archivo CSV fuente se pueda cargar correctamente y que contenga columnas mínimas esperadas.

Columnas revisadas:

```text
manufacturer
productName
releaseYear
memSize
gpuClock
memType
```

Importancia:

Esta prueba asegura que la fuente principal de datos técnicos esté disponible y tenga la estructura requerida para iniciar el pipeline.

### Prueba 2: normalización de nombres

Valida la función encargada de normalizar nombres de tarjetas gráficas.

Ejemplo:

```text
NVIDIA GeForce RTX 4070 Ti
```

Resultado esperado:

```text
geforce rtx 4070 ti
```

Importancia:

La normalización es necesaria para cruzar datos entre distintas fuentes que pueden tener nombres escritos de forma diferente.

### Prueba 3: generación de archivos finales

Ejecuta el pipeline completo y verifica que se generen los archivos finales:

```text
data/database/gpu_market_analytics.db
data/processed/gpu_market_analytics.csv
```

Importancia:

Permite validar que el pipeline end-to-end funciona desde la extracción hasta la carga.

### Prueba 4: base SQLite con datos

Valida que la tabla final `gpu_analytics` exista y contenga registros.

Importancia:

Confirma que la carga en SQLite se realizó correctamente.

### Prueba 5: columnas esperadas del dataset final

Verifica que el dataset final contenga columnas calculadas importantes:

```text
sku
marca
modelo
anio_lanzamiento
stock
precio_venta_clp
precio_msrp_usd
precio_msrp_clp
valor_total_stock_clp
gama
tipo_cambio_usd_clp
```

Importancia:

Asegura que las transformaciones principales del proyecto fueron aplicadas correctamente.

### Prueba 6: validación del dataset final

Valida que la función `validate_final_dataset` acepte correctamente el dataset generado.

Importancia:

Comprueba que el dataset final cumple con las reglas mínimas antes de ser utilizado por la API o dashboard.

## Pruebas de la API

Archivo:

```text
tests/test_api.py
```

Este archivo prueba los endpoints principales de la API desarrollada con FastAPI.

Antes de ejecutar las pruebas de API, se ejecuta el pipeline para asegurar que exista la base final.

### Prueba 1: endpoint raíz

Endpoint probado:

```text
GET /
```

Valida que la API responda correctamente y que el mensaje principal sea:

```text
GPU Market Analytics API
```

### Prueba 2: endpoint de salud

Endpoint probado:

```text
GET /health
```

Valida que la API encuentre la base de datos y que la tabla utilizada sea:

```text
gpu_analytics
```

### Prueba 3: resumen ejecutivo

Endpoint probado:

```text
GET /resumen
```

Valida que existan indicadores como:

```text
total_gpus
stock_total
valor_total_inventario_clp
```

También verifica que los valores principales sean mayores que cero.

### Prueba 4: listado de GPUs

Endpoint probado:

```text
GET /gpus?limit=5
```

Valida que el endpoint devuelva una lista de registros y respete el límite definido.

### Prueba 5: resumen por marcas

Endpoint probado:

```text
GET /marcas
```

Valida que se devuelva información agrupada por marca.

### Prueba 6: ranking de precios

Endpoint probado:

```text
GET /top-precios?limit=5
```

Valida que se entregue un ranking limitado de tarjetas gráficas con mayor precio.

### Prueba 7: inventario

Endpoint probado:

```text
GET /inventario
```

Valida que el endpoint entregue información operativa del inventario.

## Resultado obtenido

En la ejecución local se obtuvo el siguiente resultado:

```text
13 passed
```

Esto indica que las pruebas del ETL y de la API se ejecutaron correctamente.

## Evidencia recomendada

Para la entrega o presentación se recomienda incluir una captura de:

```powershell
pytest -v
```

donde se vea el resultado:

```text
13 passed
```

También se puede mencionar que las pruebas validan tanto el procesamiento de datos como el funcionamiento de los endpoints principales.

## Importancia del testing en el proyecto

El testing automatizado permite:

* Detectar errores rápidamente.
* Validar que el ETL siga funcionando después de cambios.
* Confirmar que la API responde correctamente.
* Aumentar la confiabilidad del proyecto.
* Evidenciar buenas prácticas de desarrollo.

## Comandos útiles

Ejecutar todas las pruebas:

```powershell
pytest
```

Ejecutar pruebas con detalle:

```powershell
pytest -v
```

Ejecutar solo pruebas del ETL:

```powershell
pytest tests/test_etl.py -v
```

Ejecutar solo pruebas de API:

```powershell
pytest tests/test_api.py -v
```

## Posibles errores

### Error de importación

Si aparece un error como:

```text
ModuleNotFoundError
```

verificar que exista `pytest.ini` y que contenga:

```ini
[pytest]
pythonpath = .
testpaths = tests
```

### Error por base inexistente

Ejecutar:

```powershell
python -m etl.pipeline
```

y luego repetir:

```powershell
pytest -v
```

### Advertencia de dependencias

Puede aparecer una advertencia relacionada con `httpx` o `TestClient`. No afecta la entrega mientras los tests finalicen correctamente.
