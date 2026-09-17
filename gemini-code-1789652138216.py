import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="Simulasi Respon Sensor 19-K-101 Terhadap Gempa", layout="wide"
)

st.title("🌋 Simulasi Sensitivitas Sensor Getaran 19-K-101 vs Parameters Seismik")
st.markdown(
    """
Aplikasi ini membandingkan **Tren Data Riil Stabil (Baseline Operasional)** dengan **Simulasi Getaran Tambahan** 
akibat guncangan gempa bumi berdasarkan variabel Magnitudo ($M$) dan Jarak Hiposenter ($R$).
"""
)


# --- LOAD DATA HISTORIS ---
@st.cache_data
def load_data():
    # Membaca data gabungan dari Sheet3
    df = pd.read_excel("Data PKL 19-K-101.xlsx", sheet_name="Sheet3")
    return df


try:
    df_raw = load_data()

    # --- SIDEBAR: PILIH PERIODE DATA RIIL ---
    st.sidebar.header("📅 Data Historis Riil")
    periode = st.sidebar.radio(
        "Pilih Periode Pengamatan:",
        ("Agustus 2020 (13 Aug)", "Februari 2023 (19 Feb)"),
    )

    if "Agustus" in periode:
        time_col = "Time"
        cols_sensor = {
            "19VI700": "19VI700",
            "19VI701": "19VI701",
            "19VI702": "19VI702",
            "19VI703": "19VI703",
        }
        t_label = "13 Agustus 2020"
    else:
        time_col = "Time.1"
        cols_sensor = {
            "19VI700": "19VI700.1",
            "19VI701": "19VI701.1",
            "19VI702": "19VI702.1",
            "19VI703": "19VI703.1",
        }
        t_label = "19 Februari 2023"

    sensor_display = st.sidebar.selectbox(
        "Pilih Sensor Vibration:",
        ["19VI700", "19VI701", "19VI702", "19VI703"],
    )
    sensor_col = cols_sensor[sensor_display]

    # --- SIDEBAR: PARAMETER GEMPA INTERAKTIF ---
    st.sidebar.header("🌐 Parameter Gempa Bumi")
    mag = st.sidebar.slider(
        "Magnitudo (M):", min_value=2.0, max_value=8.0, value=3.8, step=0.1
    )
    dist_epi = st.sidebar.slider(
        "Jarak Episentrum ke Balongan (km):",
        min_value=5,
        max_value=300,
        value=35,
        step=5,
    )
    depth = st.sidebar.slider(
        "Kedalaman Hiposenter (km):",
        min_value=2,
        max_value=200,
        value=10,
        step=2,
    )

    # --- KALKULASI ATENUASI SEISMIK (Joyner-Boore / Est. PGA to Amplitude) ---
    R_hipo = np.sqrt(dist_epi**2 + depth**2)  # Jarak Hiposenter total (km)

    # Formula estimasi tambahan getaran pada fondasi mesin (µm)
    # Amplitudo bertambah signifikan jika Magnitudo naik dan R_hipo mengecil
    pga_gal = 10 ** (0.53 * mag - 1.13 * np.log10(R_hipo) - 0.23)
    amp_tambahan_um = pga_gal * 1.8  # Konversi respons getaran struktural

    # Sidebar info ringkasan
    st.sidebar.markdown("---")
    st.sidebar.metric("Jarak Hiposenter Total", f"{R_hipo:.1f} km")
    st.sidebar.metric("Est. Tambahan Amplitudo Gempa", f"{amp_tambahan_um:.2f} µm")

    # --- PROSES SIMULASI GELOMBANG GEMPA ---
    df_selected = df_raw[[time_col, sensor_col]].dropna().copy()
    df_selected.columns = ["Waktu", "Nilai_Stabil_Riil"]

    n_data = len(df_selected)
    time_index = np.arange(n_data)

    # Membuat guncangan gempa sintetis (Envelope Gaussian) di tengah rentang waktu
    center_idx = n_data // 2
    durasi_gempa = 25  # sampel menit
    envelope = np.exp(-(((time_index - center_idx) / durasi_gempa) ** 2))

    # Sinyal getaran gempa (gelombang seismik)
    seismic_wave = (
        amp_tambahan_um * envelope * np.sin(2 * np.pi * (time_index) / 3.0)
    )

    # Superposisi: Nilai Stabil Riil + Sinyal Gempa
    df_selected["Nilai_Simulasi"] = (
        df_selected["Nilai_Stabil_Riil"] + seismic_wave
    )

    # --- PLOTTING GRAFIK INTERAKTIF ---
    fig = go.Figure()

    # 1. Tren Data Riil (Tetap Stabil)
    fig.add_trace(
        go.Scatter(
            x=df_selected["Waktu"],
            y=df_selected["Nilai_Stabil_Riil"],
            mode="lines",
            name=f"Data Historis Riil ({t_label}) - Stabil",
            line=dict(color="#1f77b4", width=2),
        )
    )

    # 2. Tren Hasil Simulasi Gempa
    fig.add_trace(
        go.Scatter(
            x=df_selected["Waktu"],
            y=df_selected["Nilai_Simulasi"],
            mode="lines",
            name=f"Simulasi Respon (+ Gempa M{mag}, Hiposenter {R_hipo:.0f}km)",
            line=dict(color="#ff7f0e", width=2, dash="solid"),
        )
    )

    # 3. Batas Ambang Alert & Danger (Sesuai Logsheet 19-K-101)
    fig.add_hline(
        y=80,
        line_dash="dash",
        line_color="yellow",
        annotation_text="Alert Limit (80 µm)",
    )
    fig.add_hline(
        y=105,
        line_dash="dash",
        line_color="red",
        annotation_text="Danger Limit (105 µm)",
    )

    fig.update_layout(
        title=f"Perbandingan Tren Sensor {sensor_display} (Riil vs Simulasi Gempa)",
        xaxis_title="Waktu (UTC)",
        yaxis_title="Vibration Amplitude (µm)",
        hovermode="x unified",
        height=550,
    )

    st.plotly_chart(fig, use_container_width=True)

    # --- ANALISIS DEDUKTIF GEOFISIKA ---
    max_sim = df_selected["Nilai_Simulasi"].max()
    max_riil = df_selected["Nilai_Stabil_Riil"].max()

    col1, col2, col3 = st.columns(3)
    col1.metric("Getaran Maks. Data Riil", f"{max_riil:.2f} µm")
    col2.metric("Getaran Maks. Hasil Simulasi", f"{max_sim:.2f} µm")
    col3.metric("Selisih Lonjakan", f"{(max_sim - max_riil):.2f} µm")

    st.markdown("### 📝 Kesimpulan Hasil Simulasi:")
    if max_sim < 80:
        st.success(
            f"🟢 **TETAP STABIL (TIDAK MEMICU ALARM):** Dengan **Magnitudo M{mag}** dan **Jarak Hiposenter {R_hipo:.1f} km**, puncak getaran hanya mencapai **{max_sim:.2f} µm**. Ini membuktikan mengapa pada kejadian gempa riil (Agustus 2020 & Februari 2023) tren grafik sensor **tetap terlihat datar/stabil**."
        )
    elif 80 <= max_sim < 105:
        st.warning(
            f"🟡 **MEMICU ALERT ALARM:** Puncak getaran mencapai **{max_sim:.2f} µm** (Melewati ambang Alert 80 µm). Pada kondisi ini, panel kontrol akan memberikan peringatan indikasi getaran tinggi."
        )
    else:
        st.error(
            f"🔴 **MEMICU SHUTDOWN / TRIP:** Puncak getaran mencapai **{max_sim:.2f} µm** (Melewati ambang Danger 105 µm). Guncangan gempa cukup kuat untuk memicu interlock keamanan dan mematikan Kompresor 19-K-101 secara otomatis."
        )

except Exception as e:
    st.error(f"Terjadi kesalahan pembacaan data: {e}")
