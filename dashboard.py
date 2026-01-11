import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- 1. KONFIGURATION ---
st.set_page_config(page_title="Wetter & Wind Analyse", layout="wide")

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
ausgewählte_jahre = st.sidebar.multiselect("Jahre:", options=verfügbare_jahre, default=verfügbare_jahre)
df_filtered = df[df['Jahr'].isin(ausgewählte_jahre)]

# --- 3. DASHBOARD HAUPTBEREICH ---
st.title("Wetter & Wind Master-Statistik")

if df_filtered.empty:
    st.warning("Bitte wählen Sie mindestens ein Jahr aus.")
else:
    # --- REIHE 1: REKORDE (KPIs) ---
    t_max_row = df_filtered.loc[df_filtered['temperature'].idxmax()]
    t_min_row = df_filtered.loc[df_filtered['temperature'].idxmin()]
    w_max_row = df_filtered.loc[df_filtered['wind_speed'].idxmax()]

    st.subheader("Historische Höchst- und Tiefstwerte")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Ø Temperatur", f"{df_filtered['temperature'].mean():.2f} °C")
    k2.metric("Max Temp", f"{t_max_row['temperature']:.1f} °C", f"Jahr: {t_max_row['Jahr']}")
    k3.metric("Min Temp", f"{t_min_row['temperature']:.1f} °C", f"Jahr: {t_min_row['Jahr']}", delta_color="inverse")
    k4.metric("Stärkster Wind", f"{w_max_row['wind_speed']:.1f} m/s", f"Jahr: {w_max_row['Jahr']}")

    st.divider()

    # --- REIHE 2: TEMPERATUR TREND & WIND VERTEILUNG ---
    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.subheader("Saisonaler Temperatur-Trend")
        # Aggregierte Daten für saubere Linien
        df_trend = df_filtered.groupby(['Jahr', 'Jahreszeit'])['temperature'].mean().reset_index()
        fig_trend = px.line(df_trend, x='Jahr', y='temperature', color='Jahreszeit', markers=True,
                            color_discrete_map={'Winter': '#00B4D8', 'Sommer': '#FFB703', 'Frühling': '#2D6A4F', 'Herbst': '#BA181B'})
        st.plotly_chart(fig_trend, use_container_width=True)

    with col_right:
        st.subheader("Wind-Verteilung")
        # Histogramm ist die beste "Statistik-Grafik" für Wind
        fig_wind_hist = px.histogram(df_filtered, x='wind_speed', nbins=20, 
                                    color_discrete_sequence=['#457B9D'],
                                    labels={'wind_speed': 'Wind (m/s)'})
        st.plotly_chart(fig_wind_hist, use_container_width=True)

    st.divider()

    # --- REIHE 3: TAGESVERLAUF & BOXPLOT ---
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Temperatur nach Tageszeit")
        hourly = df_filtered.groupby('Stunde')['temperature'].mean().reset_index()
        fig_hour = px.area(hourly, x='Stunde', y='temperature', color_discrete_sequence=['#E63946'])
        st.plotly_chart(fig_hour, use_container_width=True)

    with col_b:
        st.subheader("Temperatur-Streuung (Box-Plot)")
        fig_box = px.box(df_filtered, x='Jahreszeit', y='temperature', color='Jahreszeit',
                         color_discrete_map={'Winter': '#00B4D8', 'Sommer': '#FFB703', 'Frühling': '#2D6A4F', 'Herbst': '#BA181B'})
        st.plotly_chart(fig_box, use_container_width=True)

    # --- REIHE 4: DIE GROSSE MATRIX ---
    st.divider()
    st.subheader("Saisonale Statistik-Matrix")
    
    # Kombinierte Tabelle für Temp und Wind
    stats_matrix = df_filtered.groupby(['Jahr', 'Jahreszeit']).agg(
        Avg_Temp=('temperature', 'mean'),
        Max_Temp=('temperature', 'max'),
        Avg_Wind=('wind_speed', 'mean'),
        Max_Wind=('wind_speed', 'max')
    ).reset_index()

    st.dataframe(
        stats_matrix.style.background_gradient(subset=['Avg_Temp'], cmap='YlOrRd')
                          .background_gradient(subset=['Avg_Wind'], cmap='Blues'),
        use_container_width=True
    )
