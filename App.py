import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ==========================================
# 1. CONFIGURATION & CUSTOM CSS (THEMING)
# ==========================================
st.set_page_config(
    page_title="Retail Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS untuk tampilan Card & Metric
st.markdown("""
<style>
    /* Metric Card Style */
    div[data-testid="metric-container"] {
        background-color: #F0F2F6;
        border: 1px solid #D6D6D6;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 1px 1px 3px rgba(0,0,0,0.1);
        color: #333333;
    }
    div[data-testid="metric-container"] > label {
        font-size: 14px;
        font-weight: 500;
        color: #555;
    }
    div[data-testid="metric-container"] > div:nth-child(2) {
        font-size: 26px;
        font-weight: 700;
        color: #0E1117;
    }
    /* Styling Header Tab */
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 16px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATA LOADING
# ==========================================
@st.cache_data
def load_data():
    # Load CSV (Pastikan file ada di root folder GitHub)
    rfm = pd.read_csv('clean_rfm_segments.csv')
    trx = pd.read_csv('clean_transactions_full.csv')
    
    # Convert DateTime
    trx['DateTime'] = pd.to_datetime(trx['DateTime'])
    
    return rfm, trx

# Error Handling Load Data
try:
    rfm_df, trx_df = load_data()
except FileNotFoundError:
    st.error("⚠️ File CSV tidak ditemukan. Pastikan file 'clean_rfm_segments.csv' dan 'clean_transactions_full.csv' sudah diupload ke GitHub.")
    st.stop()

# ==========================================
# 3. SIDEBAR & FILTERS
# ==========================================
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3094/3094851.png", width=60)
st.sidebar.title("Analytics Menu")

# Navigasi Halaman
page = st.sidebar.radio("Pilih Halaman:", ["Dashboard Utama", "Business Recommendations", "Dataset Info"])

st.sidebar.divider()

# --- GLOBAL FILTER (Hanya aktif di Dashboard) ---
if page == "Dashboard Utama":
    st.sidebar.header("🎛️ Filter Data")
    
    # 1. Filter Segmen
    all_segments = sorted(rfm_df['Segment'].unique())
    selected_segments = st.sidebar.multiselect(
        "Pilih Segmen:",
        options=all_segments,
        default=all_segments
    )
    
    # 2. Filter Tanggal
    min_date = trx_df['DateTime'].min().date()
    max_date = trx_df['DateTime'].max().date()
    
    date_range = st.sidebar.date_input(
        "Rentang Tanggal:",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    
    # LOGIKA FILTERING
    if selected_segments:
        filtered_rfm = rfm_df[rfm_df['Segment'].isin(selected_segments)]
    else:
        filtered_rfm = rfm_df # Jika kosong, ambil semua
        
    # Ambil User ID yang valid dari filter segmen
    valid_users = filtered_rfm['User_id'].unique()
    
    # Filter Transaksi berdasarkan User ID & Tanggal
    if len(date_range) == 2:
        mask_date = (trx_df['DateTime'].dt.date >= date_range[0]) & (trx_df['DateTime'].dt.date <= date_range[1])
        filtered_trx = trx_df[trx_df['User_id'].isin(valid_users) & mask_date]
    else:
        filtered_trx = trx_df[trx_df['User_id'].isin(valid_users)]

# ==========================================
# 4. HALAMAN: DASHBOARD UTAMA
# ==========================================
if page == "Dashboard Utama":
    st.title("🚀 Retail Business Performance")
    st.markdown("Dashboard interaktif untuk memantau performa penjualan dan segmentasi pelanggan berbasis **RFM Analysis**.")
    
    # --- BARIS 1: KPI CARDS ---
    col1, col2, col3, col4 = st.columns(4)
    
    # Hitung Metrics
    total_revenue = filtered_trx['Total Price'].sum()
    total_trx_count = filtered_trx['Session_id'].nunique()
    avg_aov = filtered_trx['Total Price'].mean() if total_trx_count > 0 else 0
    total_customers = filtered_rfm['User_id'].nunique()
    
    col1.metric("Total Pendapatan", f"Rp {total_revenue:,.0f}".replace(",", "."))
    col2.metric("Total Transaksi", f"{total_trx_count:,}".replace(",", "."))
    col3.metric("Rata-rata Order (AOV)", f"Rp {avg_aov:,.0f}".replace(",", "."))
    col4.metric("Pelanggan Aktif", f"{total_customers:,}")
    
    st.divider()
    
    # --- TABS NAVIGASI (STRATEGI vs OPERASIONAL) ---
    tab_strategic, tab_operational = st.tabs(["📈 Strategic View (Executive)", "🔍 Operational View (Detail)"])
    
    # === TAB 1: STRATEGIC ===
    with tab_strategic:
        c1, c2 = st.columns([1, 2])
        
        with c1:
            st.subheader("Komposisi Pelanggan")
            # Donut Chart Segmen
            seg_counts = filtered_rfm['Segment'].value_counts().reset_index()
            seg_counts.columns = ['Segment', 'Count']
            
            fig_donut = px.pie(seg_counts, values='Count', names='Segment', hole=0.45,
                               color_discrete_sequence=px.colors.qualitative.Prism)
            fig_donut.update_traces(textinfo='percent+label', textposition='inside')
            fig_donut.update_layout(showlegend=False, margin=dict(t=30, b=0, l=0, r=0))
            st.plotly_chart(fig_donut, use_container_width=True)
            
            # Insight Box
            if not seg_counts.empty:
                top_seg = seg_counts.iloc[0]['Segment']
                st.info(f"💡 **Insight:** Mayoritas pelanggan berada di segmen **{top_seg}**. Gunakan strategi retensi yang sesuai.")

        with c2:
            st.subheader("Tren Pendapatan Harian")
            # Line Chart
            if not filtered_trx.empty:
                trend_df = filtered_trx.set_index('DateTime').resample('D')['Total Price'].sum().reset_index()
                fig_line = px.line(trend_df, x='DateTime', y='Total Price', markers=True,
                                   line_shape='spline', color_discrete_sequence=['#0068C9'])
                fig_line.update_layout(xaxis_title="", yaxis_title="Revenue (Rp)", margin=dict(t=20, b=20))
                st.plotly_chart(fig_line, use_container_width=True)
            else:
                st.warning("Data transaksi kosong.")

        # --- HEATMAP SECTION (FIXED SORTING) ---
        st.subheader("🔥 Heatmap Waktu Transaksi (Optimasi Jam Sibuk)")
        
        if not filtered_trx.empty:
            # Agregasi Data
            heatmap_data = filtered_trx.groupby(['DayOfWeek_Sorted', 'Hour_Sorted']).size().reset_index(name='Count')
            
            # FIX: Memaksa Plotly mengurutkan berdasarkan Kategori (Abjad/Angka)
            # Karena data kita formatnya "1. Monday", "2. Tuesday", maka sort category ascending akan berhasil
            fig_heat = px.density_heatmap(
                heatmap_data, 
                x='Hour_Sorted', 
                y='DayOfWeek_Sorted', 
                z='Count',
                color_continuous_scale='Blues',
                text_auto=True
            )
            
            # UPDATE LAYOUT UNTUK SORTING YANG BENAR
            fig_heat.update_xaxes(categoryorder='category ascending', title="Jam Transaksi")
            fig_heat.update_yaxes(categoryorder='category ascending', title="Hari")
            
            st.plotly_chart(fig_heat, use_container_width=True)
            st.caption("Grafik ini menunjukkan kepadatan transaksi. Warna makin gelap = Makin sibuk.")
        else:
            st.info("Tidak ada data untuk ditampilkan.")

    # === TAB 2: OPERATIONAL ===
    with tab_operational:
        # KPI Tambahan
        kpi1, kpi2, kpi3 = st.columns(3)
        max_sale = filtered_trx['Total Price'].max() if not filtered_trx.empty else 0
        total_qty = filtered_trx['Quantity'].sum() if not filtered_trx.empty else 0
        
        kpi1.metric("Rekor Penjualan Tertinggi", f"Rp {max_sale:,.0f}".replace(",", "."))
        kpi2.metric("Total Produk Terjual", f"{total_qty:,.0f}".replace(",", "."))
        
        st.markdown("---")
        
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.subheader("🏆 Top 5 Kategori Produk")
            if not filtered_trx.empty:
                top_prod = filtered_trx.groupby('SubCategory')['Total Price'].sum().sort_values(ascending=False).head(5).reset_index()
                fig_bar = px.bar(top_prod, x='Total Price', y='SubCategory', orientation='h',
                                 text_auto='.2s', color='Total Price', color_continuous_scale='Blues')
                fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.warning("Data kosong.")
        
        with col_right:
            st.subheader("📍 Peta Sebaran (Scatter)")
            if not filtered_rfm.empty:
                fig_scatter = px.scatter(filtered_rfm, x="Frequency", y="Monetary", color="Segment",
                                         hover_name="User_id", size="Monetary", log_x=True, log_y=True,
                                         color_discrete_sequence=px.colors.qualitative.Safe)
                st.plotly_chart(fig_scatter, use_container_width=True)
            else:
                st.warning("Data kosong.")
        
        # TABEL DETAIL PELANGGAN
        st.subheader("📋 Daftar Pelanggan Prioritas")
        if not filtered_rfm.empty:
            df_display = filtered_rfm[['User_id', 'Segment', 'Recency', 'Frequency', 'Monetary']].copy()
            df_display.columns = ['User ID', 'Segmen', 'Hari Terakhir', 'Transaksi', 'Total Belanja (Rp)']
            df_display = df_display.sort_values(by='Total Belanja (Rp)', ascending=False)
            
            # Fix JSON Error dengan convert ke int
            max_val = int(df_display['Total Transaksi'].max())
            
            st.dataframe(
                df_display,
                column_config={
                    "Total Belanja (Rp)": st.column_config.NumberColumn(format="Rp %d"),
                    "Total Transaksi": st.column_config.ProgressColumn(format="%d", min_value=0, max_value=max_val)
                },
                use_container_width=True,
                hide_index=True
            )

# ==========================================
# 5. HALAMAN: BUSINESS RECOMMENDATIONS
# ==========================================
elif page == "Business Recommendations":
    st.title("💡 Rekomendasi Strategis")
    st.markdown("Berdasarkan analisis data, berikut adalah **Action Plan** yang direkomendasikan:")
    
    # Menggunakan Expander agar rapi
    with st.expander("🏆 Strategi untuk 'Champions' (High Value)", expanded=True):
        st.write("""
        **Karakteristik:** Loyal, sering belanja, uang banyak.
        - **Action:** Berikan akses *Pre-order* eksklusif untuk produk Gadget/Aksesoris terbaru.
        - **Goal:** Menjaga rasa eksklusivitas dan meningkatkan *Wallet Share*.
        """)
        
    with st.expander("⚠️ Strategi untuk 'At Risk' (Berisiko Churn)", expanded=True):
        st.write("""
        **Karakteristik:** Dulu aktif, sekarang sudah lama menghilang.
        - **Action:** Kirim 'Win-Back Voucher' pada jam sibuk (Kamis Siang) sesuai Heatmap.
        - **Goal:** Mengaktifkan kembali sebelum mereka menjadi *Lost Customer*.
        """)
        
    with st.expander("🌱 Strategi untuk 'New Customers'", expanded=True):
        st.write("""
        **Karakteristik:** Baru belanja 1x.
        - **Action:** Tawarkan paket *Bundling* (Beli 2 Lebih Hemat).
        - **Goal:** Meningkatkan frekuensi belanja dari 1 menjadi 2 (agar jadi Loyal).
        """)

# ==========================================
# 6. HALAMAN: DATASET INFO
# ==========================================
elif page == "Dataset Info":
    st.title("📂 Informasi Dataset")
    st.markdown("Penjelasan mengenai sumber data dan kamus data yang digunakan dalam proyek ini.")
    
    st.markdown("""
    ### **Data Dictionary**
    | Nama Kolom | Penjelasan |
    | :--- | :--- |
    | **User_id** | Identitas unik pelanggan. |
    | **Session_id** | Kode unik setiap transaksi. |
    | **DateTime** | Waktu transaksi terjadi. |
    | **Action** | Jenis aktivitas (Purchase, View, dll). |
    | **Total Price** | Nilai total belanja (Revenue). |
    """)
    
    st.markdown("### **Preview Data Transaksi**")
    st.dataframe(trx_df.head(10))
