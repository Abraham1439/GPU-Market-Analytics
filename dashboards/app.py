from pathlib import Path
import sqlite3

import pandas as pd
import plotly.express as px
import streamlit as st


BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "data" / "database" / "gpu_market_analytics.db"


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

    tab1, tab2, tab3 = st.tabs(
        [
            "Vista ejecutiva",
            "Vista técnica",
            "Vista operativa"
        ]
    )

    with tab1:
        executive_view(filtered_df)

    with tab2:
        technical_view(filtered_df)

    with tab3:
        operational_view(filtered_df)


if __name__ == "__main__":
    main()