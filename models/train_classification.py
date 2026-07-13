import logging

from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)
from sklearn.model_selection import GridSearchCV
from sklearn.pipeline import Pipeline

from models.model_utils import (
    TARGET_CLASSIFICATION,
    build_preprocessor,
    load_final_dataset,
    save_metrics,
    save_model,
    train_test_split_gpu,
)

logging.basicConfig(level="INFO", format="%(asctime)s - %(levelname)s - %(message)s")


def evaluate_classifier(model, X_test, y_test) -> dict:
    """Calcula accuracy, F1 (macro/weighted), reporte y matriz de confusión."""
    y_pred = model.predict(X_test)
    labels = sorted(y_test.unique())

    return {
        "accuracy": round(accuracy_score(y_test, y_pred), 4),
        "f1_macro": round(f1_score(y_test, y_pred, average="macro"), 4),
        "f1_weighted": round(f1_score(y_test, y_pred, average="weighted"), 4),
        "classification_report": classification_report(
            y_test, y_pred, output_dict=True, zero_division=0
        ),
        "confusion_matrix": confusion_matrix(y_test, y_pred, labels=labels).tolist(),
        "confusion_matrix_labels": labels,
    }


def main() -> None:
    logging.info("========== Entrenando modelos de CLASIFICACIÓN (gama) ==========")

    df = load_final_dataset()

    # precio_venta_clp se agrega como feature extra: es información
    # disponible al momento de clasificar (ver docstring del módulo).
    extra_features = ["precio_venta_clp"]

    X_train, X_test, y_train, y_test = train_test_split_gpu(
        df, TARGET_CLASSIFICATION, stratify=True, extra_numeric_features=extra_features
    )

    preprocessor = build_preprocessor(
        target=TARGET_CLASSIFICATION, extra_numeric_features=extra_features
    )

    candidates = {
        "logistic_regression": Pipeline(
            steps=[
                ("preprocessor", preprocessor),
                ("model", LogisticRegression(max_iter=1000)),
            ]
        ),
        "random_forest": Pipeline(
            steps=[
                ("preprocessor", preprocessor),
                ("model", RandomForestClassifier(random_state=42)),
            ]
        ),
    }

    param_grids = {
        "logistic_regression": {
            "model__C": [0.1, 1.0, 10.0],
        },
        "random_forest": {
            "model__n_estimators": [100, 200],
            "model__max_depth": [None, 5, 10],
        },
    }

    results = {}
    trained_pipelines = {}

    for name, pipeline in candidates.items():
        logging.info("Entrenando: %s", name)

        search = GridSearchCV(
            pipeline,
            param_grids[name],
            cv=3,
            scoring="f1_macro",
            n_jobs=-1,
        )
        search.fit(X_train, y_train)
        best_pipeline = search.best_estimator_

        metrics = evaluate_classifier(best_pipeline, X_test, y_test)
        metrics["best_params"] = search.best_params_

        results[name] = metrics
        trained_pipelines[name] = best_pipeline

        logging.info(
            "%s -> Accuracy: %s | F1 macro: %s",
            name, metrics["accuracy"], metrics["f1_macro"]
        )

    # Selecciona el mejor modelo según F1 macro (mejor que accuracy
    # cuando las clases no están perfectamente balanceadas: Entusiasta=42,
    # Gama media=34, Gama alta=29, Gama entrada=15)
    best_model_name = max(results, key=lambda k: results[k]["f1_macro"])
    best_pipeline = trained_pipelines[best_model_name]

    logging.info("Mejor modelo: %s (F1 macro más alto)", best_model_name)

    final_report = {
        "target": TARGET_CLASSIFICATION,
        "best_model": best_model_name,
        "comparison": results,
        "train_rows": len(X_train),
        "test_rows": len(X_test),
        "class_distribution": df[TARGET_CLASSIFICATION].value_counts().to_dict(),
    }

    save_model(best_pipeline, "classification_model")
    save_metrics("classification", final_report)

    logging.info("========== Entrenamiento de CLASIFICACIÓN finalizado ==========")


if __name__ == "__main__":
    main()
