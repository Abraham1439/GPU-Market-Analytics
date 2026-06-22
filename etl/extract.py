from pathlib import Path
import logging
import os
import sqlite3

import pandas as pd
import requests
from dotenv import load_dotenv


load_dotenv()

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(levelname)s - %(message)s"
)

BASE_DIR = Path(__file__).resolve().parents[1]

GPU_CSV_PATH = BASE_DIR / os.getenv("GPU_CSV_PATH", "data/raw/gpu_specs_v7.csv")
INVENTORY_DB_PATH = BASE_DIR / os.getenv(
    "INVENTORY_DB_PATH",
    "data/database/inventario_tienda.db"
)

GPU_INFO_API_URL = os.getenv(
    "GPU_INFO_API_URL",
    "https://raw.githubusercontent.com/voidful/gpu-info-api/gpu-data/gpu.json"
)

EXCHANGE_RATE_API_URL = os.getenv(
    "EXCHANGE_RATE_API_URL",
    "https://mindicador.cl/api/dolar"
)


def extract_gpu_csv() -> pd.DataFrame:
    """
    Extrae datos técnicos de GPUs desde el archivo CSV local.
    """
    logging.info("Extrayendo datos desde CSV: %s", GPU_CSV_PATH)

    if not GPU_CSV_PATH.exists():
        raise FileNotFoundError(f"No se encontró el archivo CSV: {GPU_CSV_PATH}")

    df = pd.read_csv(GPU_CSV_PATH)

    required_columns = [
        "manufacturer",
        "productName",
        "releaseYear",
        "memSize",
        "memBusWidth",
        "gpuClock",
        "memClock",
        "unifiedShader",
        "tmu",
        "rop",
        "memType",
        "bus",
        "gpuChip"
    ]

    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        raise ValueError(f"Faltan columnas obligatorias en CSV: {missing_columns}")

    logging.info("CSV cargado correctamente. Registros: %s", len(df))
    return df


def extract_inventory_db() -> pd.DataFrame:
    """
    Extrae el inventario simulado desde SQLite.
    """
    logging.info("Extrayendo inventario desde SQLite: %s", INVENTORY_DB_PATH)

    if not INVENTORY_DB_PATH.exists():
        raise FileNotFoundError(
            f"No se encontró la base de inventario: {INVENTORY_DB_PATH}. "
            "Ejecuta primero: python etl/create_inventory.py"
        )

    with sqlite3.connect(INVENTORY_DB_PATH) as conn:
        df = pd.read_sql_query("SELECT * FROM inventario_gpu", conn)

    required_columns = [
        "sku",
        "marca",
        "modelo",
        "anio_lanzamiento",
        "stock",
        "estado",
        "proveedor",
        "precio_venta_clp"
    ]

    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        raise ValueError(f"Faltan columnas obligatorias en inventario: {missing_columns}")

    logging.info("Inventario cargado correctamente. Registros: %s", len(df))
    return df


def extract_gpu_api() -> pd.DataFrame:
    """
    Extrae información adicional de GPUs desde la API externa.
    """
    logging.info("Extrayendo datos desde API externa de GPUs")

    try:
        response = requests.get(GPU_INFO_API_URL, timeout=30)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as error:
        logging.error("Error al consumir API externa de GPUs: %s", error)
        return pd.DataFrame()

    if isinstance(data, dict):
        data = data.get("data", data)

    df = pd.DataFrame(data)

    logging.info("API de GPUs cargada correctamente. Registros: %s", len(df))
    return df


def extract_exchange_rate() -> float:
    """
    Extrae el valor más reciente del dólar observado desde mindicador.cl.
    """
    logging.info("Extrayendo valor del dólar desde API mindicador.cl")

    try:
        response = requests.get(EXCHANGE_RATE_API_URL, timeout=30)
        response.raise_for_status()
        data = response.json()

        serie = data.get("serie", [])

        if not serie:
            raise ValueError("La API de dólar no devolvió datos en 'serie'.")

        dolar = float(serie[0]["valor"])

        logging.info("Valor dólar obtenido correctamente: %s CLP", dolar)
        return dolar

    except Exception as error:
        logging.error("Error al obtener valor del dólar: %s", error)

        fallback_dolar = 950.0
        logging.warning(
            "Se usará valor dólar de respaldo: %s CLP",
            fallback_dolar
        )

        return fallback_dolar


def extract_all_sources() -> dict:
    """
    Ejecuta la extracción de todas las fuentes de datos.
    """
    return {
        "gpu_csv": extract_gpu_csv(),
        "inventory": extract_inventory_db(),
        "gpu_api": extract_gpu_api(),
        "exchange_rate": extract_exchange_rate()
    }


if __name__ == "__main__":
    sources = extract_all_sources()

    print("CSV Kaggle:", sources["gpu_csv"].shape)
    print("Inventario:", sources["inventory"].shape)
    print("API GPUs:", sources["gpu_api"].shape)
    print("Dólar CLP:", sources["exchange_rate"])