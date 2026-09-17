# Tambahkan checkbox di sidebar
zoom_data = st.sidebar.checkbox(
    "Fokus Zoom ke Data Riil (Sembunyikan Limit 80/105)", value=False
)

fig = go.Figure()

# (masukkan trace data riil & simulasi seperti biasa...)

# Atur rentang Y secara dinamis
if zoom_data:
    # Zoom otomatis mengikuti min & max data
    y_min = df_selected["Nilai_Stabil_Riil"].min() - 0.5
    y_max = max(df_selected["Nilai_Simulasi"].max() + 0.5, y_min + 2)
    fig.update_layout(yaxis_range=[y_min, y_max])
else:
    # Tampilkan full range sampai batas Danger Limit
    fig.add_hline(
        y=80, line_dash="dash", line_color="yellow", annotation_text="Alert"
    )
    fig.add_hline(
        y=105, line_dash="dash", line_color="red", annotation_text="Danger"
    )
    fig.update_layout(yaxis_range=[0, 115])
