# 🌋 Volcanic Eruptions Analytics Dashboard

## Overview

The objective is to provide an interactive web application for the exploration and analysis of significant volcanic eruptions worldwide through geospatial visualization, statistical analysis, and historical trend exploration.

The application has been implemented using **Streamlit**, **Folium**, **GeoPandas**, and **Plotly**, combining interactive maps and analytical dashboards.

---

## Dataset

### Significant Volcanic Eruption Database

Source:

* Smithsonian Institution Global Volcanism Program [https://volcano.si.edu/]
* Kaggle Significant Volcanic Eruption Database [https://www.kaggle.com/datasets/mexwell/significant-volcanic-eruption-database]

The dataset contains historical records of significant volcanic eruptions worldwide.

An eruption is considered significant when at least one of the following conditions is satisfied:

* Human fatalities occurred.
* Significant economic damage was reported.
* Important environmental or social consequences were documented.
* High Volcanic Explosivity Index (VEI).
* Historical relevance.

---

## Project Structure

```text
project-root/
│
├── app.py
│
├── pages/
│   ├── 1_global_map.py
│   └── 2_analytics.py
│
├── utils/
│   └── data_loader.py
│
├── data/
│   ├── significant-volcanic-eruption-database.csv
│   └── ne_50m_admin_0_countries.json
│
├── requirements.txt
│
├── README.md
│
└── .streamlit/
    └── config.toml
```

---

## Application Architecture

### app.py

Main entry point of the application.

Responsibilities:

* Streamlit configuration.
* Session state initialization.
* Multipage navigation management.
* Connection between dashboard modules.

Implemented pages:

* 🗺️ Eruptions Map
* 📊 Analytics and Trends

---

### utils/data_loader.py

Centralized data loading and preprocessing module.

Main operations:

* Dataset loading.
* Coordinate extraction.
* Latitude/Longitude conversion.
* Missing value handling.
* VEI conversion.
* Death statistics conversion.
* Tsunami and earthquake flag generation.
* GeoPandas spatial join.
* Country and continent assignment.
* Streamlit cache optimization.

Performance optimization:
```python
@st.cache_data
```
is used to avoid unnecessary recomputation.

---

## Page 1 – Geospatial Analysis and Global Mapping

### Main Features
#### Interactive Choropleth Map

Users can switch between:

* Total Eruptions
* Average VEI
* Total Deaths

using a dedicated widget.

#### Volcano Layer

Each volcano is represented through:

* Geographic position
* Marker size proportional to eruption frequency
* Marker color proportional to maximum VEI
* Interactive popup information

#### Clustering
Nearby volcanoes can be grouped using MarkerCluster.

#### Time Filtering
Historical periods can be explored through an interactive year-range slider.

---

## Page 2 – Analytics and Trends
The analytical dashboard contains six interactive visualizations.

### 1. Historical Eruption Timeline
Shows temporal evolution of eruption frequency.

Aggregation levels:
* Year
* Decade
* Century

Visualization:
* Plotly Area Chart

---

### 2. Average Deaths per Eruption by Volcano Type
Compares human impact across volcano morphologies.

Visualization:
* Horizontal Bar Chart

---

### 3. VEI vs Total Deaths
Correlation analysis between eruption intensity and fatalities.

Visualization:
* Bubble Scatter Plot
* Logarithmic Y-axis

---
### 4. Secondary Events by VEI
Measures the occurrence of:
* Tsunamis
* Earthquakes
for different eruption intensity levels.

Visualization:
* Grouped Bar Chart

---

### 5. Geographic Hierarchical Decomposition
Hierarchy:
World → Continent → Country → Volcano Type

Visualization:
* Treemap

---

### 6. Top 10 Deadliest Volcanoes

Ranks volcanoes according to cumulative fatalities.
Visualization:
* Horizontal Ranking Chart

---

## Interactive Controls
The dashboard includes:
### Global Filters
* Continent selector
* Historical year range selector

### Map Controls
* Choropleth metric selector
* Volcano clustering toggle

### Timeline Controls
* Year
* Decade
* Century aggregation

All visualizations update dynamically according to user selections.

---

## Libraries Used
### Core
* Streamlit
* Pandas
* NumPy

### Geospatial
* GeoPandas
* Folium
* Streamlit-Folium

### Visualization
* Plotly Express

---

## Performance Optimizations
The application follows Streamlit best practices:

### Cached Data Loading
```python
@st.cache_data
```
prevents repeated dataset loading.

### Session State
```python
st.session_state
```
preserves filters across pages.

### Fragment Rendering
```python
@st.fragment
```
limits unnecessary rerendering of the map.
These techniques significantly reduce computational overhead and improve user experience.

---

## Main Insights Supported by the Dashboard
The application allows users to:

* Identify volcanic hotspots worldwide.
* Explore historical eruption trends.
* Compare volcano morphologies.
* Analyze relationships between VEI and fatalities.
* Investigate secondary hazards.
* Study regional volcanic activity patterns.
* Identify historically dangerous volcanoes.

---

## Deployment

The application is designed for deployment on:

* Streamlit Community Cloud
* Any public hosting service supporting Streamlit applications

---

## Author: Giuseppe Di Palma

Academic project developed for:

**MIARFID – Data Visualization**

Universitat Politècnica de València
