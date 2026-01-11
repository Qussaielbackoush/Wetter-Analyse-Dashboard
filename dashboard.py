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

# --- 3. HAUPTBEREICH: GLOBALE HIGHLIGHTS ---
st.title("📊 Wetter & Wind Master-Statistik")

if df_filtered.empty:
    st.warning("Bitte wählen Sie mindestens ein Jahr in der Sidebar aus.")
else:
    # --- REKORDE BERECHNEN ---
    t_max_row = df_filtered.loc[df_filtered['temperature'].idxmax()]
    t_min_row = df_filtered.loc[df_filtered['temperature'].idxmin()]
    w_max_row = df_filtered.loc[df_filtered['wind_speed'].idxmax()]

    # Temperatur oben
    st.subheader("🌡️ Temperatur Highlights")
    tc1, tc2, tc3 = st.columns(3)
    tc1.metric("Ø Temperatur", f"{df_filtered['temperature'].mean():.2f} °C")
    tc2.metric("Absolutes Maximum", f"{t_max_row['temperature']:.1f} °C", f"Jahr: {t_max_row['Jahr']}")
    tc3.metric("Absolutes Minimum", f"{t_min_row['temperature']:.1f} °C", f"Jahr: {t_min_row['Jahr']}", delta_color="inverse")

    # Wind unten
    st.subheader("🌬️ Wind Highlights")
    wc1, wc2, wc3 = st.columns(3)
    wc1.metric("Ø Windgeschwindigkeit", f"{df_filtered['wind_speed'].mean():.2f} m/s")
    wc2.metric("Stärkste Böe", f"{w_max_row['wind_speed']:.1f} m/s", f"Jahr: {w_max_row['Jahr']}")
    wc3.empty() 

    st.divider()

    # --- 4. TRENDS (SAISONALER VERGLEICH) ---
    col_l, col_r = st.columns(2)

    with col_l:
        st.subheader("📈 Temperatur-Trend")
        df_t_trend = df_filtered.groupby(['Jahr', 'Jahreszeit'])['temperature'].mean().reset_index()
        fig_t = px.line(df_t_trend, x='Jahr', y='temperature', color='Jahreszeit', markers=True,
                        color_discrete_map={'Winter': '#00B4D8', 'Sommer': '#FFB703', 'Frühling': '#2D6A4F', 'Herbst': '#BA181B'})
        st.plotly_chart(fig_t, use_container_width=True)

    with col_r:
        st.subheader("🌬️ Wind-Trend")
        df_w_trend = df_filtered.groupby(['Jahr', 'Jahreszeit'])['wind_speed'].mean().reset_index()
        fig_w = px.line(df_w_trend, x='Jahr', y='wind_speed', color='Jahreszeit', markers=True,
                        color_discrete_map={'Winter': '#00B4D8', 'Sommer': '#FFB703', 'Frühling': '#2D6A4F', 'Herbst': '#BA181B'})
        st.plotly_chart(fig_w, use_container_width=True)

    st.divider()

    # --- 5. MONATLICHE HEATMAPS ---
    st.subheader("📅 Monatlicher Durchschnittsvergleich")
    monats_reihenfolge = ['January', 'February', 'March', 'April', 'May', 'June', 
                          'July', 'August', 'September', 'October', 'November', 'December']
    
    h_col1, h_col2 = st.columns(2)

    with h_col1:
        st.markdown("**Ø Temperatur pro Monat/Jahr**")
        t_heat = df_filtered.pivot_table(index='Monat', columns='Jahr', values='temperature', aggfunc='mean').reindex(monats_reihenfolge)
        fig_h_t = px.imshow(t_heat, text_auto=".1f", color_continuous_scale='RdBu_r')
        st.plotly_chart(fig_h_t, use_container_width=True)

    with h_col2:
        st.markdown("**Ø Windstärke pro Monat/Jahr**")
        w_heat = df_filtered.pivot_table(index='Monat', columns='Jahr', values='wind_speed', aggfunc='mean').reindex(monats_reihenfolge)
        fig_h_w = px.imshow(w_heat, text_auto=".1f", color_continuous_scale='Blues')
        st.plotly_chart(fig_h_w, use_container_width=True)
