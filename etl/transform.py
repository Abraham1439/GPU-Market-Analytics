import logging
import os
import re

import numpy as np
import pandas as pd
from dotenv import load_dotenv


load_dotenv()

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(levelname)s - %(message)s"
)


def normalize_gpu_name(name: str) -> str:
    """
    Normaliza nombres de GPUs para facilitar cruces entre fuentes.
    """
    if pd.isna(name):
        return ""

    name = str(name).lower()
    for marca in ["nvidia", "amd", "ati", "intel", "geforce", "radeon"]:
        name = name.replace(marca, "")
    name = re.sub(r"[^a-z0-9\s]", " ", name)
    name = re.sub(r"\s+", " ", name).strip()

    return name


def clean_numeric_column(series: pd.Series) -> pd.Series:
    """
    Convierte una columna a numérica eliminando caracteres no válidos.
    """
    return pd.to_numeric(series, errors="coerce")


def prepare_csv_specs(df_csv: pd.DataFrame) -> pd.DataFrame:
    """
    Limpia y selecciona columnas relevantes del CSV de especificaciones.
    """
    logging.info("Preparando datos del CSV de especificaciones")

    columns = [
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

    missing_columns = [col for col in columns if col not in df_csv.columns]

    if missing_columns:
        raise ValueError(f"Faltan columnas obligatorias en CSV: {missing_columns}")

    df = df_csv[columns].copy()

    df = df.rename(
        columns={
            "manufacturer": "marca",
            "productName": "modelo",
            "releaseYear": "anio_lanzamiento",
            "memSize": "memoria_mb",
            "memBusWidth": "bus_memoria_bits",
            "gpuClock": "gpu_clock_mhz",
            "memClock": "mem_clock_mhz",
            "unifiedShader": "shaders",
            "tmu": "tmu",
            "rop": "rop",
            "memType": "tipo_memoria",
            "bus": "bus_interfaz",
            "gpuChip": "chip_gpu"
        }
    )

    numeric_columns = [
        "anio_lanzamiento",
        "memoria_mb",
        "bus_memoria_bits",
        "gpu_clock_mhz",
        "mem_clock_mhz",
        "shaders",
        "tmu",
        "rop"
    ]

    for col in numeric_columns:
        df[col] = clean_numeric_column(df[col])

    df["marca"] = df["marca"].astype(str).str.strip()
    df["modelo"] = df["modelo"].astype(str).str.strip()
    df["tipo_memoria"] = df["tipo_memoria"].fillna("No especificado")
    df["bus_interfaz"] = df["bus_interfaz"].fillna("No especificado")
    df["chip_gpu"] = df["chip_gpu"].fillna("No especificado")

    df = df.dropna(subset=["marca", "modelo", "anio_lanzamiento"])
    df = df.drop_duplicates(subset=["marca", "modelo"], keep="first")

    df["modelo_normalizado"] = df["modelo"].apply(normalize_gpu_name)

    logging.info("CSV preparado. Registros finales: %s", len(df))
    return df


def prepare_inventory(df_inventory: pd.DataFrame) -> pd.DataFrame:
    """
    Limpia datos del inventario simulado.
    """
    logging.info("Preparando inventario de tienda")

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

    missing_columns = [col for col in required_columns if col not in df_inventory.columns]

    if missing_columns:
        raise ValueError(f"Faltan columnas obligatorias en inventario: {missing_columns}")

    df = df_inventory.copy()

    df["marca"] = df["marca"].astype(str).str.strip()
    df["modelo"] = df["modelo"].astype(str).str.strip()
    df["anio_lanzamiento"] = clean_numeric_column(df["anio_lanzamiento"])
    df["stock"] = clean_numeric_column(df["stock"]).fillna(0).astype(int)
    df["precio_venta_clp"] = clean_numeric_column(df["precio_venta_clp"]).fillna(0)

    df["estado"] = df["estado"].fillna("No especificado")
    df["proveedor"] = df["proveedor"].fillna("No especificado")
    df["modelo_normalizado"] = df["modelo"].apply(normalize_gpu_name)

    df = df.dropna(subset=["marca", "modelo", "anio_lanzamiento"])
    df = df[df["stock"] >= 0]
    df = df[df["precio_venta_clp"] >= 0]

    logging.info("Inventario preparado. Registros finales: %s", len(df))
    return df


def prepare_gpu_api(df_api: pd.DataFrame) -> pd.DataFrame:
    """
    Limpia y reduce datos de la API externa de GPUs.

    La API puede venir en formato tradicional o transpuesto.
    Por eso se intenta detectar automáticamente la estructura.
    """
    logging.info("Preparando datos de API externa de GPUs")

    empty_result = pd.DataFrame(
        columns=[
            "modelo_api",
            "modelo_normalizado",
            "precio_msrp_usd",
            "tdp_watts",
            "tflops_api"
        ]
    )

    if df_api.empty:
        logging.warning("La API externa llegó vacía. Se continuará sin datos API.")
        return empty_result

    df = df_api.copy()

    # Caso especial:
    # Si la API viene con demasiadas columnas, probablemente los modelos están como columnas.
    # En ese caso se transpone para dejar cada GPU como una fila.
    if df.shape[1] > 100 and df.shape[0] < df.shape[1]:
        logging.info("Formato de API detectado como transpuesto. Aplicando transpose().")
        df = df.transpose().reset_index()
        df = df.rename(columns={"index": "modelo_api"})

    possible_model_columns = [
        "Model",
        "model",
        "Name",
        "name",
        "Product",
        "product",
        "modelo_api"
    ]

    possible_price_columns = [
        "MSRP (USD)",
        "MSRP USD",
        "MSRP",
        "msrp",
        "Release Price (USD)",
        "Release Price",
        "release_price",
        "Launch Price",
        "Price",
        "price"
    ]

    possible_tdp_columns = [
        "TDP (Watts)",
        "TDP",
        "tdp",
        "TDP (W)",
        "Thermal Design Power"
    ]

    possible_tflops_columns = [
        "Single-precision TFLOPS",
        "FP32",
        "TFLOPS",
        "tflops",
        "Single Precision"
    ]

    def find_column(possible_columns: list[str]) -> str | None:
        """
        Busca una columna por coincidencia exacta o parcial.
        """
        normalized_columns = {
            str(col).lower().strip(): col
            for col in df.columns
        }

        for col in possible_columns:
            key = col.lower().strip()
            if key in normalized_columns:
                return normalized_columns[key]

        for real_col in df.columns:
            real_col_lower = str(real_col).lower()

            for possible in possible_columns:
                if possible.lower() in real_col_lower:
                    return real_col

        return None

    model_col = find_column(possible_model_columns)
    price_col = find_column(possible_price_columns)
    tdp_col = find_column(possible_tdp_columns)
    tflops_col = find_column(possible_tflops_columns)

    if model_col is None:
        logging.warning("No se encontró columna de modelo en la API.")
        logging.info("Primeras columnas disponibles en API: %s", list(df.columns)[:30])
        return empty_result

    df_result = pd.DataFrame()
    df_result["modelo_api"] = df[model_col].astype(str)
    df_result["modelo_normalizado"] = df_result["modelo_api"].apply(normalize_gpu_name)

    if price_col:
        precios = df[price_col].astype(str).str.replace(r"[\$,]", "", regex=True).str.strip()
        df_result["precio_msrp_usd"] = pd.to_numeric(precios, errors="coerce")
    else:
        logging.warning("No se encontró columna de precio MSRP en API.")
        df_result["precio_msrp_usd"] = np.nan

    if tdp_col:
        df_result["tdp_watts"] = clean_numeric_column(df[tdp_col])
    else:
        logging.warning("No se encontró columna de TDP en API.")
        df_result["tdp_watts"] = np.nan

    if tflops_col:
        df_result["tflops_api"] = clean_numeric_column(df[tflops_col])
    else:
        logging.warning("No se encontró columna de TFLOPS en API.")
        df_result["tflops_api"] = np.nan

    df_result = df_result.dropna(subset=["modelo_normalizado"])
    df_result = df_result[df_result["modelo_normalizado"] != ""]
    df_result = df_result.drop_duplicates(subset=["modelo_normalizado"], keep="first")

    logging.info("API preparada. Registros finales: %s", len(df_result))
    return df_result


def classify_gpu_segment(row: pd.Series) -> str:
    """
    Clasifica una GPU en gama de entrada, media, alta o entusiasta.
    """
    memoria_mb = row.get("memoria_mb", 0)
    precio = row.get("precio_venta_clp", 0)

    if pd.isna(memoria_mb):
        memoria_mb = 0

    if pd.isna(precio):
        precio = 0

    if memoria_mb >= 16000 or precio >= 1_200_000:
        return "Entusiasta"

    if memoria_mb >= 10000 or precio >= 700_000:
        return "Gama alta"

    if memoria_mb >= 6000 or precio >= 350_000:
        return "Gama media"

    return "Gama entrada"


def transform_data(
    df_csv: pd.DataFrame,
    df_inventory: pd.DataFrame,
    df_api: pd.DataFrame,
    exchange_rate: float
) -> pd.DataFrame:
    """
    Ejecuta la transformación completa y genera el dataset final.
    """
    logging.info("Iniciando transformación de datos")

    specs = prepare_csv_specs(df_csv)
    inventory = prepare_inventory(df_inventory)
    api = prepare_gpu_api(df_api)

    logging.info("Uniendo inventario con especificaciones técnicas")

    df_final = inventory.merge(
        specs,
        on=["marca", "modelo", "anio_lanzamiento", "modelo_normalizado"],
        how="left",
        suffixes=("_inventario", "_specs")
    )

    logging.info("Uniendo dataset con información de API externa")

    df_final = df_final.merge(
        api,
        on="modelo_normalizado",
        how="left"
    )

    df_final["precio_venta_clp"] = pd.to_numeric(
        df_final["precio_venta_clp"],
        errors="coerce"
    ).fillna(0)

    df_final["precio_msrp_usd"] = pd.to_numeric(
        df_final["precio_msrp_usd"],
        errors="coerce"
    )

    # Si la API no trae MSRP, se estima desde el precio de venta usando el dólar.
    df_final["precio_msrp_usd"] = df_final["precio_msrp_usd"].fillna(
        df_final["precio_venta_clp"] / exchange_rate
    )

    df_final["precio_msrp_clp"] = df_final["precio_msrp_usd"] * exchange_rate
    df_final["valor_total_stock_clp"] = df_final["precio_venta_clp"] * df_final["stock"]
    df_final["diferencia_precio_clp"] = (
        df_final["precio_venta_clp"] - df_final["precio_msrp_clp"]
    )

    df_final["gama"] = df_final.apply(classify_gpu_segment, axis=1)

    df_final["memoria_mb"] = pd.to_numeric(
        df_final["memoria_mb"],
        errors="coerce"
    ).fillna(0)

    df_final["memoria_gb"] = df_final["memoria_mb"] / 1024

    df_final["fuente_tipo_cambio"] = "mindicador.cl"
    df_final["tipo_cambio_usd_clp"] = float(exchange_rate)

    selected_columns = [
        "sku",
        "marca",
        "modelo",
        "anio_lanzamiento",
        "stock",
        "estado",
        "proveedor",
        "precio_venta_clp",
        "precio_msrp_usd",
        "precio_msrp_clp",
        "diferencia_precio_clp",
        "valor_total_stock_clp",
        "gama",
        "memoria_mb",
        "memoria_gb",
        "bus_memoria_bits",
        "gpu_clock_mhz",
        "mem_clock_mhz",
        "shaders",
        "tmu",
        "rop",
        "tipo_memoria",
        "bus_interfaz",
        "chip_gpu",
        "tdp_watts",
        "tflops_api",
        "tipo_cambio_usd_clp",
        "fuente_tipo_cambio"
    ]

    df_final = df_final[selected_columns]

    df_final = df_final.replace([np.inf, -np.inf], np.nan)

    numeric_fill_columns = [
        "anio_lanzamiento",
        "stock",
        "memoria_mb",
        "memoria_gb",
        "bus_memoria_bits",
        "gpu_clock_mhz",
        "mem_clock_mhz",
        "shaders",
        "tmu",
        "rop",
        "tdp_watts",
        "tflops_api"
    ]

    for col in numeric_fill_columns:
        df_final[col] = pd.to_numeric(df_final[col], errors="coerce").fillna(0)

    price_columns = [
        "precio_venta_clp",
        "precio_msrp_usd",
        "precio_msrp_clp",
        "diferencia_precio_clp",
        "valor_total_stock_clp"
    ]

    for col in price_columns:
        df_final[col] = pd.to_numeric(df_final[col], errors="coerce").fillna(0)

    df_final["stock"] = df_final["stock"].astype(int)
    df_final["anio_lanzamiento"] = df_final["anio_lanzamiento"].astype(int)

    text_columns = [
        "sku",
        "marca",
        "modelo",
        "estado",
        "proveedor",
        "gama",
        "tipo_memoria",
        "bus_interfaz",
        "chip_gpu",
        "fuente_tipo_cambio"
    ]

    for col in text_columns:
        df_final[col] = df_final[col].fillna("No especificado").astype(str)

    logging.info("Transformación finalizada. Registros finales: %s", len(df_final))

    return df_final