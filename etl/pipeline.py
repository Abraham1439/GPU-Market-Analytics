import logging
import os

from dotenv import load_dotenv

from create_inventory import main as create_inventory_main
from extract import extract_all_sources
from transform import transform_data
from load import load_final_dataset


load_dotenv()

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(levelname)s - %(message)s"
)


def main() -> None:
    """
    Ejecuta el pipeline ETL completo:
    1. Crea inventario simulado.
    2. Extrae datos desde CSV, SQLite y APIs externas.
    3. Transforma y une los datos.
    4. Guarda el dataset final en SQLite y CSV.
    """
    logging.info("========== INICIO PIPELINE ETL ==========")

    logging.info("Paso 1: Creando o actualizando inventario simulado")
    create_inventory_main()

    logging.info("Paso 2: Extrayendo fuentes de datos")
    sources = extract_all_sources()

    logging.info("Paso 3: Transformando datos")
    df_final = transform_data(
        df_csv=sources["gpu_csv"],
        df_inventory=sources["inventory"],
        df_api=sources["gpu_api"],
        exchange_rate=sources["exchange_rate"]
    )

    logging.info("Paso 4: Guardando dataset final")
    load_final_dataset(df_final)

    logging.info("Registros finales generados: %s", len(df_final))
    logging.info("Columnas finales generadas: %s", len(df_final.columns))
    logging.info("========== FIN PIPELINE ETL ==========")


if __name__ == "__main__":
    main()