import requests
import geopandas as gpd


LAYER_URL = (
    "https://services.arcgis.com/DmE6Z8jKWf8lv84J/ArcGIS/rest/services/"
    "Primary_Hosting_Capacity_Available_EB/FeatureServer/6"
)

PAGE_SIZE = 2000
REQUIRED_FIELDS = {"OBJECTID", "LIMIT_VAL", "Line_Voltage"}
MEASURE_CRS = "EPSG:2284"

# ----------------------------------------------------------------------------------
# grab all features...note that this pulls down to be stored locally and is not live

def fetch_all(layer_url, page_size=PAGE_SIZE):
    """Return all features from the layer as a GeoDataFrame."""   #pandas table with geometry
    query_url = layer_url + "/query"

    # count all features
    count = requests.get(
        query_url,
        params={"where": "1=1", "returnCountOnly": "true", "f": "json"},
        timeout=60,
    ).json()["count"]
    print(f"Service reports {count:,} features")

    all_features = []
    offset = 0
    while offset < count:
        params = {
            "where": "1=1",
            "outFields": "*",
            "orderByFields": "OBJECTID",  # stable order so pages don't overlap
            "resultOffset": offset,
            "resultRecordCount": page_size,
            "f": "geojson",
        }
        resp = requests.get(query_url, params=params, timeout=120)
        resp.raise_for_status()
        batch = resp.json()["features"]
        if not batch:
            break
        all_features.extend(batch)
        offset += len(batch)
        print(f"  downloaded {offset:,} / {count:,}")

    # lat/long for geojson (EPSG:4326).
    return gpd.GeoDataFrame.from_features(all_features, crs="EPSG:4326")


# ---------------------------------------------------------------------------
# validate schema, geometry, CRS, etc
def validate(gdf):
    # Schema check
    missing = REQUIRED_FIELDS - set(gdf.columns)
    if missing:
        raise ValueError(f"Schema changed. Missing fields: {missing}")

    # CRS check
    print("CRS:", gdf.crs)

    # Geometry checks
    empty = gdf.geometry.is_empty | gdf.geometry.isna()
    print(f"Empty or missing geometries: {empty.sum()}")
    gdf = gdf[~empty].copy()

    invalid = ~gdf.is_valid
    print(f"Invalid geometries: {invalid.sum()}")
    if invalid.any():
        gdf.loc[invalid, "geometry"] = gdf.loc[invalid].make_valid()

    return gdf
# ---------------------------------------------------------------------------
# output files
if __name__ == "__main__":
    lines = fetch_all(LAYER_URL)
    lines = validate(lines)

    lines.to_file("hosting_capacity.geojson", driver="GeoJSON")
    print("\nSaved hosting_capacity.geojson")