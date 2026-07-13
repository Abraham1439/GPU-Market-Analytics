"""
Tests de los endpoints de Machine Learning de la API
(/predict/tdp, /predict/gama, /clusters/summary, /clusters/gpus,
/models/info).

Se entrenan los 3 modelos en setup_module() antes de correr los
tests, igual que test_api.py corre el pipeline ETL antes de probar
la API.
"""

from fastapi.testclient import TestClient

from api.main import app
from etl.pipeline import main as run_pipeline
from models.train_classification import main as train_classification
from models.train_clustering import main as train_clustering
from models.train_regression import main as train_regression


client = TestClient(app)

VALID_TDP_PAYLOAD = {
    "marca": "NVIDIA",
    "tipo_memoria": "GDDR6",
    "bus_interfaz": "PCIe 4.0 x16",
    "memoria_gb": 8.0,
    "bus_memoria_bits": 256.0,
    "gpu_clock_mhz": 1500.0,
    "mem_clock_mhz": 14000.0,
    "shaders": 4000.0,
    "tmu": 200.0,
    "rop": 80.0,
    "anio_lanzamiento": 2023,
}


def setup_module():
    """
    Ejecuta el pipeline ETL y entrena los 3 modelos antes de probar
    los endpoints de ML.
    """
    run_pipeline()
    train_regression()
    train_classification()
    train_clustering()


def test_predict_tdp_endpoint():
    """
    Verifica que /predict/tdp devuelva una predicción numérica
    razonable junto con las métricas del modelo usado.
    """
    response = client.post("/predict/tdp", json=VALID_TDP_PAYLOAD)

    assert response.status_code == 200

    data = response.json()

    assert "tdp_watts_predicho" in data
    assert data["tdp_watts_predicho"] > 0
    assert "modelo_usado" in data
    assert "r2_modelo" in data


def test_predict_gama_endpoint_auto_tdp():
    """
    Verifica que /predict/gama funcione sin entregar tdp_watts,
    estimándolo automáticamente con el modelo de regresión.
    """
    payload = {**VALID_TDP_PAYLOAD, "precio_venta_clp": 900000}

    response = client.post("/predict/gama", json=payload)

    assert response.status_code == 200

    data = response.json()

    assert data["gama_predicha"] in [
        "Gama entrada", "Gama media", "Gama alta", "Entusiasta"
    ]
    assert data["tdp_estimado_automaticamente"] is True
    assert data["probabilidades_por_clase"] is not None


def test_predict_gama_endpoint_manual_tdp():
    """
    Verifica que /predict/gama respete un tdp_watts entregado
    manualmente en vez de estimarlo.
    """
    payload = {**VALID_TDP_PAYLOAD, "precio_venta_clp": 900000, "tdp_watts": 220}

    response = client.post("/predict/gama", json=payload)

    assert response.status_code == 200

    data = response.json()

    assert data["tdp_estimado_automaticamente"] is False
    assert data["tdp_watts_usado"] == 220.0


def test_clusters_summary_endpoint():
    """
    Verifica que /clusters/summary entregue el K óptimo, tamaños de
    cluster y la comparación contra las gamas de negocio.
    """
    response = client.get("/clusters/summary")

    assert response.status_code == 200

    data = response.json()

    assert "k_optimo_por_silhouette" in data
    assert "tamano_clusters" in data
    assert "comparacion_vs_gama" in data
    assert "referencia_k4" in data


def test_clusters_gpus_endpoint():
    """
    Verifica que /clusters/gpus asigne un cluster a cada GPU del
    inventario, y que el filtro por cluster funcione.
    """
    response = client.get("/clusters/gpus")

    assert response.status_code == 200

    data = response.json()

    assert data["total"] > 0
    assert all("cluster" in row for row in data["data"])

    first_cluster = data["data"][0]["cluster"]
    filtered = client.get(f"/clusters/gpus?cluster={first_cluster}")

    assert filtered.status_code == 200
    assert all(row["cluster"] == first_cluster for row in filtered.json()["data"])


def test_models_info_endpoint():
    """
    Verifica que /models/info devuelva el estado de los 3 modelos.
    """
    response = client.get("/models/info")

    assert response.status_code == 200

    data = response.json()

    assert set(data.keys()) == {"regression", "classification", "clustering"}
    assert "best_model" in data["regression"]
    assert "best_model" in data["classification"]
