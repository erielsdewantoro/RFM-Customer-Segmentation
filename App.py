import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="RFM Dashboard", layout="wide")

# --- TITLE & INTRO ---
st.title("📊 RFM Customer Segmentation Dashboard")
st.markdown("""
Aplikasi ini memvisualisasikan hasil analisis segmentasi pelanggan ritel menggunakan metode RFM.
Data diproses untuk mengidentifikasi pelanggan setia (Champions) dan berisiko (At Risk).
""")

# --- LOAD DATA ---
@st.cache_data
def load_data():
    # Pastikan path sesuai dengan struktur foldermu
    rfm = pd.read_csv('clean_rfm_segments.csv')
    trx = pd.read_csv('clean_transactions_full.csv')
    return rfm, trx

try:
    rfm_df, trx_df = load_data()
except FileNotFoundError:
    st.error("File CSV tidak ditemukan. Pastikan file ada di folder 'data/'.")
    st.stop()

# --- SIDEBAR FILTER ---
st.sidebar.header("Filter Data")
selected_segment = st.sidebar.multiselect(
    "Pilih Segmen:",
    options=rfm_df['Segment'].unique(),
    default=rfm_df['Segment'].unique()
)

# Filter Dataframe berdasarkan input user
filtered_rfm = rfm_df[rfm_df['Segment'].isin(selected_segment)]

# --- BARIS 1: KPI METRICS ---
st.header("Executive Summary")
col1, col2, col3 = st.columns(3)

total_revenue = trx_df['Total Price'].sum()
total_trx = trx_df['Session_id'].nunique()
total_customer = rfm_df['User_id'].nunique()

col1.metric("Total Revenue", f"Rp {total_revenue:,.0f}")
col2.metric("Total Transaksi", f"{total_trx}")
col3.metric("Total Pelanggan", f"{total_customer}")

st.divider()

# --- BARIS 2: VISUALISASI UTAMA ---
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Komposisi Segmen Pelanggan")
    segment_counts = filtered_rfm['Segment'].value_counts().reset_index()
    segment_counts.columns = ['Segment', 'Count']
    
    fig_pie = px.pie(segment_counts, values='Count', names='Segment', 
                     color_discrete_sequence=px.colors.qualitative.Pastel)
    st.plotly_chart(fig_pie, use_container_width=True)

with col_right:
    st.subheader("Scatter Plot: Frequency vs Monetary")
    # Scatter plot untuk validasi segmen (seperti di Power BI Hal 2)
    fig_scatter = px.scatter(filtered_rfm, x="Frequency", y="Monetary", 
                             color="Segment", hover_data=['User_id'],
                             log_x=True, log_y=True, # Skala Log agar titik tidak menumpuk
                             title="Sebaran Pelanggan (Log Scale)")
    st.plotly_chart(fig_scatter, use_container_width=True)

# --- BARIS 3: TABEL DETAIL ---
st.subheader(f"Daftar Pelanggan ({len(filtered_rfm)} User)")
st.dataframe(filtered_rfm[['User_id', 'Segment', 'Recency', 'Frequency', 'Monetary']]
             .sort_values(by='Monetary', ascending=False))

# --- DOWNLOAD BUTTON ---
csv = filtered_rfm.to_csv(index=False).encode('utf-8')
st.download_button(
    label="Download Filtered Data (CSV)",
    data=csv,
    file_name='filtered_rfm_data.csv',
    mime='text/csv',

)
