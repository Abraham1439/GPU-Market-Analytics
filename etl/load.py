from pathlib import Path
import logging
import os
import sqlite3

import pandas as pd
from dotenv import load_dotenv


load_dotenv()

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(levelname)s - %(message)s"
)

BASE_DIR = Path(__file__).resolve().parents[1]

FINAL_DB_PATH = BASE_DIR / os.getenv(
    "FINAL_DB_PATH",
    "data/database/gpu_market_analytics.db"
)

PROCESSED_DIR = BASE_DIR / os.getenv(
    "PROCESSED_DIR",
    "data/processed"
)


def validate_final_dataset(df: pd.DataFrame) -> None:
    """
    Valida que el dataset final tenga las columnas mínimas necesarias.
    """
    required_columns = [
        "sku",
        "marca",
        "modelo",
        "anio_lanzamiento",
        "stock",
        "precio_venta_clp",
        "precio_msrp_usd",
        "precio_msrp_clp",
        "valor_total_stock_clp",
        "gama"
    ]

    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        raise ValueError(
            f"El dataset final no tiene las columnas obligatorias: {missing_columns}"
        )

    if df.empty:
        raise ValueError("El dataset final está vacío. No se puede guardar.")


def save_to_sqlite(df: pd.DataFrame, db_path: Path = FINAL_DB_PATH) -> None:
    """
    Guarda el dataset final en una base SQLite.
    """
    validate_final_dataset(df)

    db_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(db_path) as conn:
        df.to_sql(
            "gpu_analytics",
            conn,
            if_exists="replace",
            index=False
        )

    logging.info("Dataset final guardado en SQLite: %s", db_path)


def save_to_csv(df: pd.DataFrame, processed_dir: Path = PROCESSED_DIR) -> Path:
    """
    Guarda el dataset final como CSV procesado.
    """
    validate_final_dataset(df)

    processed_dir.mkdir(parents=True, exist_ok=True)

    output_path = processed_dir / "gpu_market_analytics.csv"

    df.to_csv(output_path, index=False, encoding="utf-8")

    logging.info("Dataset final guardado en CSV: %s", output_path)

    return output_path


def load_final_dataset(df: pd.DataFrame) -> None:
    """
    Ejecuta la carga completa del dataset final.
    """
    logging.info("Iniciando carga del dataset final")

    save_to_sqlite(df)
    save_to_csv(df)

    logging.info("Carga finalizada correctamente")