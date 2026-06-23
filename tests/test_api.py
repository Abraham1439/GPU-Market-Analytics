from fastapi.testclient import TestClient

from api.main import app
from etl.pipeline import main as run_pipeline


client = TestClient(app)


def setup_module():
    """
    Ejecuta el pipeline antes de probar la API.
    """
    run_pipeline()


def test_root_endpoint():
    """
    Verifica que el endpoint principal responda correctamente.
    """
    response = client.get("/")

    assert response.status_code == 200

    data = response.json()

    assert "message" in data
    assert data["message"] == "GPU Market Analytics API"


def test_health_endpoint():
    """
    Verifica que el endpoint de salud encuentre la base de datos.
    """
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["database_exists"] is True
    assert data["table_name"] == "gpu_analytics"


def test_resumen_endpoint():
    """
    Verifica que el resumen entregue indicadores principales.
    """
    response = client.get("/resumen")

    assert response.status_code == 200

    data = response.json()

    assert data["total_gpus"] > 0
    assert data["stock_total"] > 0
    assert data["valor_total_inventario_clp"] > 0


def test_gpus_endpoint():
    """
    Verifica que el endpoint /gpus devuelva datos.
    """
    response = client.get("/gpus?limit=5")

    assert response.status_code == 200

    data = response.json()

    assert "total" in data
    assert "data" in data
    assert data["total"] <= 5
    assert isinstance(data["data"], list)


def test_marcas_endpoint():
    """
    Verifica que el endpoint /marcas devuelva resumen por marca.
    """
    response = client.get("/marcas")

    assert response.status_code == 200

    data = response.json()

    assert "total_marcas" in data
    assert "data" in data
    assert data["total_marcas"] > 0


def test_top_precios_endpoint():
    """
    Verifica que el endpoint /top-precios devuelva ranking de precios.
    """
    response = client.get("/top-precios?limit=5")

    assert response.status_code == 200

    data = response.json()

    assert "total" in data
    assert "data" in data
    assert data["total"] <= 5


def test_inventario_endpoint():
    """
    Verifica que el endpoint /inventario devuelva datos operativos.
    """
    response = client.get("/inventario")

    assert response.status_code == 200

    data = response.json()

    assert "total" in data
    assert "data" in data
    assert data["total"] > 0