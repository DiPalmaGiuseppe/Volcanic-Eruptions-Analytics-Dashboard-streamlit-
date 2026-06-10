import streamlit as st
import pandas as pd
import geopandas as gpd

@st.cache_data
def load_base_data():
    """
    Load and process the significant volcanic eruptions dataset and geopolitical boundaries.
    Uses caching to guarantee maximum performance when switching between pages.
    """
    df = pd.read_csv("data/significant-volcanic-eruption-database.csv", sep=";")
    
    df[['Latitude', 'Longitude']] = df['Coordinates'].str.split(',', expand=True)
    df['Latitude'] = pd.to_numeric(df['Latitude'], errors='coerce')
    df['Longitude'] = pd.to_numeric(df['Longitude'], errors='coerce')
    
    df = df.dropna(subset=['Latitude', 'Longitude', 'Year'])
    df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
    
    # STATISTICAL NOTE: Keeping NaNs for VEI to avoid distorting mathematical averages (avoiding fillna(0))
    df['VEI'] = pd.to_numeric(df['Volcanic Explosivity Index'], errors='coerce')
    
    df['Total_Deaths'] = pd.to_numeric(df['Total Effects : Deaths'], errors='coerce')
    df['Volcano_Type'] = df['Volcano Type'].fillna("Unknown")
    df['Volcano Name'] = df['Volcano Name'].fillna("Unknown")
    df['Has_Tsunami'] = df['Flag Tsunami'].notna() & (df['Flag Tsunami'].astype(str).str.strip() != '')
    df['Has_Earthquake'] = df['Flag Earthquake'].notna() & (df['Flag Earthquake'].astype(str).str.strip() != '')
    
    world = gpd.read_file("data/ne_50m_admin_0_countries.json")
    world = world.rename(columns={'ADMIN': 'Country_Map'})
    
    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.Longitude, df.Latitude), crs="EPSG:4326")
    gdf = gdf.to_crs(world.crs)
    gdf_final = gpd.sjoin(gdf, world[['Country_Map', 'CONTINENT', 'geometry']], how="left", predicate="within")
    gdf_final = gdf_final.rename(columns={'CONTINENT': 'Continent'})
    gdf_final['Continent'] = gdf_final['Continent'].fillna('Oceanic/Unassigned')
    
    gdf_final['Country_Map'] = gdf_final['Country_Map'].fillna(gdf_final['Country']).fillna('Oceanic/Unassigned')
    
    df_final = pd.DataFrame(gdf_final.drop(columns=['geometry', 'index_right'], errors='ignore'))    
    return df_final, world[['Country_Map', 'geometry']].copy()