import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- 1. KONFIGURATION ---
st.set_page_config(page_title="Wetter-Analyse", layout="wide")

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
    
    # Hilfsspalten erstellen
    df['Jahr'] = df['timestamp'].dt.year
    df['Monat_Nr'] = df['timestamp'].dt.month
    df['Monat'] = df['timestamp'].dt.month_name()
    df['Stunde'] = df['timestamp'].dt.hour
    df['Datum'] = df['timestamp'].dt.date
    
    def get_season(m):
        if m in [12, 1, 2]: return 'Winter'
        if m in [3, 4, 5]: return 'Frühling'
        if m in [6, 7, 8]: return 'Sommer'
        return 'Herbst'
    df['Jahreszeit'] = df['Monat_Nr'].apply(get_season)
    return df

df = load_data()

# --- 2. SIDEBAR ---
st.sidebar.header("Filter")
verfügbare_jahre = sorted(df['Jahr'].unique())
ausgewählte_jahre = st.sidebar.multiselect("Jahre auswählen:", options=verfügbare_jahre, default=verfügbare_jahre)
df_filtered = df[df['Jahr'].isin(ausgewählte_jahre)]

# --- 3. HAUPTBEREICH: STATISTIK-BOARD ---
st.title("Wetter & 💨 Wind Statistik")

if df_filtered.empty:
    st.warning("Bitte wählen Sie mindestens ein Jahr aus.")
else:
    # --- REKORDE BERECHNEN ---
    t_max = df_filtered.loc[df_filtered['temperature'].idxmax()]
    t_min = df_filtered.loc[df_filtered['temperature'].idxmin()]
    w_max = df_filtered.loc[df_filtered['wind_speed'].idxmax()] # Höchste Windgeschwindigkeit
    
    # KPI REIHE 1: TEMPERATUR
    st.subheader("Temperatur Highlights")
    c1, c2, c3 = st.columns(3)
    c1.metric("Ø Temperatur", f"{df_filtered['temperature'].mean():.2f} °C")
    c2.metric("Höchste Temp", f"{t_max['temperature']:.2f} °C", f"Jahr: {t_max['Jahr']}")
    c3.metric("Tiefste Temp", f"{t_min['temperature']:.2f} °C", f"Jahr: {t_min['Jahr']}", delta_color="inverse")

    # KPI REIHE 2: WIND
    st.subheader("Wind Highlights")
    w1, w2, w3 = st.columns(3)
    w1.metric("Ø Windgeschwindigkeit", f"{df_filtered['wind_speed'].mean():.2f} m/s")
    w2.metric("Stärkste Böe", f"{w_max['wind_speed']:.2f} m/s", f"Jahr: {w_max['Jahr']}")
    w3.metric("Messzeitpunkt Böe", w_max['timestamp'].strftime('%d.%m.%Y'))

    st.divider()

    # --- 4. GRAFIKEN (NUR FÜR TEMPERATUR) ---
    st.subheader("📈 Temperatur Analyse")
    
    col_l, col_r = st.columns([2, 1])
    
    with col_l:
        # Sauberer Trend
        df_trend = df_filtered.groupby(['Jahr', 'Jahreszeit'])['temperature'].mean().reset_index()
        fig_trend = px.line(df_trend, x='Jahr', y='temperature', color='Jahreszeit', markers=True,
                            title="Saisonaler Temperaturtrend",
                            color_discrete_map={'Winter': '#00B4D8', 'Sommer': '#FFB703', 'Frühling': '#2D6A4F', 'Herbst': '#BA181B'})
        st.plotly_chart(fig_trend, use_container_width=True)
    
    with col_r:
        # Verteilung (Boxplot ist super für Temperatur)
        fig_box = px.box(df_filtered, x='Jahreszeit', y='temperature', color='Jahreszeit',
                         title="Temperatur-Streuung",
                         color_discrete_map={'Winter': '#00B4D8', 'Sommer': '#FFB703', 'Frühling': '#2D6A4F', 'Herbst': '#BA181B'})
        st.plotly_chart(fig_box, use_container_width=True)

    # --- 5. WIND VERTEILUNG ---
    st.subheader("Windstärke Verteilung")
    fig_hist = px.histogram(df_filtered, x='wind_speed', nbins=50, 
                           title="Wie oft treten welche Windgeschwindigkeiten auf?",
                           labels={'wind_speed': 'Windgeschwindigkeit (m/s)'},
                           color_discrete_sequence=['#457B9D'])
    st.plotly_chart(fig_hist, use_container_width=True)

    # --- 6. HEATMAP & MATRIX ---
    st.divider()
    st.subheader(" Temperatur Heatmap (Monat vs. Jahr)")
    heatmap_data = df_filtered.pivot_table(index='Monat', columns='Jahr', values='temperature', aggfunc='mean').reindex(
        ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
    )
    fig_heat = px.imshow(heatmap_data, text_auto=".1f", color_continuous_scale='RdBu_r')
    st.plotly_chart(fig_heat, use_container_width=True)
