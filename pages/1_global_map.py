import streamlit as st
import folium
from streamlit_folium import st_folium
import numpy as np
import pandas as pd
from utils.data_loader import load_base_data
from folium.plugins import MarkerCluster

st.title("🗺️ Geospatial Analysis and Global Mapping of Volcanic Activities")

try:
    df_volcano, world_boundaries = load_base_data()
except Exception as e:
    st.error(f"Critical data loading error: {e}")
    st.stop()

st.markdown("## 📊 Dataset Description and Preparation")

st.markdown("""
    This project is based on the **Significant Volcanic Eruption Database**, publicly available on
    [Kaggle](https://www.kaggle.com/datasets/mexwell/significant-volcanic-eruption-database)
    and originally derived from the
    [Smithsonian Institution's Global Volcanism Program](https://volcano.si.edu/).

    The dataset contains historical records of **significant volcanic eruptions** worldwide.

    According to the source definition, an eruption is considered significant when at least one of the following conditions is met:

    - It caused documented fatalities.
    - It generated substantial economic damage.
    - It produced relevant social or environmental consequences.
    - It reached a high level on the Volcanic Explosivity Index (VEI).
    - It represents an event of particular historical importance.

    Because of this selection criterion, the dataset does not contain all volcanic eruptions ever recorded, but rather the subset of events considered significant from a geological, social, or economic perspective.

    ### Main Attributes Used in This Project
    The original dataset contains more than thirty variables describing eruption characteristics, consequences, and geographic information. 
    For this dashboard only the most relevant variables were selected:

    - **Year**: year in which the eruption occurred.
    - **Coordinates**: geographic location of the volcano.
    - **Volcano Name**: unique volcano identifier.
    - **Volcano Type**: morphological classification of the volcano.
    - **Country**: country reported in the original database.
    - **Volcanic Explosivity Index (VEI)**: logarithmic scale measuring eruption magnitude from 0 to 8.
    - **Total Effects : Deaths**: total fatalities associated with the eruption, including secondary events.
    - **Flag Tsunami**: indicates whether the eruption generated a tsunami.
    - **Flag Earthquake**: indicates whether the eruption was associated with seismic activity.

    ### Data Preparation
    Several preprocessing operations were performed before visualization:

    1. Geographic coordinates were extracted and converted into numerical latitude and longitude values.
    2. Invalid records without temporal or spatial information were removed.
    3. VEI and mortality variables were converted into numerical format.
    4. Volcano morphology and volcano names were standardized to avoid missing categories.
    5. Tsunami and earthquake indicators were transformed into Boolean variables.
    6. A spatial join between eruption coordinates and geopolitical boundaries was performed using GeoPandas to automatically assign each eruption to a country and continent.
    7. The processed dataset was cached using Streamlit's `@st.cache_data` decorator to improve performance and avoid repeated file loading.

    The resulting dataset enables both temporal and spatial analysis of volcanic activity, human impact, eruption intensity, and associated secondary hazards.
""")

# Primary filters
col1, col2 = st.columns(2)
with col1:
    min_year, max_year = int(df_volcano['Year'].min()), int(df_volcano['Year'].max())
    
    if "year_range" not in st.session_state or st.session_state["year_range"] is None:
        st.session_state["year_range"] = (min_year, max_year)
    
    st.session_state["year_range"] = st.slider(
        "Select historical time range", 
        min_value=min_year, 
        max_value=max_year, 
        value=st.session_state["year_range"]
    )
with col2:
    st.session_state["map_metric"] = st.selectbox(
        "Select choropleth map background metric", 
        ["Total Eruptions", "Average VEI", "Total Deaths"],
        index=["Total Eruptions", "Average VEI", "Total Deaths"].index(st.session_state["map_metric"])
    )

y_min, y_max = st.session_state["year_range"]
indexed_df = df_volcano.set_index('Year').sort_index()
filtered_df = indexed_df.loc[y_min:y_max].reset_index()

# 1. National aggregation for choropleth map
if st.session_state["map_metric"] == "Total Eruptions":
    agg_data = filtered_df.groupby('Country_Map').size().reset_index(name='Value')
elif st.session_state["map_metric"] == "Average VEI":
    agg_data = filtered_df.groupby('Country_Map')['VEI'].mean().reset_index(name='Value')
else:
    agg_data = filtered_df.groupby('Country_Map')['Total_Deaths'].sum().reset_index(name='Value')

# 2. Aggregation by single volcano to avoid overlapping points
volcano_agg = filtered_df.groupby('Volcano Name').agg(
    Latitude=('Latitude', 'first'),
    Longitude=('Longitude', 'first'),
    Volcano_Type=('Volcano_Type', 'first'),
    Eruptions_Count=('Year', 'count'),
    Max_VEI=('VEI', 'max'),
    Deaths_Sum=('Total_Deaths', 'sum'),
    Has_Tsunami=('Has_Tsunami', 'any'),
    Has_Earthquake=('Has_Earthquake', 'any')
).reset_index()

# Map isolation to prevent full page reload on zoom/click events
@st.fragment
def render_folium_map(coropleth_data, point_data):
    
    show_clusters = st.checkbox("Raggruppa vulcani vicini (cluster)", value=True)
    m = folium.Map(location=[20, 0], zoom_start=2, tiles="cartodbpositron")
    
    # Layer 1: Choropleth Map (Country Context)
    if not coropleth_data.empty:
        valid_vals = coropleth_data['Value'].dropna()
        unique_vals = len(valid_vals.unique())
        if unique_vals > 4:
            bins = list(np.unique(np.percentile(valid_vals, [0, 40, 60, 80, 100])))
        else:
            bins = list(np.sort(valid_vals.unique()))
            if len(bins) == 1:
                bins = [0, bins[0]]
            elif len(bins) == 0:
                bins = [0, 1]
                

        colors = ['#ffffb2', '#fecc5c', '#fd8d3c', '#f03b20', '#bd0026']
        val_dict = coropleth_data.set_index('Country_Map')['Value'].to_dict()
        
        def get_color(val):
            if val is None or pd.isna(val):
                return 'transparent'
            for i in range(len(bins) - 1):
                if val <= bins[i+1]:
                    return colors[i % len(colors)]
            return colors[-1]

        folium.GeoJson(
            world_boundaries,
            name="Choropleth Layer",
            style_function=lambda feature: {
                'fillColor': get_color(val_dict.get(feature['properties']['Country_Map'])),
                'color': 'transparent',
                'weight': 0,
                'fillOpacity': 0.6 if val_dict.get(feature['properties']['Country_Map']) is not None else 0
            }
        ).add_to(m)

        legend_html = f'''
        <div style="position: absolute; bottom: 30px; right: 30px; z-index:9999; font-size:13px;
                    background-color: white; padding: 10px; border-radius: 6px; 
                    box-shadow: 0 1px 5px rgba(0,0,0,0.2); font-family: Arial, sans-serif;">
            <b style="display: block; margin-bottom: 5px;">{st.session_state["map_metric"]}</b>
        '''
        for i in range(len(bins) - 1):
            c_hex = colors[i % len(colors)]
            v_low = int(bins[i]) if float(bins[i]).is_integer() else round(bins[i], 1)
            v_high = int(bins[i+1]) if float(bins[i+1]).is_integer() else round(bins[i+1], 1)
            label = f"{v_low}" if v_low == v_high else f"{v_low} - {v_high}"
            legend_html += f'<div style="margin-bottom: 3px;"><i style="background:{c_hex}; width:15px; height:15px; display:inline-block; margin-right:8px; vertical-align:middle; opacity:0.8; border:1px solid #ccc;"></i><span style="vertical-align:middle;">{label}</span></div>'
        legend_html += '</div>'
        m.get_root().html.add_child(folium.Element(legend_html))

    # Layer 2: Markers corresponding to Volcanoes
    if show_clusters:
        layer = MarkerCluster(name="Volcanoes")
    else:
        layer = folium.FeatureGroup(name="Volcanoes")

    for idx, row in point_data.iterrows():
        radius = max(4, min(15, 4 + np.log1p(row['Eruptions_Count']) * 2.5))

        max_vei = row['Max_VEI']
        if pd.isna(max_vei):
            color = '#888888'
        elif max_vei < 3:
            color = '#feb24c'
        elif max_vei < 5:
            color = '#fd8d3c'
        else:
            color = '#800026'

        events = []
        if row['Has_Tsunami']:   events.append("🌊 Tsunami")
        if row['Has_Earthquake']: events.append("⚡ Earthquake")
        events_str = ", ".join(events) if events else "None"

        popup_html = f"""
        <div style='font-family: Arial, sans-serif; min-width: 190px; font-size: 12px;'>
            <h4 style='margin:0 0 5px 0; color:#800026;'>{row['Volcano Name']}</h4>
            <b>Morphology:</b> {row['Volcano_Type']}<br>
            <b>Eruptions in period:</b> {row['Eruptions_Count']}<br>
            <b>Max VEI:</b> {int(max_vei) if not pd.isna(max_vei) else 'Not documented'}<br>
            <b>Total Deaths:</b> {int(row['Deaths_Sum']) if pd.notna(row['Deaths_Sum']) else 'Not documented'}<br>
            <b>Associated events:</b> {events_str}
        </div>
        """

        folium.CircleMarker(
            location=[row['Latitude'], row['Longitude']],
            radius=radius,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=row['Volcano Name'],        # ← aggiunto: nome visibile su hover
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.75,
            weight=1
        ).add_to(layer)

    layer.add_to(m)
    folium.LayerControl().add_to(m)
    st_folium(m, width="100%", height=620, returned_objects=[])

render_folium_map(agg_data, volcano_agg)

st.divider()

st.markdown("## 🌍 Map Interpretation and Visualization Methodology")

st.markdown("""
The map combines two complementary visualization techniques:
### Choropleth Layer
The background layer is a choropleth map representing aggregated volcanic indicators at country level.

Depending on the selected metric, countries are colored according to:

- Total number of significant eruptions.
- Average Volcanic Explosivity Index (VEI).
- Total recorded fatalities.

This approach allows users to identify spatial patterns and compare volcanic activity among different geographical regions.

### Volcano Marker Layer
The second layer displays individual volcanoes using proportional circle markers.

Visual encodings include:

- Marker size proportional to the number of recorded eruptions.
- Marker color representing the maximum VEI reached by the volcano.
- Interactive popups containing detailed information about morphology, fatalities, eruption frequency, and associated hazards.

Nearby volcanoes can optionally be grouped through clustering techniques in order to reduce visual clutter and improve readability.
""")