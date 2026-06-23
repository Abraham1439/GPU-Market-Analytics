from pathlib import Path
import sqlite3

import pandas as pd
import requests
import pytest

from etl.extract import extract_gpu_csv, extract_inventory_db, extract_exchange_rate
from etl.transform import normalize_gpu_name, transform_data
from etl.load import validate_final_dataset
from etl.pipeline import main as run_pipeline


BASE_DIR = Path(__file__).resolve().parents[1]
FINAL_DB_PATH = BASE_DIR / "data" / "database" / "gpu_market_analytics.db"
PROCESSED_CSV_PATH = BASE_DIR / "data" / "processed" / "gpu_market_analytics.csv"


def test_csv_source_exists_and_has_required_columns():
    """
    Verifica que el CSV de GPUs exista y tenga columnas mínimas.
    """
    df = extract_gpu_csv()

    required_columns = [
        "manufacturer",
        "productName",
        "releaseYear",
        "memSize",
        "gpuClock",
        "memType",
    ]

    assert not df.empty

    for column in required_columns:
        assert column in df.columns


def test_normalize_gpu_name():
    """
    Verifica que la normalización de nombres funcione.
    """
    name = "NVIDIA GeForce RTX 4070 Ti"
    normalized = normalize_gpu_name(name)

    assert normalized == "rtx 4070 ti"


def test_pipeline_creates_final_files():
    """
    Ejecuta el pipeline completo y valida que cree los archivos finales.
    """
    run_pipeline()

    assert FINAL_DB_PATH.exists()
    assert PROCESSED_CSV_PATH.exists()


def test_final_sqlite_database_has_data():
    """
    Verifica que la base SQLite final tenga datos en la tabla gpu_analytics.
    """
    if not FINAL_DB_PATH.exists():
        run_pipeline()

    with sqlite3.connect(FINAL_DB_PATH) as conn:
        df = pd.read_sql_query("SELECT * FROM gpu_analytics", conn)

    assert not df.empty
    assert len(df) > 0


def test_final_dataset_has_expected_columns():
    """
    Verifica que el dataset final tenga columnas calculadas importantes.
    """
    if not FINAL_DB_PATH.exists():
        run_pipeline()

    with sqlite3.connect(FINAL_DB_PATH) as conn:
        df = pd.read_sql_query("SELECT * FROM gpu_analytics", conn)

    expected_columns = [
        "sku",
        "marca",
        "modelo",
        "anio_lanzamiento",
        "stock",
        "precio_venta_clp",
        "precio_msrp_usd",
        "precio_msrp_clp",
        "valor_total_stock_clp",
        "gama",
        "tipo_cambio_usd_clp",
    ]

    for column in expected_columns:
        assert column in df.columns


def test_validate_final_dataset_accepts_valid_dataset():
    """
    Verifica que la validación del dataset final no falle con datos correctos.
    """
    if not FINAL_DB_PATH.exists():
        run_pipeline()

    with sqlite3.connect(FINAL_DB_PATH) as conn:
        df = pd.read_sql_query("SELECT * FROM gpu_analytics", conn)

    validate_final_dataset(df)


def test_validate_final_dataset_rejects_empty_dataframe():
    """
    Verifica que la validación rechace un dataset vacío.
    """
    empty_df = pd.DataFrame(columns=["sku", "marca", "modelo"])

    with pytest.raises(ValueError):
        validate_final_dataset(empty_df)


def test_transform_data_handles_empty_inputs():
    """
    Verifica que la transformación no falle ante un DataFrame vacío de entrada.
    """
    empty_csv = pd.DataFrame(columns=["manufacturer", "productName", "releaseYear"])
    inventory = pd.DataFrame(columns=["sku", "marca", "modelo", "anio_lanzamiento"])
    api = pd.DataFrame()

    with pytest.raises(ValueError):
        transform_data(empty_csv, inventory, api, exchange_rate=950.0)

def test_extract_exchange_rate_uses_fallback_on_api_failure(monkeypatch):
    """
    Caso 'API sin respuesta': si la API del dólar falla, debe usar el
    valor de respaldo en vez de lanzar una excepción.
    """
    import etl.extract as extract_module

    def fake_get(*args, **kwargs):
        raise requests.RequestException("API caída (simulada)")

    monkeypatch.setattr(extract_module.requests, "get", fake_get)

    dolar = extract_exchange_rate()

    assert dolar == 950.0


def test_extract_gpu_csv_raises_on_missing_file(monkeypatch):
    """
    Caso 'error de lectura de archivos': si el CSV no existe,
    extract_gpu_csv debe lanzar FileNotFoundError.
    """
    import etl.extract as extract_module

    monkeypatch.setattr(extract_module, "GPU_CSV_PATH", Path("ruta/que/no/existe.csv"))

    with pytest.raises(FileNotFoundError):
        extract_gpu_csv()