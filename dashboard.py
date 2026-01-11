import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- 1. KONFIGURATION ---
st.set_page_config(page_title="Wetter & Wind Analyse Pro", layout="wide")

@st.cache_data
def load_data():
    pfad = "data_04.csv" 
    if not os.path.exists(pfad):
        st.error(f"Datei '{pfad}' nicht gefunden!")
        st.stop()
    
    df = pd.read_csv(pfad, sep=None, engine='python')
    df.columns = df.columns.str.strip()
    df = df.rename(columns={'temperature_C': 'temperature', 'wind_speed_m_s': 'wind_speed'})
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Hilfsspalten
    df['Jahr'] = df['timestamp'].dt.year
    df['Monat_Nr'] = df['timestamp'].dt.month
    df['Monat'] = df['timestamp'].dt.month_name()
    df['Stunde'] = df['timestamp'].dt.hour
    
    def get_season(m):
        if m in [12, 1, 2]: return 'Winter'
        if m in [3, 4, 5]: return 'Frühling'
        if m in [6, 7, 8]: return 'Sommer'
        return 'Herbst'
    df['Jahreszeit'] = df['Monat_Nr'].apply(get_season)
    return df

df = load_data()

# --- 2. SIDEBAR FILTER ---
st.sidebar.header("Zeitraum wählen")
verfügbare_jahre = sorted(df['Jahr'].unique())
ausgewählte_jahre = st.sidebar.multiselect("Jahre auswählen:", options=verfügbare_jahre, default=verfügbare_jahre)
df_filtered = df[df['Jahr'].isin(ausgewählte_jahre)]

# --- 3. DASHBOARD HAUPTBEREICH ---
st.title("📊 Wetter & Wind Master-Statistik")

if df_filtered.empty:
    st.warning("Bitte wählen Sie mindestens ein Jahr aus.")
else:
    # --- BERECHNUNGEN ---
    t_max_row = df_filtered.loc[df_filtered['temperature'].idxmax()]
    t_min_row = df_filtered.loc[df_filtered['temperature'].idxmin()]
    w_max_row = df_filtered.loc[df_filtered['wind_speed'].idxmax()]
    
    hourly_wind = df_filtered.groupby('Stunde')['wind_speed'].mean()
    windiest_hour = hourly_wind.idxmax()
    avg_wind_speed = df_filtered['wind_speed'].mean()

    # --- KPI HIGHLIGHTS ---
    st.subheader("Temperatur & Wind Highlights")
    tc1, tc2, tc3 = st.columns(3)
    tc1.metric("Ø Temperatur", f"{df_filtered['temperature'].mean():.2f} °C")
    tc2.metric("Maximum", f"{t_max_row['temperature']:.1f} °C", f"Jahr: {t_max_row['Jahr']}")
    tc3.metric("Minimum", f"{t_min_row['temperature']:.1f} °C", f"Jahr: {t_min_row['Jahr']}", delta_color="inverse")

    st.subheader("Wind Highlights")
    wc1, wc2, wc3 = st.columns(3)
    wc1.metric("Ø Windgeschwindigkeit", f"{avg_wind_speed:.2f} m/s")
    wc2.metric("Stärkste Böe", f"{w_max_row['wind_speed']:.1f} m/s", f"Jahr: {w_max_row['Jahr']}")
    wc3.metric("Windieste Stunde", f"{windiest_hour}:00 Uhr", "Tages-Maximum")

    st.divider()
    
    # --- 4. TEMPERATUR: TREND & DISTRIBUTION ---
    st.subheader("🌡️ Temperatur: Entwicklung & Ausreißer")
    col_t1, col_t2 = st.columns([2, 1])
    
    with col_t1:
        df_t_trend = df_filtered.groupby(['Jahr', 'Jahreszeit'])['temperature'].mean().reset_index()
        fig_t_line = px.line(df_t_trend, x='Jahr', y='temperature', color='Jahreszeit', markers=True,
                             title="Saisonaler Trend",
                             color_discrete_map={'Winter': '#00B4D8', 'Sommer': '#FFB703', 'Frühling': '#2D6A4F', 'Herbst': '#BA181B'})
        st.plotly_chart(fig_t_line, use_container_width=True)
    
    with col_t2:
        fig_t_box = px.box(df_filtered, x='Jahreszeit', y='temperature', color='Jahreszeit',
                           title="Verteilung & Ausreißer",
                           color_discrete_map={'Winter': '#00B4D8', 'Sommer': '#FFB703', 'Frühling': '#2D6A4F', 'Herbst': '#BA181B'})
        st.plotly_chart(fig_t_box, use_container_width=True)

    st.divider()

    # --- 5. WIND: TREND & DISTRIBUTION ---
    st.subheader("🌬️ Wind: Entwicklung & Ausreißer")
    col_w1, col_w2 = st.columns([2, 1])
    
    with col_w1:
        df_w_trend = df_filtered.groupby(['Jahr', 'Jahreszeit'])['wind_speed'].mean().reset_index()
        fig_w_line = px.line(df_w_trend, x='Jahr', y='wind_speed', color='Jahreszeit', markers=True,
                             title="Saisonaler Trend",
                             color_discrete_map={'Winter': '#00B4D8', 'Sommer': '#FFB703', 'Frühling': '#2D6A4F', 'Herbst': '#BA181B'})
        st.plotly_chart(fig_w_line, use_container_width=True)
    
    with col_w2:
        fig_w_box = px.box(df_filtered, x='Jahreszeit', y='wind_speed', color='Jahreszeit',
                           title="Verteilung & Ausreißer",
                           color_discrete_map={'Winter': '#00B4D8', 'Sommer': '#FFB703', 'Frühling': '#2D6A4F', 'Herbst': '#BA181B'})
        st.plotly_chart(fig_w_box, use_container_width=True)

    st.divider()

    # --- 6. TAGESVERLAUF & HEATMAPS ---
    st.subheader("🕒 Tagesverlauf & 📅 Heatmaps")
    
    tab1, tab2 = st.tabs(["24h Verlauf", "Monatliche Matrix"])
    
    with tab1:
        hourly_stats = df_filtered.groupby('Stunde').agg({'temperature': 'mean', 'wind_speed': 'mean'}).reset_index()
        c1, c2 = st.columns(2)
        c1.plotly_chart(px.area(hourly_stats, x='Stunde', y='temperature', title="Ø Temp Verlauf"), use_container_width=True)
        c2.plotly_chart(px.area(hourly_stats, x='Stunde', y='wind_speed', title="Ø Wind Verlauf"), use_container_width=True)
    
    with tab2:
        m_order = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
        h1, h2 = st.columns(2)
        t_heat = df_filtered.pivot_table(index='Monat', columns='Jahr', values='temperature', aggfunc='mean').reindex(m_order)
        w_heat = df_filtered.pivot_table(index='Monat', columns='Jahr', values='wind_speed', aggfunc='mean').reindex(m_order)
        h1.plotly_chart(px.imshow(t_heat, text_auto=".1f", color_continuous_scale='RdBu_r', title="Heatmap Temp"), use_container_width=True)
        h2.plotly_chart(px.imshow(w_heat, text_auto=".1f", color_continuous_scale='Blues', title="Heatmap Wind"), use_container_width=True)






