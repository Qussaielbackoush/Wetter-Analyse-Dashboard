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
st.sidebar.header("⚙️ Analyse-Einstellungen")

# Filter für die Metrik
auswahl_metrik = st.sidebar.selectbox(
    "Welche Daten möchtest du analysieren?",
    ["Temperatur", "Windgeschwindigkeit"]
)

# Dynamische Variablen basierend auf Auswahl
if auswahl_metrik == "Temperatur":
    spalte = 'temperature'
    einheit = "°C"
    cmap = "RdBu_r"
else:
    spalte = 'wind_speed'
    einheit = "m/s"
    cmap = "Blues"

st.sidebar.divider()
verfügbare_jahre = sorted(df['Jahr'].unique())
ausgewählte_jahre = st.sidebar.multiselect("Jahre auswählen:", options=verfügbare_jahre, default=verfügbare_jahre)

df_filtered = df[df['Jahr'].isin(ausgewählte_jahre)]

# --- 3. DASHBOARD HAUPTBEREICH ---
st.title(f"📊 Analyse: {auswahl_metrik}")

if df_filtered.empty:
    st.warning("Bitte wählen Sie mindestens ein Jahr in der Sidebar aus.")
else:
    # Metriken (KPIs)
    val_max = df_filtered.loc[df_filtered[spalte].idxmax()]
    val_min = df_filtered.loc[df_filtered[spalte].idxmin()]
    avg_total = df_filtered[spalte].mean()

    m1, m2, m3 = st.columns(3)
    m1.metric(f"Ø {auswahl_metrik}", f"{avg_total:.2f} {einheit}")
    m2.metric("Höchster Wert", f"{val_max[spalte]:.2f} {einheit}", f"Jahr: {val_max['Jahr']}")
    m3.metric("Tiefster Wert", f"{val_min[spalte]:.2f} {einheit}", f"Jahr: {val_min['Jahr']}")

    st.divider()

    # --- 4. TRENDS & DISTRIBUTION ---
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader(f"Saisonaler Trend ({einheit})")
        df_trend = df_filtered.groupby(['Jahr', 'Jahreszeit'])[spalte].mean().reset_index()
        fig_trend = px.line(df_trend, x='Jahr', y=spalte, color='Jahreszeit', markers=True,
                            color_discrete_map={'Winter': '#00B4D8', 'Sommer': '#FFB703', 'Frühling': '#2D6A4F', 'Herbst': '#BA181B'})
        st.plotly_chart(fig_trend, use_container_width=True)

    with col2:
        st.subheader("Verteilung (Box-Plot)")
        # Ein Boxplot zeigt die Streuung und Ausreißer perfekt an
        fig_box = px.box(df_filtered, x='Jahreszeit', y=spalte, color='Jahreszeit',
                         color_discrete_map={'Winter': '#00B4D8', 'Sommer': '#FFB703', 'Frühling': '#2D6A4F', 'Herbst': '#BA181B'})
        st.plotly_chart(fig_box, use_container_width=True)

    # --- 5. TAGESVERLAUF & HISTOGRAMM ---
    st.divider()
    col3, col4 = st.columns(2)

    with col3:
        st.subheader("Durchschnittlicher Tagesverlauf")
        hourly_stats = df_filtered.groupby('Stunde')[spalte].mean().reset_index()
        fig_hour = px.area(hourly_stats, x='Stunde', y=spalte, title=f"Ø Verlauf über 24h")
        st.plotly_chart(fig_hour, use_container_width=True)

    with col4:
        st.subheader("Häufigkeitsverteilung (Histogramm)")
        # Zeigt wie oft bestimmte Windstärken/Temperaturen vorkommen
        fig_hist = px.histogram(df_filtered, x=spalte, nbins=30, 
                                title=f"Verteilung der {auswahl_metrik}-Werte",
                                color_discrete_sequence=['#457B9D'], marginal="rug")
        st.plotly_chart(fig_hist, use_container_width=True)

    # --- 6. HEATMAP ---
    st.divider()
    st.subheader(f"Monatliche Heatmap ({auswahl_metrik})")
    
    heatmap_data = df_filtered.pivot_table(
        index='Monat', columns='Jahr', values=spalte, aggfunc='mean'
    ).reindex(['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'])

    fig_heat = px.imshow(heatmap_data, text_auto=".1f", color_continuous_scale=cmap)
    st.plotly_chart(fig_heat, use_container_width=True)
