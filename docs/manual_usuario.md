# Manual de usuario

## Descripción general

Este manual explica cómo utilizar el sistema GPU Market Analytics desde el punto de vista de un usuario final. El sistema permite analizar información de tarjetas gráficas mediante un dashboard interactivo y consultar datos procesados mediante una API REST.

El usuario puede visualizar indicadores de negocio, características técnicas, stock, precios y segmentación de GPUs.

## Acceso al sistema

El sistema puede ejecutarse de dos formas:

1. Localmente con Python.
2. Mediante Docker Compose.

## Acceso al dashboard

Si se ejecuta localmente:

```powershell
streamlit run dashboards/app.py
```

Luego abrir:

```text
http://localhost:8501
```

Si se ejecuta con Docker:

```powershell
docker compose up --build -d
```

Luego abrir:

```text
http://localhost:8501
```

## Acceso a la API

Si se ejecuta localmente:

```powershell
uvicorn api.main:app --reload --port 8000
```

Luego abrir:

```text
http://127.0.0.1:8000/docs
```

Si se ejecuta con Docker:

```text
http://localhost:8000/docs
```

## Uso del dashboard

El dashboard está desarrollado con Streamlit y permite explorar la información procesada mediante filtros, gráficos y tablas.

Al ingresar al dashboard, el usuario verá el título del proyecto y una barra lateral de filtros.

## Filtros disponibles

En la barra lateral se encuentran filtros interactivos.

### Filtro por marca

Permite seleccionar una o varias marcas de tarjetas gráficas.

Ejemplos:

```text
NVIDIA
AMD
Intel
ATI
```

Uso:

* Seleccionar una marca para ver solo sus productos.
* Seleccionar varias marcas para compararlas.
* Dejar todas seleccionadas para una vista general.

### Filtro por gama

Permite filtrar las GPUs según su segmento.

Gamas disponibles:

```text
Gama entrada
Gama media
Gama alta
Entusiasta
```

Uso:

* Comparar productos de gama alta.
* Revisar productos de entrada.
* Analizar el valor de inventario por segmento.

### Filtro por tipo de memoria

Permite seleccionar tarjetas gráficas según el tipo de memoria.

Ejemplos:

```text
GDDR5
GDDR6
GDDR6X
DDR3
No especificado
```

Uso:

* Analizar tecnologías de memoria.
* Comparar generaciones de GPUs.
* Observar qué tipos de memoria predominan en el inventario.

### Filtro por año de lanzamiento

Permite definir un rango de años para visualizar GPUs lanzadas en un periodo específico.

Uso:

* Analizar GPUs antiguas.
* Revisar modelos recientes.
* Observar la evolución de memoria y precio por año.

## Vistas del dashboard

El dashboard contiene tres vistas principales:

```text
Vista ejecutiva
Vista técnica
Vista operativa
```

Cada una está orientada a una audiencia diferente.

## Vista ejecutiva

La vista ejecutiva está orientada a la toma de decisiones de negocio.

### Indicadores principales

Incluye métricas como:

```text
Valor total del inventario
Stock total
Precio promedio
Modelos únicos
```

### Gráfico de valor de inventario por marca

Este gráfico permite identificar qué marcas concentran mayor valor económico dentro del inventario.

Interpretación:

* Una barra más alta indica mayor valor total de inventario.
* Sirve para identificar marcas estratégicas para la tienda.
* Permite comparar el peso comercial de cada fabricante.

### Top 10 GPUs más caras

Muestra las tarjetas gráficas con mayor precio de venta.

Uso:

* Identificar productos premium.
* Detectar modelos de alto valor.
* Apoyar decisiones comerciales y de inventario.

## Vista técnica

La vista técnica está orientada al análisis de características de hardware.

### Memoria promedio por año

Permite observar cómo ha evolucionado la memoria de las tarjetas gráficas a lo largo del tiempo.

Interpretación:

* Una tendencia ascendente indica aumento en capacidad de memoria.
* Permite relacionar generación tecnológica con capacidad técnica.

### Relación entre memoria y precio

Muestra un gráfico de dispersión entre memoria en GB y precio de venta en CLP.

Uso:

* Observar si las GPUs con más memoria tienden a ser más caras.
* Comparar marcas.
* Detectar modelos que pueden tener precio alto o bajo respecto a su memoria.

### Distribución por tipo de memoria

Muestra cuántas GPUs existen por tipo de memoria.

Uso:

* Identificar tecnologías predominantes.
* Comparar generaciones de memoria.
* Analizar obsolescencia o modernización del inventario.

### Comparación técnica por marca

Muestra una tabla resumen con promedios técnicos por marca.

Incluye:

```text
memoria promedio
gpu clock promedio
shaders promedio
precio promedio
```

## Vista operativa

La vista operativa está orientada a la gestión interna de la tienda.

### Stock por marca

Permite visualizar cuántas unidades hay disponibles por fabricante.

Uso:

* Detectar marcas con mayor o menor disponibilidad.
* Apoyar decisiones de compra.
* Analizar concentración de inventario.

### Distribución del stock por estado

Muestra la proporción de productos según su condición.

Estados posibles:

```text
Nuevo
Usado
Reacondicionado
```

Uso:

* Conocer el estado general del inventario.
* Identificar si hay exceso de productos usados o reacondicionados.
* Apoyar decisiones de reposición.

### Productos con bajo stock

Muestra productos con pocas unidades disponibles.

Uso:

* Detectar productos que podrían necesitar reposición.
* Priorizar compras.
* Evitar quiebres de stock.

### Inventario detallado

Tabla con información específica de cada GPU.

Columnas incluidas:

```text
sku
marca
modelo
anio_lanzamiento
gama
stock
estado
proveedor
precio_venta_clp
valor_total_stock_clp
```

## Uso de la API mediante Swagger

La API cuenta con documentación interactiva en Swagger.

Acceso:

```text
http://localhost:8000/docs
```

### Pasos para probar un endpoint

1. Abrir Swagger.
2. Seleccionar un endpoint.
3. Presionar `Try it out`.
4. Ingresar parámetros si corresponde.
5. Presionar `Execute`.
6. Revisar la respuesta JSON.

### Endpoints útiles

```text
GET /health
GET /resumen
GET /gpus
GET /marcas
GET /top-precios
GET /inventario
GET /gamas
```

## Ejemplos de uso

### Ver resumen ejecutivo

Endpoint:

```text
GET /resumen
```

Permite obtener valores generales como stock total, precio promedio y valor total de inventario.

### Ver GPUs más caras

Endpoint:

```text
GET /top-precios?limit=10
```

Permite ver las 10 tarjetas gráficas con mayor precio de venta.

### Ver productos con bajo stock

Endpoint:

```text
GET /inventario?bajo_stock=true&limite_stock=5
```

Permite identificar productos con stock menor o igual a 5 unidades.

### Filtrar GPUs por marca

Endpoint:

```text
GET /gpus?marca=NVIDIA&limit=10
```

Permite consultar GPUs de una marca específica.

## Recomendaciones de uso

Para una revisión completa del sistema se recomienda:

1. Ejecutar el pipeline ETL.
2. Abrir el dashboard.
3. Probar filtros.
4. Revisar las tres vistas.
5. Abrir Swagger.
6. Probar endpoints principales.
7. Ejecutar pruebas automatizadas.
8. Verificar contenedores Docker si se usa despliegue containerizado.

## Problemas frecuentes

### El dashboard no muestra datos

Posible causa:

La base final no fue generada.

Solución:

```powershell
python -m etl.pipeline
```

### La API indica que no existe la base de datos

Solución:

```powershell
python -m etl.pipeline
```

Luego reiniciar la API.

### Docker no abre el dashboard

Verificar que los contenedores estén activos:

```powershell
docker compose ps
```

Si no están activos:

```powershell
docker compose up --build -d
```

### El puerto está ocupado

Si el puerto 8000 o 8501 está ocupado, cerrar procesos anteriores o detener Docker:

```powershell
docker compose down
```

## Público objetivo del dashboard

El dashboard fue diseñado para tres tipos de usuarios:

### Usuario ejecutivo

Busca indicadores generales para tomar decisiones de negocio.

Ejemplos:

```text
valor total del inventario
precio promedio
marcas más valiosas
productos más caros
```

### Usuario técnico

Busca analizar características de hardware.

Ejemplos:

```text
memoria por año
tipo de memoria
relación entre memoria y precio
comparación técnica por marca
```

### Usuario operativo

Busca gestionar inventario y stock.

Ejemplos:

```text
stock por marca
productos con bajo stock
estado del inventario
proveedor
valor por producto
```

## Cierre

GPU Market Analytics permite explorar de forma clara y visual un conjunto de datos integrado sobre tarjetas gráficas. El sistema combina pipeline ETL, API, dashboard y Docker para entregar una solución completa, reproducible y fácil de utilizar.
