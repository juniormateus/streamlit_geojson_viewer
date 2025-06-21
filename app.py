import streamlit as st
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
import folium
from streamlit_folium import st_folium

def carregar_geojson_ajustado(uploaded_file):
    try:
        gdf = gpd.read_file(uploaded_file)

        # Verifica se possui geometria válida
        if "geometry" in gdf.columns and not gdf.geometry.isnull().all():
            return gdf

        # Tenta reconstruir com colunas lat/lon
        df = pd.read_json(uploaded_file)

        if {'lat', 'lon'}.issubset(df.columns):
            geometry = [Point(xy) for xy in zip(df["lon"], df["lat"])]
            return gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")

        elif {'x', 'y'}.issubset(df.columns):
            geometry = [Point(xy) for xy in zip(df["x"], df["y"])]
            return gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")

        return None  # sem geometria possível

    except Exception as e:
        st.error(f"Erro ao carregar arquivo: {e}")
        return None


# --- App Streamlit ---
st.set_page_config(page_title="Visualizador de GeoJSON", layout="wide")
st.title("🗺️ Visualizador Interativo de GeoJSON")

uploaded_file = st.file_uploader("Envie seu arquivo GeoJSON", type=["geojson", "json"], key="geojson_upload")

if uploaded_file:
    gdf = carregar_geojson_ajustado(uploaded_file)

    if gdf is None:
        st.error("❌ Não foi possível carregar ou reconstruir a geometria.")
        st.stop()

    # Verifica se geometria está presente e válida
    if "geometry" not in gdf.columns or gdf.geometry.isnull().all():
        st.error("❌ O arquivo não contém geometria válida.")
        st.stop()

    # Cria mapa
    centroid = gdf.geometry.centroid
    mapa = folium.Map(location=[centroid.y.mean(), centroid.x.mean()], zoom_start=12)

    folium.GeoJson(
        gdf,
        tooltip=folium.GeoJsonTooltip(fields=[col for col in gdf.columns if col != 'geometry']),
        highlight_function=lambda x: {"weight": 3, "color": "red"},
    ).add_to(mapa)

    # Renderiza o mapa no Streamlit
    map_data = st_folium(mapa, width=700, height=500)

    # Exibe atributos da feição clicada
    if map_data and map_data.get("last_active_drawing"):
        st.subheader("📋 Atributos da feição selecionada:")
        st.json(map_data["last_active_drawing"]["properties"])
else:
    st.info("Envie um arquivo GeoJSON válido para começar.")
