import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- 1. KONFIGURATION ---
st.set_page_config(page_title="Wetter-Analyse Dashboard ", layout="wide")

@st.cache_data
def load_data():
    pfad = "data_04.csv"
    if not os.path.exists(pfad):
        st.error("Datei nicht gefunden!")
        st.stop()
    
    df = pd.read_csv(pfad, sep=None, engine='python')
    df.columns = df.columns.str.strip()
    df = df.rename(columns={'temperature_C': 'temperature', 'wind_speed_m_s': 'wind_speed'})
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
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

# --- 2. SIDEBAR ---
st.sidebar.header("Filter")
jahre = st.sidebar.multiselect("Jahre:", options=sorted(df['Jahr'].unique()), default=sorted(df['Jahr'].unique()))
df_filtered = df[df['Jahr'].isin(jahre)]

# --- 3. GLOBALE REKORDE ---
st.title("Wetter Analyse Dashboard")
global_max_row = df_filtered.loc[df_filtered['temperature'].idxmax()]
global_min_row = df_filtered.loc[df_filtered['temperature'].idxmin()]

c1, c2, c3 = st.columns(3)
c1.metric("Ø Temperatur", f"{df_filtered['temperature'].mean():.2f} °C")
c2.metric("Höchste Temp", f"{global_max_row['temperature']:.2f} °C", f"Jahr: {global_max_row['Jahr']}")
c3.metric("Tiefste Temp", f"{global_min_row['temperature']:.2f} °C", f"Jahr: {global_min_row['Jahr']}", delta_color="inverse")

st.divider()

# --- 4. SAUBERER TREND  ---
st.subheader("Saisonale Temperaturentwicklung (Durchschnittswerte)")
st.write("Hier sehen Sie nur die bereinigten Trendlinien der Durchschnittstemperatur pro Saison über die Jahre.")

# Daten aggregieren für klare Linien (Mittelwert pro Jahr und Saison)
df_trend = df_filtered.groupby(['Jahr', 'Jahreszeit'])['temperature'].mean().reset_index()

fig_trend = px.line(
    df_trend, 
    x='Jahr', 
    y='temperature', 
    color='Jahreszeit',
    markers=True, # Zeigt nur die Jahres-Durchschnittspunkte
    title="Trend der saisonalen Durchschnittstemperaturen",
    labels={'temperature': 'Ø Temperatur (°C)', 'Jahr': 'Jahr'},
    color_discrete_map={'Winter': '#00B4D8', 'Sommer': '#FFB703', 'Frühling': '#2D6A4F', 'Herbst': '#BA181B'}
)

# Trendlinie hinzufügen (Optional, aber jetzt auf sauberen Daten)
st.plotly_chart(fig_trend, use_container_width=True)

st.divider()

# --- 5. STATISTIK MATRIX ---
st.subheader("Statistik-Matrix (Jahr & Saison)")
# Monat wurde entfernt für bessere Übersicht
stats_pivot = df_filtered.groupby(['Jahr', 'Jahreszeit']).agg(
    Durchschnitt_Temp=('temperature', 'mean'),
    Max_Temp=('temperature', 'max'),
    Min_Temp=('temperature', 'min')
).reset_index()

st.dataframe(stats_pivot.style.background_gradient(subset=['Durchschnitt_Temp'], cmap='YlOrRd'), use_container_width=True)

# --- 6. HEATMAP ---
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

st.divider()
st.header("🔍 Fortgeschrittene Analysen")

col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Typischer Tagesverlauf")
    # Durchschnittliche Temperatur pro Stunde berechnen
    hourly_profile = df_filtered.groupby('Stunde')['temperature'].mean().reset_index()
    fig_hourly = px.line(hourly_profile, x='Stunde', y='temperature', 
                         title="Ø Temperatur nach Uhrzeit",
                         labels={'temperature': 'Temp (°C)', 'Stunde': 'Uhrzeit (0-23)'})
    st.plotly_chart(fig_hourly, use_container_width=True)

with col_b:
    st.subheader("Temperatur-Stabilität (Boxplot)")
    # Zeigt die Streuung der Daten pro Jahreszeit
    fig_box = px.box(df_filtered, x='Jahreszeit', y='temperature', 
                     color='Jahreszeit',
                     title="Temperatur-Streuung pro Saison",
                     color_discrete_map={'Winter': '#00B4D8', 'Sommer': '#FFB703', 'Frühling': '#2D6A4F', 'Herbst': '#BA181B'})
    st.plotly_chart(fig_box, use_container_width=True)

# 7. Volatilitäts-Check
st.subheader("Größte Temperatur-Schwankungen")
# Delta pro Tag berechnen
daily_delta = df_filtered.groupby('Datum')['temperature'].agg(['max', 'min']).reset_index()
daily_delta['Delta'] = daily_delta['max'] - daily_delta['min']
top_deltas = daily_delta.sort_values(by='Delta', ascending=False).head(5)

st.write("Tage mit den extremsten Temperaturunterschieden:")
st.table(top_deltas)


