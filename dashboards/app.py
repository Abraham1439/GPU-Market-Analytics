import sys
from pathlib import Path
import sqlite3

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "data" / "database" / "gpu_market_analytics.db"

# Necesario para poder hacer "from models.model_utils import ..." sin
# importar que streamlit se ejecute desde otra carpeta.
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from models.model_utils import load_metrics, load_model  # noqa: E402


st.set_page_config(
    page_title="GPU Market Analytics",
    page_icon="🎮",
    layout="wide"
)


@st.cache_data
def load_data() -> pd.DataFrame:
    """
    Carga los datos procesados desde SQLite.
    """
    if not DB_PATH.exists():
        st.error(
            "No se encontró la base de datos final. "
            "Ejecuta primero: python -m etl.pipeline"
        )
        return pd.DataFrame()

    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql_query("SELECT * FROM gpu_analytics", conn)

    return df


@st.cache_resource
def load_ml_models():
    """
    Carga los 3 modelos entrenados (una sola vez, cacheados) y sus
    métricas. Si alguno no está entrenado, se marca como None y la
    vista de ML lo indica con instrucciones para entrenarlo.
    """
    models = {}
    metrics = {}

    for name, model_key in [
        ("regression", "regression_model"),
        ("classification", "classification_model"),
        ("clustering", "clustering_model"),
    ]:
        try:
            models[name] = load_model(model_key)
            metrics[name] = load_metrics(name)
        except FileNotFoundError:
            models[name] = None
            metrics[name] = None

    return models, metrics


def format_clp(value: float) -> str:
    """
    Formatea valores monetarios en pesos chilenos.
    """
    return f"${value:,.0f}".replace(",", ".")


def apply_filters(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica filtros interactivos desde la barra lateral.
    """
    st.sidebar.header("Filtros")

    marcas = sorted(df["marca"].dropna().unique())
    gamas = sorted(df["gama"].dropna().unique())
    tipos_memoria = sorted(df["tipo_memoria"].dropna().unique())

    selected_marcas = st.sidebar.multiselect(
        "Marca",
        marcas,
        default=marcas
    )

    selected_gamas = st.sidebar.multiselect(
        "Gama",
        gamas,
        default=gamas
    )

    selected_tipos_memoria = st.sidebar.multiselect(
        "Tipo de memoria",
        tipos_memoria,
        default=tipos_memoria
    )

    min_year = int(df["anio_lanzamiento"].min())
    max_year = int(df["anio_lanzamiento"].max())

    selected_years = st.sidebar.slider(
        "Rango de año de lanzamiento",
        min_value=min_year,
        max_value=max_year,
        value=(min_year, max_year)
    )

    filtered_df = df[
        (df["marca"].isin(selected_marcas)) &
        (df["gama"].isin(selected_gamas)) &
        (df["tipo_memoria"].isin(selected_tipos_memoria)) &
        (df["anio_lanzamiento"].between(selected_years[0], selected_years[1]))
    ]

    return filtered_df


def executive_view(df: pd.DataFrame) -> None:
    """
    Vista ejecutiva orientada a indicadores de negocio.
    """
    st.subheader("Vista ejecutiva")

    total_inventory_value = df["valor_total_stock_clp"].sum()
    total_stock = df["stock"].sum()
    avg_price = df["precio_venta_clp"].mean()
    total_models = df["modelo"].nunique()

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Valor total inventario", format_clp(total_inventory_value))
    col2.metric("Stock total", f"{total_stock:,.0f}".replace(",", "."))
    col3.metric("Precio promedio", format_clp(avg_price))
    col4.metric("Modelos únicos", total_models)

    st.markdown("### Valor de inventario por marca")

    value_by_brand = (
        df.groupby("marca", as_index=False)["valor_total_stock_clp"]
        .sum()
        .sort_values("valor_total_stock_clp", ascending=False)
    )

    fig_brand_value = px.bar(
        value_by_brand,
        x="marca",
        y="valor_total_stock_clp",
        title="Valor total del inventario por marca",
        labels={
            "marca": "Marca",
            "valor_total_stock_clp": "Valor total inventario CLP"
        }
    )

    st.plotly_chart(fig_brand_value, use_container_width=True)

    st.markdown("### Top 10 GPUs con mayor precio de venta")

    top_prices = df.sort_values("precio_venta_clp", ascending=False).head(10)

    fig_top_prices = px.bar(
        top_prices,
        x="modelo",
        y="precio_venta_clp",
        color="marca",
        title="Top 10 tarjetas gráficas más caras",
        labels={
            "modelo": "Modelo",
            "precio_venta_clp": "Precio venta CLP",
            "marca": "Marca"
        }
    )

    st.plotly_chart(fig_top_prices, use_container_width=True)


def technical_view(df: pd.DataFrame) -> None:
    """
    Vista técnica orientada a especificaciones de hardware.
    """
    st.subheader("Vista técnica")

    col1, col2 = st.columns(2)

    memory_by_year = (
        df.groupby("anio_lanzamiento", as_index=False)["memoria_gb"]
        .mean()
        .sort_values("anio_lanzamiento")
    )

    fig_memory_year = px.line(
        memory_by_year,
        x="anio_lanzamiento",
        y="memoria_gb",
        markers=True,
        title="Memoria promedio por año de lanzamiento",
        labels={
            "anio_lanzamiento": "Año",
            "memoria_gb": "Memoria promedio GB"
        }
    )

    col1.plotly_chart(fig_memory_year, use_container_width=True)

    fig_memory_price = px.scatter(
        df,
        x="memoria_gb",
        y="precio_venta_clp",
        color="marca",
        size="stock",
        hover_data=["modelo", "gama", "anio_lanzamiento"],
        title="Relación entre memoria y precio de venta",
        labels={
            "memoria_gb": "Memoria GB",
            "precio_venta_clp": "Precio venta CLP"
        }
    )

    col2.plotly_chart(fig_memory_price, use_container_width=True)

    st.markdown("### Distribución por tipo de memoria")

    memory_type_count = (
        df.groupby("tipo_memoria", as_index=False)
        .size()
        .sort_values("size", ascending=False)
    )

    fig_memory_type = px.bar(
        memory_type_count,
        x="tipo_memoria",
        y="size",
        title="Cantidad de GPUs por tipo de memoria",
        labels={
            "tipo_memoria": "Tipo de memoria",
            "size": "Cantidad"
        }
    )

    st.plotly_chart(fig_memory_type, use_container_width=True)

    st.markdown("### Comparación técnica por marca")

    technical_by_brand = (
        df.groupby("marca", as_index=False)
        .agg({
            "memoria_gb": "mean",
            "gpu_clock_mhz": "mean",
            "shaders": "mean",
            "precio_venta_clp": "mean"
        })
    )

    st.dataframe(
        technical_by_brand,
        use_container_width=True
    )


def operational_view(df: pd.DataFrame) -> None:
    """
    Vista operativa orientada a gestión de stock de tienda.
    """
    st.subheader("Vista operativa")

    col1, col2 = st.columns(2)

    stock_by_brand = (
        df.groupby("marca", as_index=False)["stock"]
        .sum()
        .sort_values("stock", ascending=False)
    )

    fig_stock_brand = px.bar(
        stock_by_brand,
        x="marca",
        y="stock",
        title="Stock total por marca",
        labels={
            "marca": "Marca",
            "stock": "Stock disponible"
        }
    )

    col1.plotly_chart(fig_stock_brand, use_container_width=True)

    stock_by_status = (
        df.groupby("estado", as_index=False)["stock"]
        .sum()
        .sort_values("stock", ascending=False)
    )

    fig_stock_status = px.pie(
        stock_by_status,
        values="stock",
        names="estado",
        title="Distribución del stock por estado"
    )

    col2.plotly_chart(fig_stock_status, use_container_width=True)

    st.markdown("### Productos con bajo stock")

    low_stock = df[df["stock"] <= 5].sort_values("stock")

    if low_stock.empty:
        st.success("No hay productos con bajo stock según el filtro actual.")
    else:
        st.dataframe(
            low_stock[
                [
                    "sku",
                    "marca",
                    "modelo",
                    "stock",
                    "estado",
                    "proveedor",
                    "precio_venta_clp",
                    "valor_total_stock_clp"
                ]
            ],
            use_container_width=True
        )

    st.markdown("### Inventario detallado")

    st.dataframe(
        df[
            [
                "sku",
                "marca",
                "modelo",
                "anio_lanzamiento",
                "gama",
                "stock",
                "estado",
                "proveedor",
                "precio_venta_clp",
                "valor_total_stock_clp"
            ]
        ],
        use_container_width=True
    )


def regression_subview(df: pd.DataFrame, model, metrics: dict) -> None:
    """
    Sub-vista de regresión: predicción de consumo eléctrico (TDP).
    """
    st.markdown("#### Regresión — Predicción de consumo eléctrico (TDP)")

    best_model_name = metrics["best_model"]
    best_metrics = metrics["comparison"][best_model_name]

    col1, col2, col3 = st.columns(3)
    col1.metric("Modelo ganador", best_model_name)
    col2.metric("MAE", f"{best_metrics['mae_watts']} W")
    col3.metric("R²", best_metrics["r2"])

    st.markdown("##### Comparación de algoritmos")

    comparison_rows = [
        {
            "algoritmo": name,
            "MAE (W)": m["mae_watts"],
            "RMSE (W)": m["rmse_watts"],
            "R²": m["r2"],
        }
        for name, m in metrics["comparison"].items()
    ]
    st.dataframe(pd.DataFrame(comparison_rows), use_container_width=True)

    feature_importance = metrics.get("feature_importance_top10", {})
    if feature_importance:
        st.markdown("##### Importancia de features")
        fig = px.bar(
            x=list(feature_importance.values()),
            y=list(feature_importance.keys()),
            orientation="h",
            labels={"x": "Importancia", "y": "Feature"},
        )
        fig.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("##### Probar el modelo")
    st.caption("Ingresa las specs de una GPU y predice su consumo eléctrico estimado.")

    with st.form("form_predict_tdp"):
        c1, c2, c3 = st.columns(3)
        marca = c1.selectbox("Marca", sorted(df["marca"].dropna().unique()))
        tipo_memoria = c2.selectbox("Tipo de memoria", sorted(df["tipo_memoria"].dropna().unique()))
        bus_interfaz = c3.selectbox("Bus / interfaz", sorted(df["bus_interfaz"].dropna().unique()))

        c4, c5, c6 = st.columns(3)
        memoria_gb = c4.number_input("Memoria (GB)", min_value=0.0, value=8.0, step=1.0)
        bus_memoria_bits = c5.number_input("Bus de memoria (bits)", min_value=0.0, value=256.0, step=32.0)
        anio_lanzamiento = c6.number_input("Año de lanzamiento", min_value=1990, max_value=2030, value=2023)

        c7, c8, c9 = st.columns(3)
        gpu_clock_mhz = c7.number_input("Clock GPU (MHz)", min_value=0.0, value=1500.0, step=50.0)
        mem_clock_mhz = c8.number_input("Clock memoria (MHz)", min_value=0.0, value=14000.0, step=100.0)
        shaders = c9.number_input("Shaders", min_value=0.0, value=4000.0, step=100.0)

        c10, c11 = st.columns(2)
        tmu = c10.number_input("TMU", min_value=0.0, value=200.0, step=10.0)
        rop = c11.number_input("ROP", min_value=0.0, value=80.0, step=5.0)

        submitted = st.form_submit_button("Predecir TDP")

    if submitted:
        input_df = pd.DataFrame([{
            "marca": marca,
            "tipo_memoria": tipo_memoria,
            "bus_interfaz": bus_interfaz,
            "memoria_gb": memoria_gb,
            "bus_memoria_bits": bus_memoria_bits,
            "gpu_clock_mhz": gpu_clock_mhz,
            "mem_clock_mhz": mem_clock_mhz,
            "shaders": shaders,
            "tmu": tmu,
            "rop": rop,
            "anio_lanzamiento": anio_lanzamiento,
            "tflops_api": 0.0,
        }])
        prediction = model.predict(input_df)[0]
        st.success(f"Consumo eléctrico estimado: **{prediction:.1f} W**")


def classification_subview(df: pd.DataFrame, model, metrics: dict) -> None:
    """
    Sub-vista de clasificación: predicción de gama.
    """
    st.markdown("#### Clasificación — Predicción de gama")

    st.info(
        "`gama` se calcula combinando specs técnicas y precio de venta. "
        "El precio se incluye como feature porque es información disponible "
        "al catalogar un producto nuevo (ver docs/api.md para el detalle)."
    )

    best_model_name = metrics["best_model"]
    best_metrics = metrics["comparison"][best_model_name]

    col1, col2, col3 = st.columns(3)
    col1.metric("Modelo ganador", best_model_name)
    col2.metric("Accuracy", best_metrics["accuracy"])
    col3.metric("F1 macro", best_metrics["f1_macro"])

    st.markdown("##### Comparación de algoritmos")

    comparison_rows = [
        {
            "algoritmo": name,
            "Accuracy": m["accuracy"],
            "F1 macro": m["f1_macro"],
            "F1 weighted": m["f1_weighted"],
        }
        for name, m in metrics["comparison"].items()
    ]
    st.dataframe(pd.DataFrame(comparison_rows), use_container_width=True)

    st.markdown("##### Matriz de confusión")

    conf_matrix = best_metrics["confusion_matrix"]
    labels = best_metrics["confusion_matrix_labels"]

    fig = px.imshow(
        conf_matrix,
        x=labels,
        y=labels,
        text_auto=True,
        color_continuous_scale="Blues",
        labels={"x": "Predicho", "y": "Real", "color": "Cantidad"},
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("##### Probar el modelo")
    st.caption("Ingresa las specs + precio de una GPU y predice su gama.")

    with st.form("form_predict_gama"):
        c1, c2, c3 = st.columns(3)
        marca = c1.selectbox("Marca", sorted(df["marca"].dropna().unique()), key="gama_marca")
        tipo_memoria = c2.selectbox("Tipo de memoria", sorted(df["tipo_memoria"].dropna().unique()), key="gama_tipo_mem")
        bus_interfaz = c3.selectbox("Bus / interfaz", sorted(df["bus_interfaz"].dropna().unique()), key="gama_bus")

        c4, c5, c6 = st.columns(3)
        memoria_gb = c4.number_input("Memoria (GB)", min_value=0.0, value=8.0, step=1.0, key="gama_mem_gb")
        bus_memoria_bits = c5.number_input("Bus de memoria (bits)", min_value=0.0, value=256.0, step=32.0, key="gama_bus_bits")
        anio_lanzamiento = c6.number_input("Año de lanzamiento", min_value=1990, max_value=2030, value=2023, key="gama_anio")

        c7, c8, c9 = st.columns(3)
        gpu_clock_mhz = c7.number_input("Clock GPU (MHz)", min_value=0.0, value=1500.0, step=50.0, key="gama_gpu_clock")
        mem_clock_mhz = c8.number_input("Clock memoria (MHz)", min_value=0.0, value=14000.0, step=100.0, key="gama_mem_clock")
        shaders = c9.number_input("Shaders", min_value=0.0, value=4000.0, step=100.0, key="gama_shaders")

        c10, c11, c12 = st.columns(3)
        tmu = c10.number_input("TMU", min_value=0.0, value=200.0, step=10.0, key="gama_tmu")
        rop = c11.number_input("ROP", min_value=0.0, value=80.0, step=5.0, key="gama_rop")
        precio_venta_clp = c12.number_input("Precio de venta (CLP)", min_value=0.0, value=900000.0, step=10000.0, key="gama_precio")

        auto_tdp = st.checkbox("Estimar TDP automáticamente con el modelo de regresión", value=True)
        tdp_manual = None
        if not auto_tdp:
            tdp_manual = st.number_input("TDP (W)", min_value=0.0, value=220.0, step=5.0)

        submitted = st.form_submit_button("Predecir gama")

    if submitted:
        base_specs = {
            "marca": marca,
            "tipo_memoria": tipo_memoria,
            "bus_interfaz": bus_interfaz,
            "memoria_gb": memoria_gb,
            "bus_memoria_bits": bus_memoria_bits,
            "gpu_clock_mhz": gpu_clock_mhz,
            "mem_clock_mhz": mem_clock_mhz,
            "shaders": shaders,
            "tmu": tmu,
            "rop": rop,
            "anio_lanzamiento": anio_lanzamiento,
            "tflops_api": 0.0,
        }

        models, all_metrics = load_ml_models()

        if auto_tdp:
            if models["regression"] is None:
                st.error("El modelo de regresión no está entrenado, no se puede autoestimar el TDP.")
                st.stop()
            tdp_value = float(models["regression"].predict(pd.DataFrame([base_specs]))[0])
        else:
            tdp_value = tdp_manual

        input_df = pd.DataFrame([{
            **base_specs,
            "tdp_watts": tdp_value,
            "precio_venta_clp": precio_venta_clp,
        }])

        prediction = model.predict(input_df)[0]

        st.success(f"Gama predicha: **{prediction}** (TDP usado: {tdp_value:.1f} W)")

        if hasattr(model, "predict_proba"):
            proba = model.predict_proba(input_df)[0]
            classes = model.named_steps["model"].classes_
            proba_df = pd.DataFrame({"gama": classes, "probabilidad": proba}).sort_values(
                "probabilidad", ascending=False
            )
            fig = px.bar(proba_df, x="gama", y="probabilidad", title="Probabilidad por clase")
            st.plotly_chart(fig, use_container_width=True)


def clustering_subview(df: pd.DataFrame, model, metrics: dict) -> None:
    """
    Sub-vista de clustering: segmentación de mercado no supervisada.
    """
    st.markdown("#### Clustering — Segmentación de mercado")

    best_k = metrics["best_k_by_silhouette"]
    best_silhouette = metrics["silhouettes_by_k"][str(best_k)]

    col1, col2 = st.columns(2)
    col1.metric("K óptimo (silhouette)", best_k)
    col2.metric("Silhouette score", best_silhouette)

    st.warning(
        "**Hallazgo clave:** los clusters formados a partir de las specs "
        "técnicas reales NO coinciden con las 4 gamas de negocio definidas "
        "manualmente. Esto confirma que `gama` está dominada por el precio "
        "aleatorio del inventario simulado, no por las especificaciones "
        "técnicas de cada GPU (ver models/train_clustering.py)."
    )

    st.markdown("##### Método del codo y silhouette score por K")

    ks = metrics["k_range_tested"]
    inertias = [metrics["inertias_by_k"][str(k)] for k in ks]
    silhouettes = [metrics["silhouettes_by_k"][str(k)] for k in ks]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ks, y=inertias, name="Inertia", yaxis="y1"))
    fig.add_trace(go.Scatter(x=ks, y=silhouettes, name="Silhouette", yaxis="y2"))
    fig.update_layout(
        xaxis_title="K",
        yaxis=dict(title="Inertia", side="left"),
        yaxis2=dict(title="Silhouette", side="right", overlaying="y"),
        legend=dict(orientation="h"),
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("##### Comparación cluster natural vs gama de negocio")

    crosstab = pd.DataFrame(metrics["crosstab_cluster_vs_gama"]).fillna(0)
    fig = px.imshow(
        crosstab.T,
        text_auto=True,
        color_continuous_scale="Blues",
        labels={"x": "Cluster", "y": "Gama", "color": "Cantidad"},
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("##### Perfil promedio por cluster")
    profile = pd.DataFrame(metrics["cluster_profile_means"]).T
    st.dataframe(profile, use_container_width=True)

    st.markdown("##### Mapa de clusters vs gama (specs reales)")
    st.caption(
        "Comparación visual: a la izquierda, agrupamiento según specs reales "
        "(cluster). A la derecha, la misma GPU coloreada por su gama de negocio."
    )

    from models.train_clustering import CLUSTERING_FEATURES

    df_clustered = df.copy()
    df_clustered["cluster"] = model.predict(df_clustered[CLUSTERING_FEATURES]).astype(str)

    c1, c2 = st.columns(2)

    fig_cluster = px.scatter(
        df_clustered,
        x="memoria_gb",
        y="precio_venta_clp",
        color="cluster",
        hover_data=["modelo", "gama"],
        title="Coloreado por cluster (specs reales)",
    )
    c1.plotly_chart(fig_cluster, use_container_width=True)

    fig_gama = px.scatter(
        df_clustered,
        x="memoria_gb",
        y="precio_venta_clp",
        color="gama",
        hover_data=["modelo", "cluster"],
        title="Coloreado por gama (regla de negocio)",
    )
    c2.plotly_chart(fig_gama, use_container_width=True)


def ml_view(df: pd.DataFrame) -> None:
    """
    Vista de Machine Learning: portafolio de 3 modelos (regresión,
    clasificación, clustering) entrenados sobre el dataset final.
    """
    st.subheader("Machine Learning")

    models, metrics = load_ml_models()

    if all(m is None for m in models.values()):
        st.info(
            "Los modelos de ML todavía no están entrenados. Ejecuta:\n\n"
            "```bash\n"
            "python -m models.train_regression\n"
            "python -m models.train_classification\n"
            "python -m models.train_clustering\n"
            "```"
        )
        return

    tab_reg, tab_clf, tab_clu = st.tabs([
        "Regresión (TDP)",
        "Clasificación (gama)",
        "Clustering (mercado)",
    ])

    with tab_reg:
        if models["regression"] is None:
            st.info("Modelo de regresión no entrenado. Ejecuta: `python -m models.train_regression`")
        else:
            regression_subview(df, models["regression"], metrics["regression"])

    with tab_clf:
        if models["classification"] is None:
            st.info("Modelo de clasificación no entrenado. Ejecuta: `python -m models.train_classification`")
        else:
            classification_subview(df, models["classification"], metrics["classification"])

    with tab_clu:
        if models["clustering"] is None:
            st.info("Modelo de clustering no entrenado. Ejecuta: `python -m models.train_clustering`")
        else:
            clustering_subview(df, models["clustering"], metrics["clustering"])


def main() -> None:
    """
    Ejecuta la aplicación principal de Streamlit.
    """
    st.title("GPU Market Analytics")
    st.markdown(
        """
        Dashboard interactivo para analizar precios, especificaciones técnicas,
        stock y valor comercial de tarjetas gráficas.
        """
    )

    df = load_data()

    if df.empty:
        st.stop()

    filtered_df = apply_filters(df)

    st.sidebar.markdown("---")
    st.sidebar.write(f"Registros filtrados: {len(filtered_df)}")

    if filtered_df.empty:
        st.warning("No hay datos para los filtros seleccionados.")
        st.stop()

    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "Vista ejecutiva",
            "Vista técnica",
            "Vista operativa",
            "Machine Learning"
        ]
    )

    with tab1:
        executive_view(filtered_df)

    with tab2:
        technical_view(filtered_df)

    with tab3:
        operational_view(filtered_df)

    with tab4:
        ml_view(filtered_df)


if __name__ == "__main__":
    main()