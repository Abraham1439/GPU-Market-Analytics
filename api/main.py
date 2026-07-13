from pathlib import Path
import sqlite3

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from models.model_utils import load_metrics, load_model


BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "data" / "database" / "gpu_market_analytics.db"
TABLE_NAME = "gpu_analytics"

app = FastAPI(
    title="GPU Market Analytics API",
    description="API para consultar datos procesados de tarjetas gráficas, precios, stock e inventario.",
    version="1.0.0"
)


class TDPPredictionInput(BaseModel):
    """
    Specs necesarias para predecir el consumo eléctrico (TDP) de una
    GPU. Deben coincidir exactamente con las features usadas al
    entrenar (ver models/train_regression.py).
    """
    marca: str
    tipo_memoria: str
    bus_interfaz: str
    memoria_gb: float
    bus_memoria_bits: float
    gpu_clock_mhz: float
    mem_clock_mhz: float
    shaders: float
    tmu: float
    rop: float
    anio_lanzamiento: int
    tflops_api: float = 0.0


class GamaPredictionInput(TDPPredictionInput):
    """
    Specs necesarias para predecir la gama de una GPU. Además de las
    specs técnicas, requiere precio_venta_clp (ver justificación en
    models/train_classification.py: el precio es información
    disponible al momento de catalogar un producto nuevo).

    tdp_watts es opcional: si no se entrega, se estima automáticamente
    usando el modelo de regresión antes de clasificar.
    """
    precio_venta_clp: float
    tdp_watts: float | None = None


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


def load_trained_model(name: str):
    """
    Carga un modelo entrenado desde models/artifacts/, con un error
    claro si todavía no se ha corrido el entrenamiento.
    """
    try:
        return load_model(name)
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=(
                f"El modelo '{name}' no está entrenado todavía. "
                f"Ejecuta: python -m models.train_regression / "
                f"train_classification / train_clustering"
            )
        )


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
            "/gamas",
            "/predict/tdp",
            "/predict/gama",
            "/clusters/summary",
            "/clusters/gpus",
            "/models/info"
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


@app.post("/predict/tdp")
def predict_tdp(payload: TDPPredictionInput) -> dict:
    """
    Predice el consumo eléctrico (TDP en watts) de una GPU a partir
    de sus specs técnicas, usando el mejor modelo de regresión
    entrenado (ver models/train_regression.py).
    """
    model = load_trained_model("regression_model")

    input_df = pd.DataFrame([payload.model_dump()])
    prediction = model.predict(input_df)[0]

    metrics = load_metrics("regression")

    return {
        "tdp_watts_predicho": round(float(prediction), 1),
        "modelo_usado": metrics["best_model"],
        "mae_esperado_watts": metrics["comparison"][metrics["best_model"]]["mae_watts"],
        "r2_modelo": metrics["comparison"][metrics["best_model"]]["r2"],
    }


@app.post("/predict/gama")
def predict_gama(payload: GamaPredictionInput) -> dict:
    """
    Predice la gama (Entrada/Media/Alta/Entusiasta) de una GPU a
    partir de sus specs técnicas + precio de venta, usando el mejor
    modelo de clasificación entrenado (ver
    models/train_classification.py).

    Si no se entrega tdp_watts, se estima automáticamente con el
    modelo de regresión antes de clasificar.
    """
    data = payload.model_dump()

    tdp_estimado = False
    if data["tdp_watts"] is None:
        regression_model = load_trained_model("regression_model")
        tdp_input = {k: v for k, v in data.items() if k not in ("precio_venta_clp", "tdp_watts")}
        data["tdp_watts"] = round(float(regression_model.predict(pd.DataFrame([tdp_input]))[0]), 1)
        tdp_estimado = True

    classification_model = load_trained_model("classification_model")

    input_df = pd.DataFrame([data])
    prediction = classification_model.predict(input_df)[0]

    probabilities = None
    if hasattr(classification_model, "predict_proba"):
        proba = classification_model.predict_proba(input_df)[0]
        classes = classification_model.named_steps["model"].classes_
        probabilities = {
            str(cls): round(float(p), 4) for cls, p in zip(classes, proba)
        }

    metrics = load_metrics("classification")

    return {
        "gama_predicha": str(prediction),
        "tdp_watts_usado": data["tdp_watts"],
        "tdp_estimado_automaticamente": tdp_estimado,
        "probabilidades_por_clase": probabilities,
        "modelo_usado": metrics["best_model"],
        "accuracy_esperado": metrics["comparison"][metrics["best_model"]]["accuracy"],
    }


@app.get("/clusters/summary")
def get_clusters_summary() -> dict:
    """
    Devuelve el resumen del análisis de clustering: K óptimo,
    tamaños de cluster, comparación contra las gamas de negocio y
    perfil promedio de cada cluster (ver models/train_clustering.py).
    """
    metrics = load_metrics("clustering")

    return {
        "k_optimo_por_silhouette": metrics["best_k_by_silhouette"],
        "silhouette_score": metrics["silhouettes_by_k"][str(metrics["best_k_by_silhouette"])],
        "tamano_clusters": metrics["cluster_sizes"],
        "comparacion_vs_gama": metrics["crosstab_cluster_vs_gama"],
        "perfil_promedio_por_cluster": metrics["cluster_profile_means"],
        "referencia_k4": metrics["k4_reference"],
    }


@app.get("/clusters/gpus")
def get_clusters_gpus(
    cluster: int | None = Query(default=None, description="Filtrar por número de cluster")
) -> dict:
    """
    Aplica el modelo de clustering entrenado sobre el inventario
    actual y devuelve a qué cluster pertenece cada GPU.
    """
    from models.train_clustering import CLUSTERING_FEATURES

    df = load_data()
    model = load_trained_model("clustering_model")

    df["cluster"] = model.predict(df[CLUSTERING_FEATURES])

    if cluster is not None:
        df = df[df["cluster"] == cluster]

    columns = ["sku", "marca", "modelo", "gama", "precio_venta_clp", "cluster"]

    return {
        "total": int(len(df)),
        "data": df[columns].to_dict(orient="records")
    }


@app.get("/models/info")
def get_models_info() -> dict:
    """
    Devuelve un resumen consolidado del estado y desempeño de los 3
    modelos del portafolio ML (útil para el dashboard y el informe
    ejecutivo).
    """
    info = {}

    for name in ["regression", "classification", "clustering"]:
        try:
            info[name] = load_metrics(name)
        except FileNotFoundError:
            info[name] = {"status": "no entrenado todavía"}

    return info