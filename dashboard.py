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

df_raw = load_data()

# --- 2. SIDEBAR FILTER & OUTLIER LOGIK ---
st.sidebar.header("⚙️ Daten-Bereinigung")

# Outlier Toggle
clean_outliers = st.sidebar.checkbox("Ausreißer entfernen (IQR-Methode)", value=False)

def filter_outliers(df, column):
    Q1 = df[column].quantile(0.25)
    Q3 = df[column].quantile(0.75)
    IQR = Q3 - Q1
    # Formel: Untere Grenze = Q1 - 1.5 * IQR | Obere Grenze = Q3 + 1.5 * IQR
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    return df[(df[column] >= lower_bound) & (df[column] <= upper_bound)]

if clean_outliers:
    # Wir filtern beide Spalten nacheinander
    df = filter_outliers(df_raw, 'temperature')
    df = filter_outliers(df, 'wind_speed')
    st.sidebar.success("✅ Daten bereinigt")
else:
    df = df_raw

st.sidebar.divider()
verfügbare_jahre = sorted(df['Jahr'].unique())
ausgewählte_jahre = st.sidebar.multiselect("Jahre auswählen:", options=verfügbare_jahre, default=verfügbare_jahre)
df_filtered = df[df['Jahr'].isin(ausgewählte_jahre)]

# --- 3. DASHBOARD HAUPTBEREICH ---
st.title("📊 Wetter & Wind Master-Statistik")

if df_filtered.empty:
    st.warning("Keine Daten vorhanden.")
else:
    # Berechnungen
    t_max_row = df_filtered.loc[df_filtered['temperature'].idxmax()]
    t_min_row = df_filtered.loc[df_filtered['temperature'].idxmin()]
    w_max_row = df_filtered.loc[df_filtered['wind_speed'].idxmax()]

    # --- KPI REIHE 1: TEMPERATUR ---
    st.subheader("🌡️ Temperatur Highlights")
    tc1, tc2, tc3 = st.columns(3)
    tc1.metric("Ø Temperatur", f"{df_filtered['temperature'].mean():.2f} °C")
    tc2.metric("Max Temp", f"{t_max_row['temperature']:.1f} °C", f"Jahr: {t_max_row['Jahr']}")
    tc3.metric("Min Temp", f"{t_min_row['temperature']:.1f} °C", f"Jahr: {t_min_row['Jahr']}", delta_color="inverse")

    # --- KPI REIHE 2: WIND ---
    st.subheader("🌬️ Wind Highlights")
    wc1, wc2, wc3 = st.columns(3)
    wc1.metric("Ø Windgeschwindigkeit", f"{df_filtered['wind_speed'].mean():.2f} m/s")
    wc2.metric("Stärkste Böe", f"{w_max_row['wind_speed']:.1f} m/s", f"Jahr: {w_max_row['Jahr']}")
    wc3.empty()

    st.divider()

    # --- 4. TRENDS & HEATMAPS ---
    col_l, col_r = st.columns(2)
    with col_l:
        st.subheader("📈 Temperatur-Trend")
        df_t = df_filtered.groupby(['Jahr', 'Jahreszeit'])['temperature'].mean().reset_index()
        fig_t = px.line(df_t, x='Jahr', y='temperature', color='Jahreszeit', markers=True)
        st.plotly_chart(fig_t, use_container_width=True)

    with col_r:
        st.subheader("🌬️ Wind-Trend")
        df_w = df_filtered.groupby(['Jahr', 'Jahreszeit'])['wind_speed'].mean().reset_index()
        fig_w = px.line(df_w, x='Jahr', y='wind_speed', color='Jahreszeit', markers=True)
        st.plotly_chart(fig_w, use_container_width=True)

    st.divider()
    st.subheader("📅 Monatlicher Vergleich")
    m_order = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
    
    h1, h2 = st.columns(2)
    with h1:
        t_heat = df_filtered.pivot_table(index='Monat', columns='Jahr', values='temperature', aggfunc='mean').reindex(m_order)
        st.plotly_chart(px.imshow(t_heat, text_auto=".1f", color_continuous_scale='RdBu_r', title="Ø Temp"), use_container_width=True)
    with h2:
        w_heat = df_filtered.pivot_table(index='Monat', columns='Jahr', values='wind_speed', aggfunc='mean').reindex(m_order)
        st.plotly_chart(px.imshow(w_heat, text_auto=".1f", color_continuous_scale='Blues', title="Ø Wind"), use_container_width=True)import streamlit as st
import pandas as pd
import plotly.express as px
import os

# --- 1. KONFIGURATION ---
st.set_page_config(page_title="Wetter Analyse Dashboard", layout="wide")

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

# --- 2. SIDEBAR ---
st.sidebar.header("Filter")
verfügbare_jahre = sorted(df['Jahr'].unique())
ausgewählte_jahre = st.sidebar.multiselect("Jahre auswählen:", options=verfügbare_jahre, default=verfügbare_jahre)
df_filtered = df[df['Jahr'].isin(ausgewählte_jahre)]

# --- 3. HAUPTBEREICH ---
st.title("Temperatur & Wind Statistik")

if df_filtered.empty:
    st.warning("Bitte wählen Sie mindestens ein Jahr aus.")
else:
    # --- REIHE 1: REKORDE (KPIs) ---
    t_max_row = df_filtered.loc[df_filtered['temperature'].idxmax()]
    t_min_row = df_filtered.loc[df_filtered['temperature'].idxmin()]
    w_max_row = df_filtered.loc[df_filtered['wind_speed'].idxmax()]
    avg_wind = df_filtered['wind_speed'].mean()

    # --- TEMPERATUR METRIKEN ---
    st.subheader("Temperatur Highlights")
    tc1, tc2, tc3 = st.columns(3)
    tc1.metric("Ø Temperatur", f"{df_filtered['temperature'].mean():.2f} °C")
    tc2.metric("Maximum", f"{t_max_row['temperature']:.1f} °C", f"Jahr: {t_max_row['Jahr']}")
    tc3.metric("Minimum", f"{t_min_row['temperature']:.1f} °C", f"Jahr: {t_min_row['Jahr']}", delta_color="inverse")

    # --- WIND METRIKEN ---
    st.subheader("Wind Highlights")
    wc1, wc2, wc3 = st.columns(3)
    wc1.metric("Ø Windgeschwindigkeit", f"{df_filtered['wind_speed'].mean():.2f} m/s")
    wc2.metric("Stärkste", f"{w_max_row['wind_speed']:.1f} m/s", f"Jahr: {w_max_row['Jahr']}")
    wc3.empty() # Platzhalter für Symmetrie

    st.divider()

    # --- REIHE 2: TRENDLINIEN (Übersicht nach Jahren) ---
    col_l, col_r = st.columns(2)

    with col_l:
        st.subheader("Temperatur-Trend (Saisonal)")
        df_t_trend = df_filtered.groupby(['Jahr', 'Jahreszeit'])['temperature'].mean().reset_index()
        fig_t = px.line(df_t_trend, x='Jahr', y='temperature', color='Jahreszeit', markers=True,
                        color_discrete_map={'Winter': '#00B4D8', 'Sommer': '#FFB703', 'Frühling': '#2D6A4F', 'Herbst': '#BA181B'})
        st.plotly_chart(fig_t, use_container_width=True)

    with col_r:
        st.subheader("Wind-Trend (Saisonal)")
        df_w_trend = df_filtered.groupby(['Jahr', 'Jahreszeit'])['wind_speed'].mean().reset_index()
        fig_w = px.line(df_w_trend, x='Jahr', y='wind_speed', color='Jahreszeit', markers=True,
                        color_discrete_map={'Winter': '#00B4D8', 'Sommer': '#FFB703', 'Frühling': '#2D6A4F', 'Herbst': '#BA181B'})
        st.plotly_chart(fig_w, use_container_width=True)

    st.divider()

    # --- REIHE 3: MONATLICHE HEATMAPS (Der "Per Monat" Vergleich) ---
    st.subheader("Monatliche Durchschnittswerte im Vergleich")
    
    # Vorbereitung der Monate für die richtige Sortierung
    monats_reihenfolge = ['January', 'February', 'March', 'April', 'May', 'June', 
                          'July', 'August', 'September', 'October', 'November', 'December']

    h_col1, h_col2 = st.columns(2)

    with h_col1:
        st.markdown("**Ø Temperatur pro Monat/Jahr**")
        t_heat = df_filtered.pivot_table(index='Monat', columns='Jahr', values='temperature', aggfunc='mean').reindex(monats_reihenfolge)
        fig_h_t = px.imshow(t_heat, text_auto=".1f", color_continuous_scale='RdBu_r', labels=dict(color="°C"))
        st.plotly_chart(fig_h_t, use_container_width=True)

    with h_col2:
        st.markdown("**Ø Windstärke pro Monat/Jahr**")
        w_heat = df_filtered.pivot_table(index='Monat', columns='Jahr', values='wind_speed', aggfunc='mean').reindex(monats_reihenfolge)
        fig_h_w = px.imshow(w_heat, text_auto=".1f", color_continuous_scale='Blues', labels=dict(color="m/s"))
        st.plotly_chart(fig_h_w, use_container_width=True)

    # --- REIHE 4: DETAIL MATRIX ---
    st.divider()
    st.subheader("Detaillierte Statistik-Matrix")
    
    stats_matrix = df_filtered.groupby(['Jahr', 'Jahreszeit']).agg(
        Avg_Temp=('temperature', 'mean'),
        Max_Temp=('temperature', 'max'),
        Min_Temp=('temperature', 'min'),
        Avg_Wind=('wind_speed', 'mean'),
        Max_Wind=('wind_speed', 'max')
    ).reset_index()

    st.dataframe(
        stats_matrix.style.background_gradient(subset=['Avg_Temp'], cmap='YlOrRd')
                          .background_gradient(subset=['Avg_Wind'], cmap='Blues'),
        use_container_width=True
    )







