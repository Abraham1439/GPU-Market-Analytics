from pathlib import Path
import sqlite3

import pandas as pd
from fastapi import FastAPI, HTTPException, Query


BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "data" / "database" / "gpu_market_analytics.db"
TABLE_NAME = "gpu_analytics"

app = FastAPI(
    title="GPU Market Analytics API",
    description="API para consultar datos procesados de tarjetas gráficas, precios, stock e inventario.",
    version="1.0.0"
)


def load_data() -> pd.DataFrame:
    """
    Carga los datos procesados desde la base SQLite final.
    """
    if not DB_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail="No se encontró la base de datos final. Ejecuta primero: python -m etl.pipeline"
        )

    try:
        with sqlite3.connect(DB_PATH) as conn:
            df = pd.read_sql_query(f"SELECT * FROM {TABLE_NAME}", conn)
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Error al leer la base de datos: {error}"
        ) from error

    if df.empty:
        raise HTTPException(
            status_code=404,
            detail="La tabla gpu_analytics está vacía."
        )

    return df


@app.get("/")
def root() -> dict:
    """
    Endpoint inicial de la API.
    """
    return {
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
            "/gamas"
        ]
    }


@app.get("/health")
def health() -> dict:
    """
    Verifica el estado de la API y de la base de datos.
    """
    return {
        "status": "ok" if DB_PATH.exists() else "warning",
        "database_exists": DB_PATH.exists(),
        "database_path": str(DB_PATH),
        "table_name": TABLE_NAME,
    }

@app.get("/gpus")
def get_gpus(
    marca: str | None = Query(default=None, description="Filtrar por marca"),
    gama: str | None = Query(default=None, description="Filtrar por gama"),
    anio_min: int | None = Query(default=None, description="Año mínimo de lanzamiento"),
    anio_max: int | None = Query(default=None, description="Año máximo de lanzamiento"),
    limit: int = Query(default=50, ge=1, le=500, description="Cantidad máxima de registros")
) -> dict:
    """
    Devuelve listado de GPUs con filtros opcionales.
    """
    df = load_data()

    if marca:
        df = df[df["marca"].str.lower() == marca.lower()]

    if gama:
        df = df[df["gama"].str.lower() == gama.lower()]

    if anio_min is not None:
        df = df[df["anio_lanzamiento"] >= anio_min]

    if anio_max is not None:
        df = df[df["anio_lanzamiento"] <= anio_max]

    df = df.head(limit)

    return {
        "total": len(df),
        "data": df.to_dict(orient="records")
    }


@app.get("/resumen")
def get_resumen() -> dict:
    """
    Devuelve indicadores generales del inventario.
    """
    df = load_data()

    return {
        "total_gpus": int(len(df)),
        "modelos_unicos": int(df["modelo"].nunique()),
        "marcas_unicas": int(df["marca"].nunique()),
        "stock_total": int(df["stock"].sum()),
        "valor_total_inventario_clp": float(df["valor_total_stock_clp"].sum()),
        "precio_promedio_clp": float(df["precio_venta_clp"].mean()),
        "anio_minimo": int(df["anio_lanzamiento"].min()),
        "anio_maximo": int(df["anio_lanzamiento"].max()),
        "tipo_cambio_usd_clp": float(df["tipo_cambio_usd_clp"].iloc[0])
    }


@app.get("/marcas")
def get_marcas() -> dict:
    """
    Devuelve resumen agrupado por marca.
    """
    df = load_data()

    resumen = (
        df.groupby("marca", as_index=False)
        .agg(
            cantidad_modelos=("modelo", "nunique"),
            stock_total=("stock", "sum"),
            precio_promedio_clp=("precio_venta_clp", "mean"),
            valor_total_inventario_clp=("valor_total_stock_clp", "sum"),
            memoria_promedio_gb=("memoria_gb", "mean")
        )
        .sort_values("valor_total_inventario_clp", ascending=False)
    )

    return {
        "total_marcas": int(len(resumen)),
        "data": resumen.to_dict(orient="records")
    }


@app.get("/top-precios")
def get_top_precios(
    limit: int = Query(default=10, ge=1, le=100, description="Cantidad de GPUs a mostrar")
) -> dict:
    """
    Devuelve las GPUs con mayor precio de venta.
    """
    df = load_data()

    columns = [
        "sku",
        "marca",
        "modelo",
        "anio_lanzamiento",
        "gama",
        "stock",
        "precio_venta_clp",
        "precio_msrp_usd",
        "precio_msrp_clp"
    ]

    top = (
        df[columns]
        .sort_values("precio_venta_clp", ascending=False)
        .head(limit)
    )

    return {
        "total": int(len(top)),
        "data": top.to_dict(orient="records")
    }


@app.get("/inventario")
def get_inventario(
    bajo_stock: bool = Query(default=False, description="Mostrar solo productos con stock bajo"),
    limite_stock: int = Query(default=5, ge=0, description="Límite para considerar bajo stock")
) -> dict:
    """
    Devuelve información operativa del inventario.
    """
    df = load_data()

    if bajo_stock:
        df = df[df["stock"] <= limite_stock]

    columns = [
        "sku",
        "marca",
        "modelo",
        "stock",
        "estado",
        "proveedor",
        "precio_venta_clp",
        "valor_total_stock_clp"
    ]

    inventario = df[columns].sort_values("stock", ascending=True)

    return {
        "total": int(len(inventario)),
        "data": inventario.to_dict(orient="records")
    }


@app.get("/gamas")
def get_gamas() -> dict:
    """
    Devuelve resumen agrupado por gama.
    """
    df = load_data()

    resumen = (
        df.groupby("gama", as_index=False)
        .agg(
            cantidad_modelos=("modelo", "nunique"),
            stock_total=("stock", "sum"),
            precio_promedio_clp=("precio_venta_clp", "mean"),
            valor_total_inventario_clp=("valor_total_stock_clp", "sum")
        )
        .sort_values("valor_total_inventario_clp", ascending=False)
    )

    return {
        "total_gamas": int(len(resumen)),
        "data": resumen.to_dict(orient="records")
    }