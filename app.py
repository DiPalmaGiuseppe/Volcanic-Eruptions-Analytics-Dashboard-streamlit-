import streamlit as st

st.set_page_config(
    page_title="Volcanic Eruptions Analytics Dashboard",
    layout="wide",
    page_icon="🌋"
)

if "map_metric" not in st.session_state:
    st.session_state["map_metric"] = "Total Eruptions"
if "continent" not in st.session_state:
    st.session_state["continent"] = "All"
if "show_clusters" not in st.session_state:
    st.session_state["show_clusters"] = True
if "year_range" not in st.session_state:
    st.session_state["year_range"] = None

map_page = st.Page("pages/1_global_map.py", title="Eruptions Map", icon="🗺️")
analytics_page = st.Page("pages/2_analytics.py", title="Analytics and Trends", icon="📊")

pg = st.navigation([map_page, analytics_page])
pg.run()