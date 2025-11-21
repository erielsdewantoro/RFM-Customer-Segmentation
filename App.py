import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ==========================================
# 1. CONFIGURATION & CUSTOM CSS
# ==========================================
st.set_page_config(
    page_title="Retail Analytics Pro",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    /* Styling Metric Card */
    div[data-testid="metric-container"] {
        background-color: #FFFFFF;
        border: 1px solid #E0E0E0;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
    div[data-testid="metric-container"] > label {
        color: #666; font-size: 14px;
    }
    div[data-testid="metric-container"] > div:nth-child(2) {
        color: #0068C9; font-size: 24px; font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. DATA LOADING (DENGAN PAKSA FORMAT)
# ==========================================
@st.cache_data
def load_data():
    rfm = pd.read_csv('clean_rfm_segments.csv')
    trx = pd.read_csv('clean_transactions_full.csv')
    
    # Feature Engineering (Dihitung ulang agar format 100% konsisten)
    trx['DateTime'] = pd.to_datetime(trx['DateTime'])
    
    # PAKSA FORMAT HARI & JAM (Agar sesuai dengan Hardcode Order)
    trx['DayOfWeek_Sorted'] = (trx['DateTime'].dt.dayofweek + 1).astype(str) + ". " + trx['DateTime'].dt.day_name()
    trx['Hour_Sorted'] = trx['DateTime'].dt.hour.astype(str).str.zfill(2) + ":00"
        
    return rfm, trx

try:
    rfm_df, trx_df = load_data()
except FileNotFoundError:
    st.error("⚠️ File CSV tidak ditemukan. Upload 'clean_rfm_segments.csv' & 'clean_transactions_full.csv' ke GitHub.")
    st.stop()

# DEFINE ORDER LIST (URUTAN BAKU)
# Ini kunci agar heatmap tidak pernah berantakan lagi
DAYS_ORDER = ["1. Monday", "2. Tuesday", "3. Wednesday", "4. Thursday", "5. Friday", "6. Saturday", "7. Sunday"]
HOURS_ORDER = [f"{i:02d}:00" for i in range(24)]

# ==========================================
# 3. SIDEBAR NAVIGATION
# ==========================================
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3094/3094851.png", width=60)
st.sidebar.title("Retail Analytics Pro")

page = st.sidebar.radio("Menu Navigasi:", 
    ["📊 Dashboard Utama", "🛠️ Marketing Action Center", "💡 Rekomendasi Bisnis", "📂 Dataset Info"]
)

st.sidebar.divider()

# ==========================================
# HALAMAN 1: DASHBOARD UTAMA
# ==========================================
if page == "📊 Dashboard Utama":
    
    st.sidebar.header("🎛️ Filter Dashboard")
    sel_seg = st.sidebar.multiselect("Segmen:", rfm_df['Segment'].unique(), default=rfm_df['Segment'].unique())
    min_d, max_d = trx_df['DateTime'].min().date(), trx_df['DateTime'].max().date()
    sel_date = st.sidebar.date_input("Tanggal:", (min_d, max_d), min_value=min_d, max_value=max_d)
    
    # FILTER LOGIC
    if sel_seg:
        f_rfm = rfm_df[rfm_df['Segment'].isin(sel_seg)]
    else:
        f_rfm = rfm_df
        
    valid_users = f_rfm['User_id'].unique()
    
    if len(sel_date) == 2:
        mask = (trx_df['DateTime'].dt.date >= sel_date[0]) & (trx_df['DateTime'].dt.date <= sel_date[1])
        f_trx = trx_df[trx_df['User_id'].isin(valid_users) & mask]
    else:
        f_trx = trx_df[trx_df['User_id'].isin(valid_users)]

    st.title("🚀 Business Performance Monitor")
    
    c1, c2, c3, c4 = st.columns(4)
    rev = f_trx['Total Price'].sum()
    trx_count = f_trx['Session_id'].nunique()
    aov = f_trx['Total Price'].mean() if trx_count > 0 else 0
    cust = f_rfm['User_id'].nunique()
    
    c1.metric("Total Revenue", f"Rp {rev:,.0f}".replace(",", "."))
    c2.metric("Total Transaksi", f"{trx_count:,}".replace(",", "."))
    c3.metric("Avg. Order Value", f"Rp {aov:,.0f}".replace(",", "."))
    c4.metric("Pelanggan Aktif", f"{cust:,}")
    
    st.divider()
    
    tab1, tab2 = st.tabs(["📈 Strategic View", "🔍 Operational View"])
    
    with tab1:
        col1, col2 = st.columns([1, 2])
        with col1:
            st.subheader("Komposisi Segmen")
            sc = f_rfm['Segment'].value_counts().reset_index()
            sc.columns = ['Segment', 'Count']
            fig = px.pie(sc, values='Count', names='Segment', hole=0.4, color_discrete_sequence=px.colors.qualitative.Prism)
            fig.update_traces(textinfo='percent+label', textposition='inside')
            fig.update_layout(showlegend=False, margin=dict(t=20, b=0, l=0, r=0))
            st.plotly_chart(fig, use_container_width=True)
            
        with col2:
            st.subheader("Heatmap Waktu Transaksi")
            if not f_trx.empty:
                hm = f_trx.groupby(['DayOfWeek_Sorted', 'Hour_Sorted']).size().reset_index(name='Count')
                
                fig_h = px.density_heatmap(hm, x='Hour_Sorted', y='DayOfWeek_Sorted', z='Count', 
                                           color_continuous_scale='Blues', text_auto=True)
                
                # --- FIX UTAMA: HARDCODE SORTING ORDER ---
                fig_h.update_xaxes(categoryorder='array', categoryarray=HOURS_ORDER, title="Jam")
                fig_h.update_yaxes(categoryorder='array', categoryarray=DAYS_ORDER, title="Hari")
                
                st.plotly_chart(fig_h, use_container_width=True)
            else:
                st.info("No Data")

    with tab2:
        c_left, c_right = st.columns(2)
        with c_left:
            st.subheader("Top 5 Produk (Revenue)")
            if not f_trx.empty:
                tp = f_trx.groupby('SubCategory')['Total Price'].sum().sort_values(ascending=False).head(5).reset_index()
                fig_b = px.bar(tp, x='Total Price', y='SubCategory', orientation='h', text_auto='.2s', color='Total Price', color_continuous_scale='Blues')
                fig_b.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_b, use_container_width=True)
        
        with c_right:
            st.subheader("Sebaran Pelanggan (Scatter)")
            if not f_rfm.empty:
                fig_s = px.scatter(f_rfm, x="Frequency", y="Monetary", color="Segment", hover_name="User_id", size="Monetary", log_x=True, log_y=True)
                st.plotly_chart(fig_s, use_container_width=True)

        st.subheader("📋 Daftar Detail Pelanggan")
        if not f_rfm.empty:
            df_d = f_rfm[['User_id', 'Segment', 'Recency', 'Frequency', 'Monetary']].copy()
            df_d.columns = ['User ID', 'Segmen', 'Hari Terakhir', 'Total Transaksi', 'Total Belanja (Rp)']
            df_d = df_d.sort_values('Total Belanja (Rp)', ascending=False)
            max_val = int(df_d['Total Transaksi'].max())
            st.dataframe(df_d, column_config={
                "Total Belanja (Rp)": st.column_config.NumberColumn(format="Rp %d"),
                "Total Transaksi": st.column_config.ProgressColumn(format="%d", min_value=0, max_value=max_val)
            }, use_container_width=True, hide_index=True)

# ==========================================
# HALAMAN 2: MARKETING ACTION CENTER
# ==========================================
elif page == "🛠️ Marketing Action Center":
    st.title("🛠️ Marketing Action Center")
    
    st.markdown("---")
    st.header("1️⃣ Product Deep Dive")
    
    col_sel, col_stat = st.columns([1, 3])
    all_prods = sorted(trx_df['SubCategory'].unique())
    
    with col_sel:
        selected_prod = st.selectbox("Pilih Produk:", all_prods)
    
    prod_trx = trx_df[trx_df['SubCategory'] == selected_prod]
    
    with col_stat:
        rev_p = prod_trx['Total Price'].sum()
        qty_p = prod_trx['Quantity'].sum()
        k1, k2 = st.columns(2)
        k1.metric(f"Revenue: {selected_prod}", f"Rp {rev_p:,.0f}".replace(",", "."))
        k2.metric("Terjual (Qty)", f"{qty_p:,.0f}")
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader(f"Kapan {selected_prod} Laris?")
        if not prod_trx.empty:
            hm_prod = prod_trx.groupby(['DayOfWeek_Sorted', 'Hour_Sorted']).size().reset_index(name='Count')
            fig_hm_p = px.density_heatmap(hm_prod, x='Hour_Sorted', y='DayOfWeek_Sorted', z='Count', 
                                          color_continuous_scale='Oranges', title=f"Heatmap: {selected_prod}")
            
            # --- FIX UTAMA: HARDCODE SORTING ORDER JUGA DI SINI ---
            fig_hm_p.update_xaxes(categoryorder='array', categoryarray=HOURS_ORDER)
            fig_hm_p.update_yaxes(categoryorder='array', categoryarray=DAYS_ORDER)
            
            st.plotly_chart(fig_hm_p, use_container_width=True)
        else:
            st.warning("Data tidak cukup.")
            
    with c2:
        st.subheader("Segmen Pembeli")
        buyer_ids = prod_trx['User_id'].unique()
        buyer_rfm = rfm_df[rfm_df['User_id'].isin(buyer_ids)]
        seg_buy = buyer_rfm['Segment'].value_counts().reset_index()
        seg_buy.columns = ['Segment', 'Count']
        fig_p_seg = px.bar(seg_buy, x='Count', y='Segment', orientation='h', color='Count')
        st.plotly_chart(fig_p_seg, use_container_width=True)

    st.markdown("---")
    st.header("2️⃣ Campaign Target Generator")
    
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        target_seg = st.multiselect("Target Segmen:", rfm_df['Segment'].unique(), default=["At Risk"])
    with col_f2:
        min_recency = st.number_input("Min. Recency (Hari):", min_value=0, value=30)
    with col_f3:
        min_monetary = st.number_input("Min. Belanja (Rp):", min_value=0, value=50000)
        
    target_list = rfm_df[
        (rfm_df['Segment'].isin(target_seg)) & 
        (rfm_df['Recency'] >= min_recency) &
        (rfm_df['Monetary'] >= min_monetary)
    ]
    
    st.success(f"🎯 Ditemukan **{len(target_list)} Pelanggan**.")
    st.dataframe(target_list, use_container_width=True)
    
    csv = target_list.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download CSV", data=csv, file_name='target_list.csv', mime='text/csv')

# ==========================================
# HALAMAN 3 & 4 (Recommendation & Info)
# ==========================================
elif page == "💡 Rekomendasi Bisnis":
    st.title("💡 Rekomendasi Strategis")
    with st.expander("🏆 Strategi Champions", expanded=True):
        st.write("**Action:** Berikan akses *Pre-order* eksklusif Gadget.")
    with st.expander("⚠️ Strategi At Risk", expanded=True):
        st.write("**Action:** Kirim Voucher pada jam sibuk sesuai Heatmap.")
    with st.expander("🌱 Strategi New Customers", expanded=True):
        st.write("**Action:** Tawarkan Bundling Beli 2 Hemat.")

elif page == "📂 Dataset Info":
    st.title("📂 Informasi Dataset")
    st.markdown("Sumber Data: E-Commerce Retail Transaction 2019.")
    st.dataframe(trx_df.head())
