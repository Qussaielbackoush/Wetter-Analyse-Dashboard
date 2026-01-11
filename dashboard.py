# --- REIHE 4: TEMPERATUR (TREND & DISTRIBUTION) ---
st.subheader("🌡️ Temperatur: Entwicklung & Ausreißer")
col_t_trend, col_t_box = st.columns([2, 1]) # 2:1 Verhältnis für bessere Lesbarkeit

with col_t_trend:
    # Saisonaler Trend (Linie)
    df_t_trend = df_filtered.groupby(['Jahr', 'Jahreszeit'])['temperature'].mean().reset_index()
    fig_t_line = px.line(df_t_trend, x='Jahr', y='temperature', color='Jahreszeit', markers=True,
                         title="Durchschnittstemp. Trend pro Saison",
                         color_discrete_map={'Winter': '#00B4D8', 'Sommer': '#FFB703', 'Frühling': '#2D6A4F', 'Herbst': '#BA181B'})
    st.plotly_chart(fig_t_line, use_container_width=True)

with col_t_box:
    # Verteilung & Ausreißer (Boxplot)
    fig_t_box = px.box(df_filtered, x='Jahreszeit', y='temperature', color='Jahreszeit',
                       title="Temp. Streuung & Ausreißer",
                       color_discrete_map={'Winter': '#00B4D8', 'Sommer': '#FFB703', 'Frühling': '#2D6A4F', 'Herbst': '#BA181B'})
    st.plotly_chart(fig_t_box, use_container_width=True)




st.divider()

# --- REIHE 5: WIND (TREND & DISTRIBUTION) ---
st.subheader("🌬️ Wind: Entwicklung & Ausreißer")
col_w_trend, col_w_box = st.columns([2, 1])

with col_w_trend:
    # Wind Trend (Linie)
    df_w_trend = df_filtered.groupby(['Jahr', 'Jahreszeit'])['wind_speed'].mean().reset_index()
    fig_w_line = px.line(df_w_trend, x='Jahr', y='wind_speed', color='Jahreszeit', markers=True,
                         title="Durchschnittswind Trend pro Saison",
                         color_discrete_map={'Winter': '#00B4D8', 'Sommer': '#FFB703', 'Frühling': '#2D6A4F', 'Herbst': '#BA181B'})
    st.plotly_chart(fig_w_line, use_container_width=True)

with col_col_w_box:
    # Wind Verteilung & Ausreißer (Boxplot)
    fig_w_box = px.box(df_filtered, x='Jahreszeit', y='wind_speed', color='Jahreszeit',
                       title="Wind Streuung & Ausreißer",
                       color_discrete_map={'Winter': '#00B4D8', 'Sommer': '#FFB703', 'Frühling': '#2D6A4F', 'Herbst': '#BA181B'})
    st.plotly_chart(fig_w_box, use_container_width=True)
