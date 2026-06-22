from pathlib import Path
import logging
import sqlite3
import random

import pandas as pd
from dotenv import load_dotenv
import os


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


def load_gpu_csv(csv_path: Path) -> pd.DataFrame:
    """
    Carga el dataset de GPUs desde un archivo CSV.
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"No se encontró el archivo CSV en: {csv_path}")

    df = pd.read_csv(csv_path)

    required_columns = ["manufacturer", "productName", "releaseYear"]

    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        raise ValueError(f"Faltan columnas obligatorias en el CSV: {missing_columns}")

    return df


def create_inventory_dataframe(df_gpus: pd.DataFrame, sample_size: int = 120) -> pd.DataFrame:
    """
    Crea un inventario simulado de tienda a partir del dataset de GPUs.
    """
    df_base = df_gpus[["manufacturer", "productName", "releaseYear"]].copy()

    df_base = df_base.dropna(subset=["manufacturer", "productName", "releaseYear"])
    df_base = df_base.drop_duplicates(subset=["manufacturer", "productName"])

    if len(df_base) < sample_size:
        sample_size = len(df_base)

    df_inventory = df_base.sample(n=sample_size, random_state=42).reset_index(drop=True)

    condiciones = ["Nuevo", "Usado", "Reacondicionado"]
    proveedores = ["TechImport", "GPUStore Chile", "Andes Hardware", "PC Factory Simulado"]

    random.seed(42)

    df_inventory["stock"] = [random.randint(1, 30) for _ in range(len(df_inventory))]
    df_inventory["estado"] = [random.choice(condiciones) for _ in range(len(df_inventory))]
    df_inventory["proveedor"] = [random.choice(proveedores) for _ in range(len(df_inventory))]

    df_inventory["precio_venta_clp"] = [
        random.randint(120_000, 1_800_000) for _ in range(len(df_inventory))
    ]

    df_inventory["sku"] = [
        f"GPU-{idx + 1:04d}" for idx in range(len(df_inventory))
    ]

    df_inventory = df_inventory.rename(
        columns={
            "manufacturer": "marca",
            "productName": "modelo",
            "releaseYear": "anio_lanzamiento"
        }
    )

    return df_inventory


def save_inventory_to_sqlite(df_inventory: pd.DataFrame, db_path: Path) -> None:
    """
    Guarda el inventario simulado en una base de datos SQLite.
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(db_path) as conn:
        df_inventory.to_sql(
            "inventario_gpu",
            conn,
            if_exists="replace",
            index=False
        )

    logging.info("Inventario guardado correctamente en: %s", db_path)


def main() -> None:
    """
    Ejecuta la creación del inventario simulado.
    """
    logging.info("Iniciando creación de inventario simulado")

    df_gpus = load_gpu_csv(GPU_CSV_PATH)
    df_inventory = create_inventory_dataframe(df_gpus)
    save_inventory_to_sqlite(df_inventory, INVENTORY_DB_PATH)

    logging.info("Proceso finalizado correctamente")
    logging.info("Total de GPUs en inventario: %s", len(df_inventory))


if __name__ == "__main__":
    main()