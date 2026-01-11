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
    # --- REKORDE & STATISTIKEN BERECHNEN ---
    t_max_row = df_filtered.loc[df_filtered['temperature'].idxmax()]
    t_min_row = df_filtered.loc[df_filtered['temperature'].idxmin()]
    w_max_row = df_filtered.loc[df_filtered['wind_speed'].idxmax()]
    
    # Windieste Stunde berechnen
    hourly_wind = df_filtered.groupby('Stunde')['wind_speed'].mean()
    windiest_hour = hourly_wind.idxmax()
    max_hour_wind = hourly_wind.max()

    # --- KPI REIHE 1: TEMPERATUR ---
    st.subheader("🌡️ Temperatur Highlights")
    tc1, tc2, tc3 = st.columns(3)
    tc1.metric("Ø Temperatur", f"{df_filtered['temperature'].mean():.2f} °C")
    tc2.metric("Absolutes Maximum", f"{t_max_row['temperature']:.1f} °C", f"Jahr: {t_max_row['Jahr']}")
    tc3.metric("Absolutes Minimum", f"{t_min_row['temperature']:.1f} °C", f"Jahr: {t_min_row['Jahr']}", delta_color="inverse")

    # --- KPI REIHE 2: WIND ---
    st.subheader("🌬️ Wind Highlights")
    wc1, wc2, wc3 = st.columns(3)
    wc1.metric("Ø Windgeschwindigkeit", f"{df_filtered['wind_speed'].mean():.2f} m/s")
    wc2.metric("Stärkste Böe", f"{w_max_row['wind_speed']:.1f} m/s", f"Jahr: {w_max_row['Jahr']}")
    wc3.metric("Windieste Tageszeit", f"{windiest_hour}:00 Uhr", f"Schnitt: {max_hour_wind:.1f} m/s")

    st.divider()

    # --- REIHE 4: TAGESVERLAUF (24H KURVE) ---
    st.subheader("🕒 Durchschnittlicher Tagesverlauf (24h)")
    hourly_stats = df_filtered.groupby('Stunde').agg({'temperature': 'mean', 'wind_speed': 'mean'}).reset_index()
    
    c_day1, c_day2 = st.columns(2)
    with c_day1:
        fig_h_t = px.area(hourly_stats, x='Stunde', y='temperature', title="Temperaturkurve über den Tag", color_discrete_sequence=['#E63946'])
        st.plotly_chart(fig_h_t, use_container_width=True)
    with c_day2:
        fig_h_w = px.area(hourly_stats, x='Stunde', y='wind_speed', title="Windgeschwindigkeit über den Tag", color_discrete_sequence=['#457B9D'])
        st.plotly_chart(fig_h_w, use_container_width=True)

    

    st.divider()

    # --- REIHE 5: BOXPLOTS (OUTLIER ANALYSE) ---
    st.subheader("📦 Verteilung & Ausreißer (Boxplots)")
    st.info("Punkte außerhalb der Linien gelten statistisch als Ausreißer (Extremereignisse).")
    
    box_col1, box_col2 = st.columns(2)
    with box_col1:
        fig_box_t = px.box(df_filtered, x='Jahreszeit', y='temperature', color='Jahreszeit', 
                           title="Temperatur-Verteilung pro Saison",
                           color_discrete_map={'Winter': '#00B4D8', 'Sommer': '#FFB703', 'Frühling': '#2D6A4F', 'Herbst': '#BA181B'})
        st.plotly_chart(fig_box_t, use_container_width=True)
    with box_col2:
        fig_box_w = px.box(df_filtered, x='Jahreszeit', y='wind_speed', color='Jahreszeit', 
                           title="Wind-Verteilung pro Saison",
                           color_discrete_map={'Winter': '#00B4D8', 'Sommer': '#FFB703', 'Frühling': '#2D6A4F', 'Herbst': '#BA181B'})
        st.plotly_chart(fig_box_w, use_container_width=True)

    

    st.divider()

    # --- REIHE 6: TRENDS & HEATMAPS ---
    st.subheader("📅 Langzeit-Trends & Monatswerte")
    # Heatmaps (Kompakt nebeneinander)
    m_order = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
    h1, h2 = st.columns(2)
    with h1:
        t_heat = df_filtered.pivot_table(index='Monat', columns='Jahr', values='temperature', aggfunc='mean').reindex(m_order)
        st.plotly_chart(px.imshow(t_heat, text_auto=".1f", color_continuous_scale='RdBu_r', title="Ø Temp Heatmap"), use_container_width=True)
    with h2:
        w_heat = df_filtered.pivot_table(index='Monat', columns='Jahr', values='wind_speed', aggfunc='mean').reindex(m_order)
        st.plotly_chart(px.imshow(w_heat, text_auto=".1f", color_continuous_scale='Blues', title="Ø Wind Heatmap"), use_container_width=True)
