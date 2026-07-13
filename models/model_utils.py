import json
import logging
import sqlite3
from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler

logging.basicConfig(level="INFO", format="%(asctime)s - %(levelname)s - %(message)s")

ARTIFACTS_DIR = "models/artifacts"

# Columnas objetivo de cada modelo (referencia para los 3 scripts)
#
# TARGET_REGRESSION originalmente era "precio_venta_clp", pero se
# descubrió que ese campo se genera con random.randint() en
# etl/create_inventory.py (no depende de las specs de la GPU), por lo
# que ningún modelo puede predecirlo con señal real (R² negativo en
# las 3 pruebas). Se reemplazó por "tdp_watts" (consumo eléctrico),
# que sí tiene relación física con las specs y cuenta con 83/120
# filas de dato real proveniente de la API (ver train_regression.py
# para el filtro que excluye las filas sin dato real).
TARGET_REGRESSION = "tdp_watts"
TARGET_CLASSIFICATION = "gama"

# Features candidatas (specs técnicas comunes a los 3 modelos)
NUMERIC_FEATURES = [
    "memoria_gb",
    "gpu_clock_mhz",
    "mem_clock_mhz",
    "shaders",
    "tmu",
    "rop",
    "tdp_watts",
    "tflops_api",
    "anio_lanzamiento",
]

# chip_gpu queda fuera a propósito (ver docstring del módulo)
CATEGORICAL_FEATURES = [
    "marca",
    "tipo_memoria",
    "bus_interfaz",
]

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "data" / "database" / "gpu_market_analytics.db"
TABLE_NAME = "gpu_analytics"
ARTIFACTS_PATH = BASE_DIR / ARTIFACTS_DIR

RANDOM_STATE = 42


def load_final_dataset() -> pd.DataFrame:
    """
    Carga el dataset final generado por el pipeline ETL (mismo
    archivo SQLite que usa api/main.py) y aplica una limpieza mínima
    necesaria para que los modelos entrenen bien.
    """
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"No se encontró {DB_PATH}. Ejecuta primero: python -m etl.pipeline"
        )

    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql_query(f"SELECT * FROM {TABLE_NAME}", conn)

    # Normaliza categorías con espacios en blanco (ej. " GDDR6" vs "GDDR6")
    for col in CATEGORICAL_FEATURES:
        df[col] = df[col].astype(str).str.strip()

    logging.info("Dataset cargado: %s filas, %s columnas", len(df), len(df.columns))
    return df


def get_feature_columns() -> tuple[list[str], list[str]]:
    """
    Devuelve las columnas numéricas y categóricas usadas como
    features por los modelos de regresión y clasificación.
    """
    return NUMERIC_FEATURES, CATEGORICAL_FEATURES


def build_preprocessor(
    target: str | None = None,
    extra_numeric_features: list[str] | None = None,
) -> ColumnTransformer:
    """
    ColumnTransformer compartido: StandardScaler para numéricas,
    OneHotEncoder para categóricas. handle_unknown='ignore' evita que
    el pipeline falle si el test set trae una categoría que no
    apareció en train (posible dado que el dataset es pequeño, 120
    filas).

    Si `target` coincide con alguna columna de NUMERIC_FEATURES (caso
    de tdp_watts, que es target en regresión pero feature en
    clasificación), se excluye de las columnas a transformar, porque
    train_test_split_gpu ya la sacó de X.

    `extra_numeric_features` permite sumar columnas numéricas fuera
    de la lista base (caso de precio_venta_clp, que solo se usa como
    feature en clasificación, no en los otros modelos).
    """
    numeric_cols = [c for c in NUMERIC_FEATURES if c != target]
    if extra_numeric_features:
        numeric_cols = numeric_cols + [
            c for c in extra_numeric_features if c != target
        ]
    categorical_cols = [c for c in CATEGORICAL_FEATURES if c != target]

    return ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), numeric_cols),
            (
                "cat",
                OneHotEncoder(handle_unknown="ignore"),
                categorical_cols,
            ),
        ]
    )


def train_test_split_gpu(
    df: pd.DataFrame,
    target: str,
    stratify: bool = False,
    extra_numeric_features: list[str] | None = None,
):
    """
    Wrapper de train_test_split con random_state fijo (reproducible)
    y split 80/20, consistente con el resto del proyecto.

    stratify=True se usa para clasificación, así cada clase de
    `gama` queda representada proporcionalmente en train y test
    (importante porque las clases no están perfectamente balanceadas:
    Entusiasta=42, Gama media=34, Gama alta=29, Gama entrada=15).

    extra_numeric_features permite sumar columnas fuera de la lista
    base compartida (caso de precio_venta_clp en clasificación).
    """
    # Si el target también aparece en la lista de features candidatas
    # (ej. tdp_watts es target de regresión pero feature de
    # clasificación), se excluye automáticamente para evitar leakage.
    feature_cols = [c for c in NUMERIC_FEATURES + CATEGORICAL_FEATURES if c != target]
    if extra_numeric_features:
        feature_cols = feature_cols + [
            c for c in extra_numeric_features if c != target and c not in feature_cols
        ]
    X = df[feature_cols]
    y = df[target]

    stratify_arg = y if stratify else None

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=RANDOM_STATE,
        stratify=stratify_arg,
    )

    logging.info(
        "Split 80/20 -> train: %s filas, test: %s filas", len(X_train), len(X_test)
    )
    return X_train, X_test, y_train, y_test


def save_model(model, name: str) -> Path:
    """
    Guarda un modelo (o Pipeline sklearn completo) serializado en
    models/artifacts/<name>.pkl
    """
    ARTIFACTS_PATH.mkdir(parents=True, exist_ok=True)
    output_path = ARTIFACTS_PATH / f"{name}.pkl"
    joblib.dump(model, output_path)
    logging.info("Modelo guardado en: %s", output_path)
    return output_path


def load_model(name: str):
    """
    Carga un modelo serializado desde models/artifacts/<name>.pkl
    """
    model_path = ARTIFACTS_PATH / f"{name}.pkl"
    if not model_path.exists():
        raise FileNotFoundError(
            f"No se encontró {model_path}. Entrena el modelo primero."
        )
    return joblib.load(model_path)


def save_metrics(name: str, metrics: dict) -> Path:
    """
    Guarda métricas de un modelo como JSON en
    models/artifacts/<name>_metrics.json, para que evaluate.py y la
    API las puedan leer sin tener que reentrenar nada.
    """
    ARTIFACTS_PATH.mkdir(parents=True, exist_ok=True)
    output_path = ARTIFACTS_PATH / f"{name}_metrics.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False, default=str)

    logging.info("Métricas guardadas en: %s", output_path)
    return output_path


def load_metrics(name: str) -> dict:
    """
    Carga métricas guardadas previamente desde
    models/artifacts/<name>_metrics.json
    """
    metrics_path = ARTIFACTS_PATH / f"{name}_metrics.json"
    if not metrics_path.exists():
        raise FileNotFoundError(f"No se encontró {metrics_path}.")

    with open(metrics_path, "r", encoding="utf-8") as f:
        return json.load(f)
