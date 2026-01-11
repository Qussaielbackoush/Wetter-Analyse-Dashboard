import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- 1. KONFIGURATION ---
st.set_page_config(page_title="Wetter-Analyse Dashboard", layout="wide")

@st.cache_data
def load_data():
    pfad = "data_04.csv" 
    
    if not os.path.exists(pfad):
        st.error(f"Datei '{pfad}' nicht gefunden!")
        st.stop()
    
    # Daten laden und Spalten säubern
    df = pd.read_csv(pfad, sep=None, engine='python')
    df.columns = df.columns.str.strip()
    
    # Spalten umbenennen
    df = df.rename(columns={'temperature_C': 'temperature', 'wind_speed_m_s': 'wind_speed'})
    
    # Zeitstempel umwandeln
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # --- ALLE HILFSSPALTEN HIER ERSTELLEN ---
    df['Jahr'] = df['timestamp'].dt.year
    df['Monat_Nr'] = df['timestamp'].dt.month
    df['Monat'] = df['timestamp'].dt.month_name()
    df['Stunde'] = df['timestamp'].dt.hour
    df['Datum'] = df['timestamp'].dt.date
    
    # Jahreszeiten Logik
    def get_season(m):
        if m in [12, 1, 2]: return 'Winter'
        if m in [3, 4, 5]: return 'Frühling'
        if m in [6, 7, 8]: return 'Sommer'
        return 'Herbst'
    df['Jahreszeit'] = df['Monat_Nr'].apply(get_season)
    
    return df

# Daten initial laden
df = load_data()

# --- 2. SIDEBAR FILTER ---
st.sidebar.header("Filter-Optionen")
verfügbare_jahre = sorted(df['Jahr'].unique())
ausgewählte_jahre = st.sidebar.multiselect("Jahre auswählen:", options=verfügbare_jahre, default=verfügbare_jahre)

# Filter anwenden
df_filtered = df[df['Jahr'].isin(ausgewählte_jahre)]

# --- 3. DASHBOARD HAUPTBEREICH ---
st.title("Wetter Analyse Dashboard")

if df_filtered.empty:
    st.warning("Keine Daten für die Auswahl vorhanden.")
else:
    # Metriken
    global_max = df_filtered.loc[df_filtered['temperature'].idxmax()]
    global_min = df_filtered.loc[df_filtered['temperature'].idxmin()]
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Ø Temperatur", f"{df_filtered['temperature'].mean():.2f} °C")
    m2.metric("Höchster Wert", f"{global_max['temperature']:.2f} °C", f"Jahr: {global_max['Jahr']}")
    m3.metric("Tiefster Wert", f"{global_min['temperature']:.2f} °C", f"Jahr: {global_min['Jahr']}", delta_color="inverse")

    st.divider()

    # --- 4. TRENDLINIE (SAUBER) ---
    st.subheader("Saisonale Trends")
    # Gruppieren für saubere Linien (kein Scatter-Chaos)
    df_trend = df_filtered.groupby(['Jahr', 'Jahreszeit'])['temperature'].mean().reset_index()
    
    fig_trend = px.line(df_trend, x='Jahr', y='temperature', color='Jahreszeit', 
                        markers=True, title="Durchschnittstemp. Trend pro Saison",
                        color_discrete_map={'Winter': '#00B4D8', 'Sommer': '#FFB703', 'Frühling': '#2D6A4F', 'Herbst': '#BA181B'})
    st.plotly_chart(fig_trend, use_container_width=True)

    # --- 5. TAGESVERLAUF (STUNDE) ---
    st.subheader("Durchschnittlicher Tagesverlauf")
    # Hier wird die Spalte 'Stunde' verwendet
    hourly_stats = df_filtered.groupby('Stunde')['temperature'].mean().reset_index()
    fig_hour = px.area(hourly_stats, x='Stunde', y='temperature', title="Temperaturkurve über 24h")
    st.plotly_chart(fig_hour, use_container_width=True)

    # --- 6. STATISTIK MATRIX ---
    st.subheader("Statistik-Matrix (Jahr & Saison)")
    stats_pivot = df_filtered.groupby(['Jahr', 'Jahreszeit']).agg(
        Avg_Temp=('temperature', 'mean'),
        Max_Temp=('temperature', 'max'),
        Min_Temp=('temperature', 'min')
    ).reset_index()
    
    st.dataframe(stats_pivot.style.background_gradient(subset=['Avg_Temp'], cmap='YlOrRd'), use_container_width=True)
    # --- 7. HEATMAP ---
    st.divider()
    st.subheader("Temperatur-Heatmap")
    # Korrigiert: aggfunc statt agg_func
    heatmap_data = df_filtered.pivot_table(
         index='Monat', 
         columns='Jahr', 
         values='temperature', 
         aggfunc='mean' 
    ).reindex(['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'])

    fig_heat = px.imshow(heatmap_data, text_auto=".1f", color_continuous_scale='RdBu_r')
    st.plotly_chart(fig_heat, use_container_width=True)



