import logging

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from models.model_utils import (
    NUMERIC_FEATURES,
    load_final_dataset,
    save_metrics,
    save_model,
)

logging.basicConfig(level="INFO", format="%(asctime)s - %(levelname)s - %(message)s")

# Para clustering se usan specs + precio (sin `gama`, que es la
# etiqueta de negocio contra la que después vamos a comparar).
CLUSTERING_FEATURES = NUMERIC_FEATURES + ["precio_venta_clp"]

K_RANGE = range(2, 9)


def find_best_k(X_scaled) -> tuple[dict, dict]:
    """
    Prueba K=2..8, calcula inertia y silhouette score para cada uno.
    Devuelve (inertias_por_k, silhouettes_por_k).
    """
    inertias = {}
    silhouettes = {}

    for k in K_RANGE:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = kmeans.fit_predict(X_scaled)

        inertias[k] = round(float(kmeans.inertia_), 2)
        silhouettes[k] = round(float(silhouette_score(X_scaled, labels)), 4)

        logging.info(
            "K=%s -> inertia: %s | silhouette: %s", k, inertias[k], silhouettes[k]
        )

    return inertias, silhouettes


def main() -> None:
    logging.info("========== Entrenando modelo de CLUSTERING (mercado) ==========")

    df = load_final_dataset()

    rows_before = len(df)
    df = df[df["tdp_watts"] > 0].reset_index(drop=True)
    logging.info(
        "Filtradas filas con tdp_watts=0 (dato faltante, no real): %s -> %s filas",
        rows_before, len(df)
    )

    X = df[CLUSTERING_FEATURES]

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    inertias, silhouettes = find_best_k(X_scaled)

    # K óptimo = el que maximiza silhouette score (más objetivo que
    # el codo para decidir automáticamente sin inspección visual).
    best_k = max(silhouettes, key=silhouettes.get)
    logging.info("K óptimo elegido por silhouette score: %s", best_k)

    final_kmeans = KMeans(n_clusters=best_k, random_state=42, n_init=10)
    cluster_labels = final_kmeans.fit_predict(X_scaled)

    df["cluster"] = cluster_labels

    # Tabla cruzada cluster vs gama: el análisis crítico central de
    # este modelo (¿coincide el agrupamiento natural con la regla
    # de negocio manual?)
    crosstab = pd.crosstab(df["cluster"], df["gama"])
    logging.info("Tabla cruzada cluster vs gama:\n%s", crosstab)

    # Perfil promedio de cada cluster (para interpretar qué
    # caracteriza a cada grupo en el informe/dashboard)
    cluster_profile = df.groupby("cluster")[CLUSTERING_FEATURES].mean().round(2)

    # K=2 (óptimo por silhouette) separa mayormente "atípicos" vs
    # "resto", lo cual es un hallazgo válido pero poco comparable con
    # las 4 gamas de negocio. Se guarda también K=4 como referencia,
    # para poder comparar directamente cluster natural vs gama en el
    # informe (el análisis crítico que pide la pauta), sin forzar el
    # resultado estadístico principal.
    kmeans_k4 = KMeans(n_clusters=4, random_state=42, n_init=10)
    df["cluster_k4"] = kmeans_k4.fit_predict(X_scaled)
    crosstab_k4 = pd.crosstab(df["cluster_k4"], df["gama"])
    logging.info("Tabla cruzada cluster (K=4) vs gama:\n%s", crosstab_k4)

    pipeline = Pipeline(
        steps=[
            ("scaler", scaler),
            ("model", final_kmeans),
        ]
    )

    final_report = {
        "features_used": CLUSTERING_FEATURES,
        "k_range_tested": list(K_RANGE),
        "inertias_by_k": inertias,
        "silhouettes_by_k": silhouettes,
        "best_k_by_silhouette": best_k,
        "cluster_sizes": df["cluster"].value_counts().sort_index().to_dict(),
        "crosstab_cluster_vs_gama": crosstab.to_dict(),
        "cluster_profile_means": cluster_profile.to_dict(orient="index"),
        "k4_reference": {
            "note": (
                "K=4 no es el óptimo estadístico (silhouette más bajo "
                "que K=2), pero se guarda como referencia para comparar "
                "directamente contra las 4 gamas de negocio."
            ),
            "silhouette": silhouettes[4],
            "crosstab_vs_gama": crosstab_k4.to_dict(),
        },
    }

    save_model(pipeline, "clustering_model")
    save_metrics("clustering", final_report)

    logging.info("========== Entrenamiento de CLUSTERING finalizado ==========")


if __name__ == "__main__":
    main()
