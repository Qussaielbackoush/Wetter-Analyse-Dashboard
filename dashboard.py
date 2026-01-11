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
    df['Datum'] = df['timestamp'].dt.date
    
    def get_season(m):
        if m in [12, 1, 2]: return 'Winter'
        if m in [3, 4, 5]: return 'Frühling'
        if m in [6, 7, 8]: return 'Sommer'
        return 'Herbst'
    df['Jahreszeit'] = df['Monat_Nr'].apply(get_season)
    return df

df = load_data()

# --- 2. SIDEBAR FILTER ---
st.sidebar.header("⚙️ Einstellungen")

# NEU: Filter für die Metrik
auswahl_metrik = st.sidebar.radio(
    "Haupt-Analyse für:",
    ["Temperatur", "Windgeschwindigkeit"]
)

# Zuordnung der Spalten basierend auf Auswahl
if auswahl_metrik == "Temperatur":
    ziel_spalte = 'temperature'
    einheit = "°C"
    farbe = "RdBu_r"
else:
    ziel_spalte = 'wind_speed'
    einheit = "m/s"
    farbe = "Blues"

st.sidebar.divider()
verfügbare_jahre = sorted(df['Jahr'].unique())
ausgewählte_jahre = st.sidebar.multiselect("Jahre auswählen:", options=verfügbare_jahre, default=verfügbare_jahre)

df_filtered = df[df['Jahr'].isin(ausgewählte_jahre)]

# --- 3. DASHBOARD HAUPTBEREICH ---
st.title(f" Wetter Analyse: {auswahl_metrik}")

if df_filtered.empty:
    st.warning("Keine Daten für die Auswahl vorhanden.")
else:
    # --- KPIs ---
    kpi_val_max = df_filtered.loc[df_filtered[ziel_spalte].idxmax()]
    kpi_val_min = df_filtered.loc[df_filtered[ziel_spalte].idxmin()]
    avg_val = df_filtered[ziel_spalte].mean()

    col1, col2, col3 = st.columns(3)
    col1.metric(f"Ø {auswahl_metrik}", f"{avg_val:.2f} {einheit}")
    col2.metric(f"Höchster Wert", f"{kpi_val_max[ziel_spalte]:.2f} {einheit}", f"Jahr: {kpi_val_max['Jahr']}")
    col3.metric(f"Tiefster Wert", f"{kpi_val_min[ziel_spalte]:.2f} {einheit}", f"Jahr: {kpi_val_min['Jahr']}", delta_color="inverse")

    st.divider()

    # --- 4. TREND & VERTEILUNG ---
    spalte_links, spalte_rechts = st.columns([2, 1])

    with spalte_links:
        st.subheader(f"Saisonaler Trend ({einheit})")
        df_trend = df_filtered.groupby(['Jahr', 'Jahreszeit'])[ziel_spalte].mean().reset_index()
        fig_trend = px.line(df_trend, x='Jahr', y=ziel_spalte, color='Jahreszeit', markers=True,
                            color_discrete_map={'Winter': '#00B4D8', 'Sommer': '#FFB703', 'Frühling': '#2D6A4F', 'Herbst': '#BA181B'})
        st.plotly_chart(fig_trend, use_container_width=True)

    with spalte_rechts:
        st.subheader("Verteilung (Box-Plot)")
        fig_box = px.box(df_filtered, x='Jahreszeit', y=ziel_spalte, color='Jahreszeit',
                         color_discrete_map={'Winter': '#00B4D8', 'Sommer': '#FFB703', 'Frühling': '#2D6A4F', 'Herbst': '#BA181B'})
        st.plotly_chart(fig_box, use_container_width=True)

    st.divider()

    # --- 5. TAGESVERLAUF & HISTOGRAMM ---
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Durchschnittlicher Tagesverlauf")
        hourly_stats = df_filtered.groupby('Stunde')[ziel_spalte].mean().reset_index()
        fig_hour = px.area(hourly_stats, x='Stunde', y=ziel_spalte, title=f"{auswahl_metrik} über 24h")
        st.plotly_chart(fig_hour, use_container_width=True)

    with col_b:
        st.subheader(f"Häufigkeit der {auswahl_metrik}")
        fig_hist = px.histogram(df_filtered, x=ziel_spalte, nbins=30, marginal="rug", 
                                title=f"Wie oft kommen welche Werte vor?",
                                color_discrete_sequence=['#457B9D'])
        st.plotly_chart(fig_hist, use_container_width=True)

    # --- 6. HEATMAP & MATRIX ---
    st.divider()
    st.subheader(f"Monatliche Heatmap: {auswahl_metrik}")
    
    heatmap_data = df_filtered.pivot_table(
        index='Monat', columns='Jahr', values=ziel_spalte, aggfunc='mean'
    ).reindex(['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'])

    fig_heat = px.imshow(heatmap_data, text_auto=".1f", color_continuous_scale=farbe)
    st.plotly_chart(fig_heat, use_container_width=True)

    with st.expander("Detaillierte Statistik-Matrix anzeigen"):
        stats_pivot = df_filtered.groupby(['Jahr', 'Jahreszeit']).agg(
            Durchschnitt=(ziel_spalte, 'mean'),
            Max=(ziel_spalte, 'max'),
            Min=(ziel_spalte, 'min')
        ).reset_index()
        st.dataframe(stats_pivot.style.background_gradient(subset=['Durchschnitt'], cmap='YlOrRd'), use_container_width=True)
