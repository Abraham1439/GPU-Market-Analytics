import logging

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from models.model_utils import ARTIFACTS_PATH, load_metrics

logging.basicConfig(level="INFO", format="%(asctime)s - %(levelname)s - %(message)s")

FIGURES_PATH = ARTIFACTS_PATH / "figures"


def build_comparison_table() -> pd.DataFrame:
    """
    Consolida las métricas de los 3 modelos en una sola tabla,
    lista para pegar en el informe ejecutivo.
    """
    rows = []

    reg = load_metrics("regression")
    for algo, m in reg["comparison"].items():
        rows.append({
            "modelo": "Regresión (TDP)",
            "algoritmo": algo,
            "metrica_principal": f"MAE = {m['mae_watts']} W",
            "metrica_secundaria": f"R² = {m['r2']}",
            "es_el_mejor": algo == reg["best_model"],
        })

    clf = load_metrics("classification")
    for algo, m in clf["comparison"].items():
        rows.append({
            "modelo": "Clasificación (gama)",
            "algoritmo": algo,
            "metrica_principal": f"Accuracy = {m['accuracy']}",
            "metrica_secundaria": f"F1 macro = {m['f1_macro']}",
            "es_el_mejor": algo == clf["best_model"],
        })

    clu = load_metrics("clustering")
    rows.append({
        "modelo": "Clustering (mercado)",
        "algoritmo": f"KMeans (K={clu['best_k_by_silhouette']})",
        "metrica_principal": f"Silhouette = {clu['silhouettes_by_k'][str(clu['best_k_by_silhouette'])]}",
        "metrica_secundaria": f"K probados: {clu['k_range_tested']}",
        "es_el_mejor": True,
    })

    return pd.DataFrame(rows)


def plot_feature_importance() -> None:
    """Gráfico de barras con el top 10 de features del modelo de regresión."""
    reg = load_metrics("regression")
    importance = reg.get("feature_importance_top10", {})
    if not importance:
        logging.warning("No hay feature_importance guardado, se omite el gráfico.")
        return

    fig, ax = plt.subplots(figsize=(8, 5))
    names = list(importance.keys())
    values = list(importance.values())
    sns.barplot(x=values, y=names, ax=ax, color="#4C72B0")
    ax.set_title(f"Importancia de features — Regresión TDP ({reg['best_model']})")
    ax.set_xlabel("Importancia")
    fig.tight_layout()

    FIGURES_PATH.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURES_PATH / "regression_feature_importance.png", dpi=150)
    plt.close(fig)
    logging.info("Gráfico guardado: regression_feature_importance.png")


def plot_confusion_matrix() -> None:
    """Matriz de confusión del mejor modelo de clasificación."""
    clf = load_metrics("classification")
    best = clf["comparison"][clf["best_model"]]
    matrix = best["confusion_matrix"]
    labels = best["confusion_matrix_labels"]

    fig, ax = plt.subplots(figsize=(6, 5))
    sns.heatmap(matrix, annot=True, fmt="d", cmap="Blues",
                xticklabels=labels, yticklabels=labels, ax=ax)
    ax.set_title(f"Matriz de confusión — Clasificación gama ({clf['best_model']})")
    ax.set_xlabel("Predicho")
    ax.set_ylabel("Real")
    fig.tight_layout()

    FIGURES_PATH.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURES_PATH / "classification_confusion_matrix.png", dpi=150)
    plt.close(fig)
    logging.info("Gráfico guardado: classification_confusion_matrix.png")


def plot_elbow_and_silhouette() -> None:
    """Gráfico de codo (inertia) + silhouette score por K, lado a lado."""
    clu = load_metrics("clustering")
    ks = clu["k_range_tested"]
    inertias = [clu["inertias_by_k"][str(k)] for k in ks]
    silhouettes = [clu["silhouettes_by_k"][str(k)] for k in ks]

    fig, axes = plt.subplots(1, 2, figsize=(11, 4))

    axes[0].plot(ks, inertias, marker="o", color="#4C72B0")
    axes[0].set_title("Método del codo")
    axes[0].set_xlabel("K")
    axes[0].set_ylabel("Inertia")

    axes[1].plot(ks, silhouettes, marker="o", color="#DD8452")
    best_k = clu["best_k_by_silhouette"]
    axes[1].axvline(best_k, color="gray", linestyle="--", alpha=0.6)
    axes[1].set_title(f"Silhouette score (mejor K={best_k})")
    axes[1].set_xlabel("K")
    axes[1].set_ylabel("Silhouette")

    fig.tight_layout()
    FIGURES_PATH.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURES_PATH / "clustering_elbow_silhouette.png", dpi=150)
    plt.close(fig)
    logging.info("Gráfico guardado: clustering_elbow_silhouette.png")


def main() -> None:
    logging.info("========== Generando comparación consolidada ==========")

    table = build_comparison_table()
    print("\n" + table.to_string(index=False) + "\n")

    table_path = ARTIFACTS_PATH / "comparison_table.csv"
    table.to_csv(table_path, index=False)
    logging.info("Tabla comparativa guardada en: %s", table_path)

    plot_feature_importance()
    plot_confusion_matrix()
    plot_elbow_and_silhouette()

    logging.info("========== Comparación consolidada finalizada ==========")


if __name__ == "__main__":
    main()
