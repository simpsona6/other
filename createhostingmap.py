import geopandas as gpd
import pydeck as pdk
import streamlit as st

st.set_page_config(page_title="Hosting Capacity", layout="wide")
st.title("Distribution hosting capacity")

#same as map
COLORS = {
    24: [230, 0, 169],
    20: [0, 112, 255],
    16: [76, 230, 0],
    8: [255, 255, 0],
    4: [255, 85, 0],
    1: [255, 0, 0],
}


@st.cache_data  #load and cache
def load():
    gdf = gpd.read_file("hosting_capacity.geojson")
    #multipart lines into single lines
    gdf = gdf.explode(index_parts=False)
    gdf["path"] = gdf.geometry.apply(lambda g: [list(c) for c in g.coords])
    gdf["color"] = gdf["LIMIT_VAL"].map(COLORS)
    gdf["color"] = gdf["color"].apply(lambda c: c if isinstance(c, list) else [150, 150, 150])
    return gdf


lines = load()

# --- Sidebar filter --------------------------------------------------------
min_mw = st.sidebar.select_slider(
    "Minimum available capacity (MW)",
    options=sorted(lines["LIMIT_VAL"].dropna().unique()),
)
shown = lines[lines["LIMIT_VAL"] >= min_mw]

# --- Headline number -------------------------------------------------------
st.metric("Line segments shown", f"{len(shown):,}")

# --- Map -------------------------------------------------------------------
center = shown.geometry.union_all().centroid
layer = pdk.Layer(
    "PathLayer",
    data=shown[["path", "color", "LIMIT_VAL", "Line_Voltage"]],
    get_path="path",
    get_color="color",
    width_min_pixels=2,
    pickable=True,
)
st.pydeck_chart(
    pdk.Deck(
        layers=[layer],
        initial_view_state=pdk.ViewState(
            latitude=center.y, longitude=center.x, zoom=7
        ),
        tooltip={"text": "Up to {LIMIT_VAL} MW\nVoltage code: {Line_Voltage}"},
    )
)

# --- Download --------------------------------------------------------------
st.download_button(
    "Download filtered lines (GeoJSON)",
    shown.drop(columns=["path", "color"]).to_json(),
    file_name=f"hosting_capacity_{min_mw}MW_plus.geojson",
)

# -m streamlit run createhostingmap.py paste in terminal to run