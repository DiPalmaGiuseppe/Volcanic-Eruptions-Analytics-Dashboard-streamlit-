import streamlit as st
import plotly.express as px
import pandas as pd
from utils.data_loader import load_base_data


def build_volcano_list(group):
    """Build a formatted HTML list of volcanoes for treemap hover tooltips."""
    per_volcano = group.groupby('Volcano Name').agg(
        Eruptions=('Year', 'count'),
        Has_Tsunami=('Has_Tsunami', 'any'),
        Has_Earthquake=('Has_Earthquake', 'any')
    ).reset_index().sort_values('Eruptions', ascending=False)

    items = []
    for _, v in per_volcano.iterrows():
        icons = ('🌊' if v['Has_Tsunami'] else '') + ('⚡' if v['Has_Earthquake'] else '')
        items.append(f"{v['Volcano Name']} {icons}".strip())

    MAX_ITEMS = 24
    extra = len(items) - MAX_ITEMS if len(items) > MAX_ITEMS else 0
    if extra > 0:
        items = items[:MAX_ITEMS]

    mid = (len(items) + 1) // 2
    col1_items, col2_items = items[:mid], items[mid:]

    lines = []
    for i in range(mid):
        right = col2_items[i] if i < len(col2_items) else ''
        lines.append(f"{col1_items[i]}  ·  {right}" if right else col1_items[i])

    if extra > 0:
        lines.append(f"...+{extra} more")

    return '<br>'.join(lines)


st.title("Analytical Study and Evolution of Volcanic Activities")
st.markdown("""
    ## 📖 Analytical Methodology

    The following visualizations explore volcanic activity from multiple complementary perspectives:

    - Temporal evolution of eruption frequency.
    - Morphological differences among volcanoes.
    - Relationship between eruption intensity and human impact.
    - Occurrence of secondary hazards.
    - Geographic distribution patterns.
    - Historical risk rankings.

    ---
    ## 🎛️ Global Controls & Filters
    Use the interactive widgets below to slice and dice the dataset. All visualizations on this page updates automatically based on your selection:

    *   **Filter by Continent:** Focus your analysis on a single continent to identify regional patterns, or select **"All"** to maintain a global perspective.
    *   **Year Range Slider:** Filter the historical timeline to focus on specific eras, centuries, or modern decades. This helps mitigate historical reporting bias by isolating well-documented periods.
""")

try:
    df_volcano, _ = load_base_data()
except Exception as e:
    st.error(f"Error loading analytical module: {e}")
    st.stop()

col_f1, col_f2 = st.columns(2)
chart_col, text_col = st.columns([2,1])
with col_f1:
    continent_list = ["All"] + sorted(df_volcano['Continent'].dropna().unique().tolist())
    if st.session_state["continent"] not in continent_list:
        st.session_state["continent"] = "All"

    def _save_continent():
        st.session_state["continent"] = st.session_state["_continent_widget"]

    st.selectbox("Filter by Continent", continent_list,
                 index=continent_list.index(st.session_state["continent"]),
                 key="_continent_widget",
                 on_change=_save_continent)

with col_f2:
    min_year, max_year = int(df_volcano['Year'].min()), int(df_volcano['Year'].max())
    if st.session_state["year_range"] is None:
        st.session_state["year_range"] = (min_year, max_year)

    def _save_year_analytics():
        st.session_state["year_range"] = st.session_state["_year_range_analytics"]

    st.slider("Year Range", min_year, max_year,
              value=st.session_state["year_range"],
              key="_year_range_analytics",
              on_change=_save_year_analytics)

plot_df = df_volcano.copy()
if st.session_state["continent"] != "All":
    plot_df = plot_df[plot_df['Continent'] == st.session_state["continent"]]
y_min, y_max = st.session_state["year_range"]
plot_df = plot_df[(plot_df['Year'] >= y_min) & (plot_df['Year'] <= y_max)]


st.markdown("### 📈 Temporal Development and Morphological Characteristics")
chart_col, text_col = st.columns([2,1])

# ── Graph 1: Timeline with granularity selector (NEW version) ──────────────
with chart_col:
    st.subheader(f"1. Historical Eruption Timeline ({y_min} – {y_max})")

    granularity = st.radio(
        "Granularity", ["Year", "Decade", "Century"],
        horizontal=True, index=1, key="tl_gran"
    )

    if granularity == "Year":
        timeline_df = plot_df.groupby('Year').size().reset_index(name='Eruptions')
        x_col = 'Year'
        x_label = 'Year'
    elif granularity == "Decade":
        tmp = plot_df.copy()
        tmp['Decade'] = (tmp['Year'] // 10) * 10
        timeline_df = tmp.groupby('Decade').size().reset_index(name='Eruptions')
        x_col = 'Decade'
        x_label = 'Decade'
    else:
        tmp = plot_df.copy()
        tmp['Century'] = (tmp['Year'] // 100) * 100
        timeline_df = tmp.groupby('Century').size().reset_index(name='Eruptions')
        x_col = 'Century'
        x_label = 'Century'

    if not timeline_df.empty:
        fig1 = px.area(
            timeline_df, x=x_col, y='Eruptions',
            title=f"Annual frequency of cataloged eruptions (per {granularity.lower()})",
            labels={'Eruptions': 'Number of Significant Eruptions', x_col: x_label},
            color_discrete_sequence=['#ff4b4b']
        )
        fig1.update_layout(hovermode="x unified", margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig1, width='stretch', theme="streamlit")

    else:
        st.info("No data recorded for the selected area.")
        
with text_col:
    st.markdown("""
        ### Interpretation
        This area chart represents the temporal evolution of significant volcanic eruptions.
        Users can dynamically change the aggregation level between years, decades, and centuries to explore both short-term and long-term trends.
        The chart helps identify historical periods characterized by increased volcanic activity and provides insight into how eruption records are distributed through time.

        ### Visualization Design
        An area chart was selected because it effectively highlights changes in event frequency while preserving temporal continuity.
        The chart is implemented using Plotly Express, providing interactive exploration through zooming and tooltips.
    """)

# ── Graph 2: Average Deaths per Eruption by Volcano Type (unchanged) ──────
st.divider()
chart_col, text_col = st.columns([2,1])
with chart_col:
    st.subheader("2. Average Deaths per Eruption by Volcano Type")

    # Statistical note: we weight only eruptions that have a death record.
    # Using all eruptions as denominator (including those with NaN deaths)
    # would underestimate the true average lethality of documented events.
    type_lethality = plot_df.groupby('Volcano_Type').agg(
        Total_Eruptions=('Year', 'count'),
        # count only rows where Total_Deaths is not NaN for the average denominator
        Eruptions_With_Deaths=('Total_Deaths', 'count'),
        Total_Deaths=('Total_Deaths', 'sum')
    ).reset_index()

    # Exclude types with fewer than 5 eruptions (too small a sample)
    type_lethality = type_lethality[type_lethality['Total_Eruptions'] >= 5]

    # Divide by Eruptions_With_Deaths (not Total_Eruptions) to avoid denominator bias.
    # Guard against division by zero when no death data exists for a type.
    type_lethality['Deaths_per_Eruption'] = (
        type_lethality.apply(
            lambda r: round(r['Total_Deaths'] / r['Eruptions_With_Deaths'], 1)
            if r['Eruptions_With_Deaths'] > 0 else 0.0,
            axis=1
        )
    )
    type_lethality = type_lethality.sort_values('Deaths_per_Eruption', ascending=False)

    if not type_lethality.empty:
        fig2 = px.bar(
            type_lethality,
            x='Deaths_per_Eruption',
            y='Volcano_Type',
            orientation='h',
            text='Deaths_per_Eruption',
            custom_data=['Total_Eruptions', 'Eruptions_With_Deaths', 'Total_Deaths'],
            title="Average human impact per significant eruption event",
            labels={
                'Deaths_per_Eruption': 'Avg Deaths per Eruption',
                'Volcano_Type': 'Morphological Type'
            },
            color='Deaths_per_Eruption',
            color_continuous_scale='Reds'
        )
        fig2.update_traces(
            texttemplate='%{text:,.0f}',
            textposition='outside',
            cliponaxis=False,
            hovertemplate=(
                '<b>%{y}</b><br>'
                'Avg deaths per eruption: %{x:,.1f}<br>'
                'Total cataloged eruptions: %{customdata[0]}<br>'
                'Eruptions with death data: %{customdata[1]}<br>'
                'Total cumulative deaths: %{customdata[2]:,.0f}'
                '<extra></extra>'
            )
        )
        fig2.update_layout(
            yaxis={'categoryorder': 'total ascending'},
            coloraxis_showscale=False,
            xaxis=dict(range=[0, type_lethality['Deaths_per_Eruption'].max() * 1.18]),
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig2, width='stretch', theme="streamlit")
    else:
        st.info("Insufficient data for the selected filters.")
        

with text_col:
    st.markdown("""
        ### Interpretation
        This visualization compares the average human impact associated with different volcano morphologies.
        Rather than measuring total fatalities, the chart focuses on average deaths per eruption, allowing a more balanced comparison between volcano types.
        This helps identify which volcanic structures have historically generated the most severe consequences when an eruption occurs.

        ### Visualization Design
        A horizontal bar chart was chosen because it facilitates ranking and comparison between categorical groups.
        Interactive tooltips provide additional statistical context including eruption counts and cumulative fatalities.
    """)

st.markdown("### 💥 Impact Correlation and Historical Explosion Density")
st.divider()
chart_col, text_col = st.columns([2,1])

with chart_col:
    st.subheader("3. Lethality Analysis: VEI vs Total Deaths")

    # Drop rows missing VEI (can't place on X axis) OR missing deaths (can't plot on log Y axis).
    # Using only rows with both values avoids phantom points at y=0 on a log scale.
    scatter_df = plot_df.dropna(subset=['VEI', 'Total_Deaths']).copy()
    # Filter out zero-death rows to keep the log scale meaningful
    scatter_df = scatter_df[scatter_df['Total_Deaths'] > 0]

    # Bubble size: power-scale on deaths (dampens outliers), clipped to a reasonable display range
    scatter_df['bubble_size'] = (
        scatter_df['Total_Deaths'].clip(upper=10_000) ** 0.4
    ).clip(lower=5).astype(int)

    if not scatter_df.empty:
        fig3 = px.scatter(
            scatter_df, x='VEI', y='Total_Deaths',
            hover_name='Volcano Name',
            hover_data={'Country_Map': True, 'Year': True, 'bubble_size': False},
            color='VEI',
            size='bubble_size',
            size_max=35,
            title="VEI Index vs Total Fatalities (Log Y Scale)",
            labels={
                'VEI': 'Volcanic Explosivity Index',
                'Total_Deaths': 'Total Deaths (incl. secondary effects)',
                'Country_Map': 'Country'
            },
            color_continuous_scale='Reds',
            log_y=True
        )
        fig3.update_layout(margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig3, width='stretch', theme="streamlit")

        n_excluded = len(plot_df) - len(scatter_df)
        if n_excluded > 0:
            st.caption(
                f"⚠️ {n_excluded} eruptions excluded: missing VEI, zero reported deaths, "
                f"or deaths data unavailable. Log scale requires positive values."
            )
    else:
        st.info("No eruptions with both VEI and fatality data for the selected filters.")

with text_col:
    st.markdown("""
        ### Interpretation
        This scatter plot investigates the relationship between eruption intensity and human impact.
        The horizontal axis represents the Volcanic Explosivity Index (VEI), while the vertical logarithmic axis represents total fatalities.
        Bubble size is proportional to the number of deaths, allowing simultaneous analysis of magnitude, impact, and event distribution.

        ### Visualization Design
        Scatter plots are particularly suitable for correlation analysis because they reveal potential relationships between quantitative variables.
        The logarithmic scale reduces distortion caused by extreme historical disasters and improves visibility of medium-scale events.
        Plotly interactivity enables detailed exploration of individual eruptions.
    """)
    
st.divider()
chart_col, text_col = st.columns([2,1])

with chart_col:
    st.subheader("4. Secondary Events by VEI Level")

    vei_df = plot_df.dropna(subset=['VEI']).copy()
    vei_df['VEI_int'] = vei_df['VEI'].astype(int)

    vei_grouped = vei_df.groupby('VEI_int').agg(
        Total=('VEI_int', 'count'),
        Tsunami_Count=('Has_Tsunami', 'sum'),
        Earthquake_Count=('Has_Earthquake', 'sum')
    ).reset_index()

    vei_grouped['🌊 Tsunami'] = (vei_grouped['Tsunami_Count'] / vei_grouped['Total'] * 100).round(1)
    vei_grouped['⚡ Earthquake'] = (vei_grouped['Earthquake_Count'] / vei_grouped['Total'] * 100).round(1)

    melted = vei_grouped.melt(
        id_vars=['VEI_int', 'Total'],
        value_vars=['🌊 Tsunami', '⚡ Earthquake'],
        var_name='Event Type',
        value_name='Percentage'
    )
    melted['hover_label'] = melted.apply(
        lambda r: f"{r['Event Type']}<br>VEI {r['VEI_int']}: {r['Percentage']}% of {r['Total']} eruptions",
        axis=1
    )

    if not melted.empty:
        fig4 = px.bar(
            melted, x='VEI_int', y='Percentage',
            color='Event Type',
            barmode='group',
            text='Percentage',
            title="% of eruptions with associated secondary events per VEI",
            labels={'VEI_int': 'VEI Level', 'Percentage': '% of Eruptions'},
            color_discrete_map={'🌊 Tsunami': '#1a6ca8', '⚡ Earthquake': '#e07b00'},
            custom_data=['hover_label']
        )
        fig4.update_traces(
            texttemplate='%{text:.1f}%',
            textposition='outside',
            cliponaxis=False,
            hovertemplate='%{customdata[0]}<extra></extra>'
        )
        fig4.update_layout(
            xaxis=dict(tickmode='linear', dtick=1, title='VEI Level'),
            yaxis=dict(range=[0, 105], title='% of Eruptions'),
            margin=dict(l=20, r=20, t=40, b=20),
            legend=dict(title='Secondary Event')
        )
        st.plotly_chart(fig4, width='stretch', theme="streamlit")
    else:
        st.info("Insufficient data for the selected filters.")

with text_col:
    st.markdown("""
        ### Interpretation
        This chart analyzes the frequency of secondary hazards associated with different eruption intensities.
        For each VEI level, the percentage of eruptions generating tsunamis or earthquakes is calculated.
        The visualization helps evaluate whether stronger eruptions are more likely to trigger additional hazardous phenomena.

        ### Visualization Design
        Grouped bar charts provide a clear comparison between multiple categories measured across the same quantitative scale.
        The use of percentages normalizes the results and prevents bias caused by unequal sample sizes among VEI categories.
        Interactive features facilitate detailed examination of each eruption class.
    """)

st.markdown("### 🌍 Overall Composition and Cumulative Risk Rankings")
st.divider()
chart_col, text_col = st.columns([2,1])

with chart_col:
    st.subheader("5. Geographic Hierarchical Decomposition (Treemap)")
    tree_df = plot_df[plot_df['Country_Map'] != 'Oceanic/Unassigned'].copy()

    if not tree_df.empty:
        agg_parts = []
        for (continent, country, vtype), grp in tree_df.groupby(
            ['Continent', 'Country_Map', 'Volcano_Type']
        ):
            agg_parts.append({
                'Continent': continent,
                'Country_Map': country,
                'Volcano_Type': vtype,
                'Eruptions': len(grp),
                'Volcano_List': build_volcano_list(grp)
            })
        volcano_tree = pd.DataFrame(agg_parts)

        fig5 = px.treemap(
            volcano_tree,
            path=[px.Constant("World"), 'Continent', 'Country_Map', 'Volcano_Type'],
            values='Eruptions',
            color='Volcano_Type',
            custom_data=['Volcano_List'],
            color_discrete_sequence=px.colors.qualitative.Bold,
            title="Continent → Country → Type (sized by eruption count)"
        )
        # Template choice: clean label inside the rectangle (avoids text overflow on small tiles),
        # full volcano list visible in the hover tooltip.
        fig5.update_traces(
            texttemplate='<b>%{label}</b>',
            textposition='middle center',
            textfont_size=11,
            hovertemplate=(
                '<b>%{label}</b><br>'
                'Eruptions: %{value}<br><br>'
                '%{customdata[0]}'
                '<extra></extra>'
            )
        )
        fig5.update_layout(margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig5, width='stretch', theme="streamlit")
    else:
        st.info("No national data available for treemap visualization.")
        
with text_col:
    st.markdown("""
        ### Interpretation
        The treemap presents a hierarchical decomposition of global volcanic activity.
        Data is organized according to:
        World → Continent → Country → Volcano Type
        Rectangle size represents the number of significant eruptions, while colors distinguish volcano morphologies.
        This structure reveals geographical concentration patterns and dominant volcanic forms across regions.

        ### Visualization Design
        Treemaps are particularly effective for displaying hierarchical datasets while simultaneously encoding quantitative information through area.
        Interactive tooltips expose detailed volcano information while maintaining a compact layout.
    """)
    
st.divider()
chart_col, text_col = st.columns([2,1])

with chart_col:
    st.subheader("6. The 10 Deadliest Volcanoes in History")

    deadliest_volcanoes = (
        plot_df.groupby(['Volcano Name', 'Volcano_Type'])['Total_Deaths']
        .sum()
        .reset_index()
        .sort_values(by='Total_Deaths', ascending=False)
        .head(10)
    )

    if not deadliest_volcanoes.empty and deadliest_volcanoes['Total_Deaths'].sum() > 0:
        fig6 = px.bar(
            deadliest_volcanoes, x='Total_Deaths', y='Volcano Name',
            color='Volcano_Type', orientation='h',
            title="Historical ranking by cumulative mortality",
            labels={
                'Total_Deaths': 'Historical Total Casualties (Secondary Effects Included)',
                'Volcano Name': 'Volcano Name'
            },
            color_discrete_sequence=px.colors.qualitative.Safe
        )
        fig6.update_traces(texttemplate='%{x:,.0f}', textposition='outside', cliponaxis=False)
        fig6.update_layout(
            xaxis=dict(range=[0, deadliest_volcanoes['Total_Deaths'].max() * 1.18]),
            yaxis={'categoryorder': 'total ascending'},
            margin=dict(l=20, r=20, t=40, b=20),
            legend=dict(title="Morphology")
        )
        st.plotly_chart(fig6, width='stretch', theme="streamlit")
    else:
        st.info("No fatalities recorded for the selected interval or area.")
        
with text_col:
    st.markdown("""
        ### Interpretation
        This ranking identifies the volcanoes responsible for the highest cumulative number of fatalities in recorded history.
        The chart emphasizes long-term human impact rather than eruption frequency or eruption intensity.
        It highlights how a relatively small number of volcanoes account for a significant proportion of recorded casualties.

        ### Visualization Design
        Ranking tasks are naturally represented using sorted horizontal bar charts.
        This format improves label readability and facilitates comparison among entities with large numerical differences.
        Interactive filtering inherited from the dashboard enables users to explore how rankings change across regions and historical periods.
    """)