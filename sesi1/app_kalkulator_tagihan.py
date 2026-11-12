import streamlit as st 

st.set_page_config(page_title="Kalkulator Tagihan", page_icon="🧾") 
st.title("🧾 Kalkulator Estimasi Tagihan Internet") 
st.write("Masukkan paket dan durasi berlangganan untuk melihat estimasi biaya.") 

HARGA = {"DSL": 260_000, "Fiber": 420_000, "Mobile Broadband": 310_000, "Satelit": 550_000} 
DISKON = {"Bulanan": 0.00, "Tahunan": 0.10, "Dua Tahun": 0.18} 

layanan = st.selectbox("Jenis layanan", list(HARGA)) 
kontrak = st.radio("Jenis kontrak", list(DISKON), horizontal=True) 
bulan = st.number_input("Durasi (bulan)", min_value=1, max_value=72, value=12, step=1) 
ppn = st.checkbox("Tambahkan PPN 11%", value=True) 
promo = st.slider("Diskon promosi tambahan (%)", min_value=0, max_value=20, value=0) 

if st.button("Hitung", type="primary"): 
    per_bulan = HARGA[layanan] * (1 - DISKON[kontrak]) * (1 - promo/100)
    total = per_bulan * bulan * (1.11 if ppn else 1) 
    st.metric("Biaya per bulan", f"Rp{per_bulan:,.0f}".replace(",", ".")) 
    st.metric("Total estimasi", f"Rp{total:,.0f}".replace(",", "."), 
    delta=f"hemat {DISKON[kontrak]:.0%}" if DISKON[kontrak] else None) 
    st.caption("Estimasi bersifat ilustratif untuk latihan.")