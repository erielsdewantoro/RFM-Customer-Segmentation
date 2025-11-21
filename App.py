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

# Custom CSS untuk tampilan yang lebih 'Clean' & 'Card-like'
st.markdown("""
<style>
    /* Mengubah background metric card */
    div[data-testid="metric-container"] {
        background-color: #FFFFFF;
        border: 1px solid #E0E0E0;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
        color: #333333;
    }
    /* Judul metric lebih kecil dan abu-abu */
    div[data-testid="metric-container"] > label {
        font-size: 14px;
        color: #666666;
    }
    /* Angka metric lebih besar dan tebal */
    div[data-testid="metric-container"] > div:nth-child(2) {
        font-size: 24px;
        font-weight: bold;
        color: #0068C9; /* Warna Biru Streamlit Professional */
    }
    /* Hapus padding atas default agar header lebih naik */
    .block-container {
        padding-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATA LOADING & PREPROCESSING
# ==========================================
@st.cache_data
def load_data():
    # Load data (Pastikan file ada di root folder GitHub)
    rfm = pd.read_csv('clean_rfm_segments.csv')
    trx = pd.read_csv('clean_transactions_full.csv')
    
    # Convert DateTime
    trx['DateTime'] = pd.to_datetime(trx['DateTime'])
    
    return rfm, trx

# Load Data dengan Error Handling
try:
    rfm_df, trx_df = load_data()
except FileNotFoundError:
    st.error("⚠️ File CSV tidak ditemukan. Pastikan 'clean_rfm_segments.csv' dan 'clean_transactions_full.csv' ada di repository.")
    st.stop()

# ==========================================
# 3. SIDEBAR (NAVIGASI & FILTER)
# ==========================================
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3094/3094851.png", width=50) # Icon Dummy
st.sidebar.title("Navigation")

# Menu Pilihan Halaman
page = st.sidebar.radio("Go to", ["Dashboard Utama", "Dataset Source", "About Project"])

st.sidebar.divider()

# Global Filter (Hanya muncul di halaman Dashboard)
if page == "Dashboard Utama":
    st.sidebar.header("🎛️ Filter Options")
    
    # Filter Segmen
    selected_segments = st.sidebar.multiselect(
        "Pilih Segmen Customer:",
        options=rfm_df['Segment'].unique(),
        default=rfm_df['Segment'].unique()
    )
    
    # Filter Date Range
    min_date = trx_df['DateTime'].min().date()
    max_date = trx_df['DateTime'].max().date()
    
    date_range = st.sidebar.date_input(
        "Rentang Tanggal Transaksi:",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    
    # Terapkan Filter
    # 1. Filter RFM Data
    # Jika user tidak memilih segmen, gunakan semua segmen (opsional, atau biarkan kosong)
    if selected_segments:
        filtered_rfm = rfm_df[rfm_df['Segment'].isin(selected_segments)]
    else:
        filtered_rfm = rfm_df
    
    # 2. Filter Transaction Data
    # Ambil User ID yang terpilih di filter segmen
    valid_users = filtered_rfm['User_id'].unique()
    
    # Filter TRX berdasarkan User ID valid DAN Date Range
    # Pastikan date_range memiliki 2 nilai (start, end) sebelum filter
    if len(date_range) == 2:
        mask_date = (trx_df['DateTime'].dt.date >= date_range[0]) & (trx_df['DateTime'].dt.date <= date_range[1])
        filtered_trx = trx_df[trx_df['User_id'].isin(valid_users) & mask_date]
    else:
        filtered_trx = trx_df[trx_df['User_id'].isin(valid_users)]

# ==========================================
# 4. MAIN PAGE CONTENT
# ==========================================

if page == "Dashboard Utama":
    st.title("🚀 Retail Business Performance Dashboard")
    st.markdown("### Monitoring Kesehatan Bisnis & Perilaku Pelanggan Berbasis RFM")
    
    # --- ROW 1: KPI CARDS ---
    col1, col2, col3, col4 = st.columns(4)
    
    total_rev = filtered_trx['Total Price'].sum()
    total_trx = filtered_trx['Session_id'].nunique()
    avg_order = filtered_trx['Total Price'].mean() if total_trx > 0 else 0
    active_customers = filtered_rfm['User_id'].nunique()
    
    col1.metric("Total Revenue", f"Rp {total_rev:,.0f}".replace(",", "."))
    col2.metric("Total Transaksi", f"{total_trx:,}".replace(",", "."))
    col3.metric("Avg. Order Value", f"Rp {avg_order:,.0f}".replace(",", "."))
    col4.metric("Active Customers", f"{active_customers:,}")
    
    st.divider()
    
    # --- TABS LAYOUT (STRATEGY vs OPERATION) ---
    tab1, tab2 = st.tabs(["📈 Executive Summary (Strategic)", "🔍 Customer Deep Dive (Operational)"])
    
    # === TAB 1: EXECUTIVE VIEW ===
    with tab1:
        c1, c2 = st.columns([1, 2]) # Kolom kiri kecil, kanan besar
        
        with c1:
            st.subheader("Komposisi Segmen")
            # Donut Chart
            seg_counts = filtered_rfm['Segment'].value_counts().reset_index()
            seg_counts.columns = ['Segment', 'Count']
            
            fig_donut = px.pie(seg_counts, values='Count', names='Segment', hole=0.4,
                               color_discrete_sequence=px.colors.qualitative.Prism)
            fig_donut.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5))
            st.plotly_chart(fig_donut, use_container_width=True)
            
            # Insight Box
            if not seg_counts.empty:
                top_segment = seg_counts.iloc[0]['Segment']
                st.info(f"💡 **Insight:** Segmen dominan saat ini adalah **{top_segment}**. Pastikan strategi retensi fokus pada konversi segmen ini.")
            else:
                st.warning("Data tidak tersedia untuk filter yang dipilih.")

        with c2:
            st.subheader("Tren Pendapatan (Revenue Trend)")
            # Line Chart Bulanan
            # Resample ke Bulanan/Harian
            if not filtered_trx.empty:
                trend_df = filtered_trx.set_index('DateTime').resample('D')['Total Price'].sum().reset_index()
                
                fig_line = px.line(trend_df, x='DateTime', y='Total Price', 
                                   markers=True, line_shape='spline',
                                   color_discrete_sequence=['#0068C9'])
                fig_line.update_layout(xaxis_title="Tanggal", yaxis_title="Revenue (Rp)")
                st.plotly_chart(fig_line, use_container_width=True)
            else:
                st.warning("Tidak ada data transaksi untuk ditampilkan.")
        
        # Heatmap Section (Full Width)
        st.subheader("🔥 Peta Waktu Transaksi (Heatmap)")
        
        if not filtered_trx.empty:
            # Agregasi untuk Heatmap
            heatmap_data = filtered_trx.groupby(['DayOfWeek_Sorted', 'Hour_Sorted']).size().reset_index(name='Count')
            
            fig_heat = px.density_heatmap(heatmap_data, x='Hour_Sorted', y='DayOfWeek_Sorted', z='Count',
                                          color_continuous_scale='Blues', text_auto=True)
            fig_heat.update_layout(xaxis_title="Jam", yaxis_title="Hari")
            st.plotly_chart(fig_heat, use_container_width=True)
        else:
            st.info("Data transaksi kosong.")

    # === TAB 2: OPERATIONAL VIEW ===
    with tab2:
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.subheader("Top 5 Kategori Produk (Revenue)")
            # Bar Chart Horizontal
            if not filtered_trx.empty:
                top_products = filtered_trx.groupby('SubCategory')['Total Price'].sum().sort_values(ascending=False).head(5).reset_index()
                
                fig_bar = px.bar(top_products, x='Total Price', y='SubCategory', orientation='h',
                                 text_auto='.2s', color='Total Price', color_continuous_scale='Blues')
                fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.info("Data kosong.")
            
        with col_right:
            st.subheader("Peta Sebaran Pelanggan (Scatter)")
            # Scatter Plot
            if not filtered_rfm.empty:
                fig_scatter = px.scatter(filtered_rfm, x="Frequency", y="Monetary", 
                                         color="Segment", size='Monetary', hover_name="User_id",
                                         log_x=True, log_y=True, 
                                         color_discrete_sequence=px.colors.qualitative.Safe)
                st.plotly_chart(fig_scatter, use_container_width=True)
            else:
                st.info("Data kosong.")
            
        # Tabel Detail
        st.subheader("📋 Daftar Detail Pelanggan")
        
        if not filtered_rfm.empty:
            # Format Tabel untuk display
            display_df = filtered_rfm[['User_id', 'Segment', 'Recency', 'Frequency', 'Monetary']].copy()
            display_df.columns = ['User ID', 'Segmen', 'Hari Terakhir Belanja', 'Total Transaksi', 'Total Belanja (Rp)']
            
            # Sort by Monetary
            display_df = display_df.sort_values(by='Total Belanja (Rp)', ascending=False)
            
            # --- PERBAIKAN BUG JSON DI SINI ---
            # Kita paksa max_value menjadi float/int Python murni, bukan numpy type
            max_trx_val = int(display_df['Total Transaksi'].max()) 
            
            st.dataframe(
                display_df,
                column_config={
                    "Total Belanja (Rp)": st.column_config.NumberColumn(format="Rp %d"), 
                    "Total Transaksi": st.column_config.ProgressColumn(
                        format="%f", 
                        min_value=0, 
                        max_value=max_trx_val # <-- FIX: Menggunakan variable yang sudah di-cast ke int
                    ) 
                },
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("Tidak ada data pelanggan yang cocok dengan filter.")

elif page == "Dataset Source":
    st.title("📂 Data Source & Dictionary")
    
    st.markdown("""
    **Sumber Data:** E-Commerce Retail Transaction Dataset (2019).
    
    **Kamus Data (Data Dictionary):**
    | Kolom | Deskripsi |
    | :--- | :--- |
    | **User_id** | Identitas unik pelanggan. |
    | **Segment** | Hasil klasifikasi RFM (Champions, Loyal, At Risk, dll). |
    | **Recency** | Jumlah hari sejak pembelian terakhir. |
    | **Frequency** | Total jumlah transaksi yang dilakukan. |
    | **Monetary** | Total uang yang dibelanjakan (Revenue). |
    """)
    
    st.subheader("Sample Data RFM")
    st.dataframe(rfm_df.head(10), use_container_width=True)
    
    st.subheader("Sample Data Transaksi")
    st.dataframe(trx_df.head(10), use_container_width=True)

elif page == "About Project":
    st.title("ℹ️ Tentang Proyek Ini")
    
    st.markdown("""
    ### **Background**
    Perusahaan ritel memiliki data transaksi historis namun belum memanfaatkannya secara optimal. 
    Strategi pemasaran saat ini bersifat *generic*, sehingga tingkat retensi pelanggan rendah.
    
    ### **Solution**
    Dashboard ini dibangun menggunakan pendekatan **RFM Analysis (Recency, Frequency, Monetary)** untuk melakukan segmentasi pelanggan.
    
    ### **Technology Stack**
    - **Python**: Data Cleaning, EDA, RFM Modeling.
    - **Pandas**: Data Manipulation.
    - **Streamlit**: Interactive Web App.
    - **Plotly**: Advanced Visualization.
    
    ---
    *Created by [Eriel Setiawan Dewantoro] - Data Analyst Student*
    """)

