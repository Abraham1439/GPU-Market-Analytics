from pathlib import Path
import logging
import sqlite3
import random
import re

import pandas as pd
import requests
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


def _normalizar_modelo(nombre: str) -> str:
    """Normaliza un nombre de GPU para cruzarlo con la API (igual que en transform)."""
    if pd.isna(nombre):
        return ""
    nombre = str(nombre).lower()
    for marca in ["nvidia", "amd", "ati", "intel", "geforce", "radeon"]:
        nombre = nombre.replace(marca, "")
    nombre = re.sub(r"[^a-z0-9\s]", " ", nombre)
    nombre = re.sub(r"\s+", " ", nombre).strip()
    return nombre


def _gpus_con_precio_en_api() -> set:
    """
    Consulta la API para saber qué GPUs tienen precio MSRP de referencia.
    Si la API falla, devuelve un set vacío (la selección será aleatoria).
    """
    url = os.getenv(
        "GPU_INFO_API_URL",
        "https://raw.githubusercontent.com/voidful/gpu-info-api/gpu-data/gpu.json"
    )
    try:
        data = requests.get(url, timeout=30).json()
    except Exception as error:  # noqa: BLE001
        logging.warning("No se pudo consultar la API para sembrar inventario: %s", error)
        return set()

    df = pd.DataFrame(data).transpose().reset_index()
    if "MSRP (USD)" not in df.columns or "Model" not in df.columns:
        return set()

    precios = df["MSRP (USD)"].astype(str).str.replace(r"[\$,]", "", regex=True).str.strip()
    df["msrp"] = pd.to_numeric(precios, errors="coerce")
    df["key"] = df["Model"].astype(str).apply(_normalizar_modelo)
    return set(df.dropna(subset=["msrp"])["key"])


def create_inventory_dataframe(df_gpus: pd.DataFrame, sample_size: int = 120) -> pd.DataFrame:
    """
    Crea un inventario simulado de tienda a partir del dataset de GPUs.

    Se filtra a GPUs de consumidor de escritorio y se prioriza la selección
    de modelos que SÍ tienen precio de referencia en la API, para que el
    análisis de precios del dashboard tenga datos reales que mostrar.
    """
    df_base = df_gpus[["manufacturer", "productName", "releaseYear"]].copy()

    df_base = df_base.dropna(subset=["manufacturer", "productName", "releaseYear"])
    df_base = df_base.drop_duplicates(subset=["manufacturer", "productName"])

    # Filtro de GPUs de consumidor de escritorio (las que una tienda real vende).
    patron_consumo = r"GeForce (?:GTX|RTX|GT) |Radeon (?:RX|HD|R9|R7) "
    patron_excluir = r"Mobile|OEM|Quadro|FirePro|Tesla|Instinct|IGP|MXM|Xbox|Laptop|Embedded|Max-Q"
    df_base = df_base[df_base["productName"].str.contains(patron_consumo, regex=True, na=False)]
    df_base = df_base[~df_base["productName"].str.contains(patron_excluir, regex=True, na=False)]
    df_base = df_base[df_base["releaseYear"] >= 2008]

    # Siembra API-aware: priorizamos modelos con precio de referencia conocido.
    keys_con_precio = _gpus_con_precio_en_api()
    df_base = df_base.copy()
    df_base["key"] = df_base["productName"].apply(_normalizar_modelo)
    con_precio = df_base[df_base["key"].isin(keys_con_precio)]
    sin_precio = df_base[~df_base["key"].isin(keys_con_precio)]

    partes = []
    if not con_precio.empty:
        n1 = min(int(sample_size * 0.7), len(con_precio))
        partes.append(con_precio.sample(n=n1, random_state=42))
    restante = sample_size - sum(len(p) for p in partes)
    if restante > 0 and not sin_precio.empty:
        n2 = min(restante, len(sin_precio))
        partes.append(sin_precio.sample(n=n2, random_state=42))

    df_inventory = pd.concat(partes).drop(columns=["key"])
    df_inventory = df_inventory.sample(frac=1, random_state=42).reset_index(drop=True)

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