import sys 
from pathlib import Path 
import pandas as pd 
import plotly.express as px 
import streamlit as st 
  
ROOT = Path(__file__).resolve().parents[1] 
sys.path.append(str(ROOT))                      # agar folder utils bisa di-import 
from utils.model_utils import load_model, load_metadata, validate_input, predict 
  
st.set_page_config(page_title="Eksplorasi & Prediksi Churn", page_icon="🤖", layout="wide") 
  
# 1) LOAD MODEL — sekali saja, disimpan di cache 
@st.cache_resource 
def get_model(): 
    return load_model() 
  
@st.cache_data 
def get_meta(): 
    return load_metadata() 
  
model, meta = get_model(), get_meta() 
  
st.title("🔎 Eksplorasi Data & 🤖 Prediksi Risiko Churn Pelanggan") 
with st.expander("ℹ️ Informasi model final", expanded=False): 
    st.write(f"**{meta['model_name']}** · versi {meta['model_version']} · {meta['algorithm']}") 
    st.write("Fitur input:", ", ".join(meta["feature_order"])) 
    st.write(f"Threshold keputusan: {meta['decision_threshold']} · " 
             f"Risk bins: {meta['risk_bins']}") 
    st.caption("Model tidak dilatih ulang di aplikasi ini; aplikasi hanya melakukan inference.") 
  
COLOR = {"Rendah": "🟢", "Sedang": "🟡", "Tinggi": "🔴"} 
tab_eda, tab_single, tab_batch = st.tabs(["🔎 Eksplorasi Data", "👤 Prediksi satu pelanggan",
                                          "📂 Prediksi batch (CSV)"])

STATUS = {"Bertahan": "#2a78d6", "Churn": "#eb6834"}
KATEGORI = ["#2a78d6", "#1baf7a", "#eda100", "#4a3aa7", "#e87ba4"]
KONTRAK = ["Bulanan", "Tahunan", "Dua Tahun"]

@st.cache_data
def load_eda_data():
    d = pd.read_csv(ROOT / "data" / "customer_churn.csv", parse_dates=["signup_date"])
    d["total_charges"] = d["total_charges"].fillna(d["total_charges"].median())
    d["status"] = d["churn"].map({0: "Bertahan", 1: "Churn"})
    d["kelompok_tenure"] = pd.cut(d["tenure_months"], [0, 12, 24, 48, 72],
                                  labels=["0-12", "13-24", "25-48", "49-72"]).astype(str)
    d["kuartal"] = d["signup_date"].dt.to_period("Q").astype(str)
    return d

def gaya(fig, tinggi=360):
    fig.update_layout(template="plotly_white", height=tinggi, margin=dict(l=10, r=10, t=50, b=10),
                      title_font_size=15, legend_title_text="")
    return fig

# 0) EKSPLORASI DATA — grafik kunci dari sesi2/app_eda.py
with tab_eda:
    eda = load_eda_data()
    base = eda.churn.mean()
    st.caption("Data latihan sintetis · konteks untuk membaca hasil prediksi di tab berikutnya.")

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total pelanggan", f"{len(eda):,}")
    k2.metric("Churn rate", f"{base:.1%}")
    k3.metric("Rata-rata tagihan", f"Rp{eda.monthly_charges.mean():,.0f}".replace(",", "."))
    k4.metric("Rata-rata tenure", f"{eda.tenure_months.mean():.1f} bln")

    # Komposisi
    c1, c2 = st.columns(2)
    with c1, st.container(border=True):
        pie = px.pie(eda, names="status", color="status", color_discrete_map=STATUS,
                     title="Komposisi status pelanggan")
        pie.update_traces(textinfo="percent+label", textfont_size=14)
        st.plotly_chart(gaya(pie), width="stretch")
    with c2, st.container(border=True):
        donut = px.pie(eda, names="contract_type", hole=0.55, color_discrete_sequence=KATEGORI,
                       category_orders={"contract_type": KONTRAK}, title="Komposisi jenis kontrak")
        donut.update_traces(textinfo="percent+label")
        st.plotly_chart(gaya(donut), width="stretch")

    # Churn rate per kategori (dipilih pengguna)
    with st.container(border=True):
        kolom = st.selectbox("Bandingkan churn rate berdasarkan",
                             ["contract_type", "internet_service", "payment_method", "region", "segment"],
                             key="eda_kolom")
        rk = (eda.groupby(kolom, as_index=False).agg(pelanggan=("customer_id", "count"),
                                                    churn_rate=("churn", "mean"))
                 .sort_values("churn_rate"))
        bar = px.bar(rk, x="churn_rate", y=kolom, orientation="h", text_auto=".1%",
                     hover_data=["pelanggan"], color_discrete_sequence=["#eb6834"],
                     title=f"Churn rate per {kolom}")
        bar.add_vline(x=base, line_dash="dot", annotation_text="rata-rata")
        bar.update_xaxes(tickformat=".0%")
        st.plotly_chart(gaya(bar), width="stretch")
        tinggi, rendah = rk.iloc[-1], rk.iloc[0]
        st.caption(f"💡 Churn tertinggi: **{tinggi[kolom]}** ({tinggi.churn_rate:.1%}); "
                   f"terendah: **{rendah[kolom]}** ({rendah.churn_rate:.1%}).")

    # Tenure & keluhan
    c3, c4 = st.columns(2)
    with c3, st.container(border=True):
        kt = eda.groupby("kelompok_tenure", as_index=False)["churn"].mean()
        lt = px.line(kt, x="kelompok_tenure", y="churn", markers=True,
                     text=kt["churn"].map("{:.1%}".format), color_discrete_sequence=["#eb6834"],
                     title="Churn rate per kelompok tenure (bulan)")
        lt.update_traces(textposition="top center", marker_size=10)
        lt.update_yaxes(tickformat=".0%", range=[0, kt.churn.max() * 1.3], title="Churn rate")
        lt.update_xaxes(title="")
        st.plotly_chart(gaya(lt), width="stretch")
        st.caption("💡 Pelanggan baru paling rentan; risiko turun seiring masa berlangganan.")
    with c4, st.container(border=True):
        kl = eda.groupby("num_complaints", as_index=False).agg(pelanggan=("customer_id", "count"),
                                                              churn_rate=("churn", "mean"))
        bk = px.bar(kl, x="num_complaints", y="churn_rate", text=kl["churn_rate"].map("{:.0%}".format),
                    hover_data=["pelanggan"], color_discrete_sequence=["#eb6834"],
                    title="Churn rate per jumlah keluhan")
        bk.add_hline(y=base, line_dash="dot", annotation_text="rata-rata")
        bk.update_xaxes(dtick=1, title="Jumlah keluhan")
        bk.update_yaxes(tickformat=".0%", range=[0, 1.1], title="Churn rate")
        st.plotly_chart(gaya(bk), width="stretch")
        st.caption("💡 Semakin banyak keluhan, semakin tinggi churn (kelompok keluhan tinggi berjumlah kecil).")

    # Tren kuartal & distribusi tagihan
    c5, c6 = st.columns(2)
    with c5, st.container(border=True):
        cq = eda.groupby("kuartal", as_index=False)["churn"].mean()
        lq = px.line(cq, x="kuartal", y="churn", markers=True, text=cq["churn"].map("{:.1%}".format),
                     color_discrete_sequence=["#eb6834"], title="Churn rate per kuartal pendaftaran")
        lq.update_traces(textposition="top center")
        lq.add_hline(y=base, line_dash="dot", annotation_text="rata-rata")
        lq.update_yaxes(tickformat=".0%", range=[0, cq.churn.max() * 1.4], title="Churn rate")
        lq.update_xaxes(title="")
        st.plotly_chart(gaya(lq), width="stretch")
    with c6, st.container(border=True):
        hist = px.histogram(eda, x="monthly_charges", color="status", barmode="overlay", opacity=0.7,
                            nbins=30, color_discrete_map=STATUS, marginal="box",
                            title="Distribusi tagihan bulanan per status")
        st.plotly_chart(gaya(hist), width="stretch")

    # Heatmap
    c7, c8 = st.columns(2)
    with c7, st.container(border=True):
        pv = pd.pivot_table(eda, values="churn", index="region", columns="segment", aggfunc="mean")
        hm2 = px.imshow(pv * 100, text_auto=".1f", color_continuous_scale="Oranges",
                        labels={"color": "Churn (%)"}, title="Churn rate region × segmen (%)")
        st.plotly_chart(gaya(hm2), width="stretch")
    with c8, st.container(border=True):
        corr = eda[["tenure_months", "monthly_charges", "num_complaints", "support_calls", "churn"]].corr()
        hm = px.imshow(corr.round(2), text_auto=True, color_continuous_scale="RdBu_r", zmin=-1, zmax=1,
                       title="Korelasi antar variabel numerik")
        st.plotly_chart(gaya(hm), width="stretch")

  
# 2) PREDIKSI SATU PELANGGAN — input lewat form 
with tab_single: 
    cats, rng = meta["categories"], meta["numeric_ranges"] 
    with st.form("form_prediksi"): 
        c1, c2, c3 = st.columns(3) 
        region = c1.selectbox("Region", cats["region"]) 
        segment = c1.selectbox("Segmen", cats["segment"]) 
        contract = c2.selectbox("Jenis kontrak", cats["contract_type"]) 
        payment = c2.selectbox("Metode pembayaran", cats["payment_method"]) 
        service = c3.selectbox("Layanan internet", cats["internet_service"])
        tmin, tmax = (int(v) for v in rng["tenure_months"])
        tenure = c3.number_input("Tenure (bulan)", tmin, tmax, min(12, tmax))
        d1, d2, d3 = st.columns(3) 
        monthly = d1.number_input("Tagihan bulanan (Rp)", 100_000, 2_000_000, 450_000, step=10_000) 
        complaints = d2.number_input("Jumlah keluhan", 0, 10, 2) 
        calls = d3.number_input("Panggilan ke CS", 0, 15, 3) 
        submitted = st.form_submit_button("🔮 Prediksi", type="primary") 
  
    if submitted: 
        row = pd.DataFrame([{ 
            "tenure_months": tenure, "monthly_charges": monthly, 
            "total_charges": monthly * tenure, "num_complaints": complaints, 
            "support_calls": calls, "region": region, "segment": segment, 
            "contract_type": contract, "payment_method": payment, "internet_service": service, 
        }]) 
        errs = validate_input(row, meta) 
        if errs: 
            st.error("\n".join(errs)) 
        else: 
            res = predict(model, row, meta).iloc[0] 
            m1, m2, m3 = st.columns(3) 
            m1.metric("Probabilitas churn", f"{res.churn_probability:.1%}") 
            m2.metric("Prediksi", "Churn" if res.predicted_churn else "Bertahan") 
            m3.metric("Kategori risiko", f"{COLOR[res.risk_category]} {res.risk_category}") 
            st.progress(float(res.churn_probability)) 
            if res.risk_category == "Tinggi": 
                st.error("Rekomendasi: prioritaskan retensi — tawarkan migrasi ke kontrak tahunan " 
                         "dan tindak lanjuti keluhan dalam 48 jam.") 
            elif res.risk_category == "Sedang": 
                st.warning("Rekomendasi: pantau, kirim survei kepuasan dan penawaran loyalitas.") 
            else: 
                st.success("Rekomendasi: pertahankan layanan standar.") 
  
# 3) PREDIKSI BATCH — upload CSV pelanggan baru 
with tab_batch: 
    up = st.file_uploader("Upload CSV pelanggan baru (format sama dengan data/new_customers.csv)", 
                          type="csv") 
    pakai_contoh = st.checkbox("Gunakan contoh data/new_customers.csv", value=up is None) 
    if up is not None: 
        data = pd.read_csv(up) 
    elif pakai_contoh: 
        data = pd.read_csv(ROOT / "data" / "new_customers.csv") 
    else: 
        st.info("Upload file atau centang contoh data.") 
        st.stop() 
  
    errs = validate_input(data, meta) 
    if errs: 
        for e in errs: 
            st.error(e) 
        st.stop() 
  
    hasil = predict(model, data, meta) 
    k1, k2, k3, k4 = st.columns(4) 
    k1.metric("Pelanggan diproses", f"{len(hasil):,}") 
    k2.metric("Prediksi churn", f"{hasil.predicted_churn.sum():,}") 
    k3.metric("Rata-rata probabilitas", f"{hasil.churn_probability.mean():.1%}") 
    k4.metric("Risiko tinggi", f"{(hasil.risk_category == 'Tinggi').sum():,}") 
  
    RISK_COLOR = {"Rendah": "#1baf7a", "Sedang": "#eda100", "Tinggi": "#e34948"} 
    a, b = st.columns(2) 
    donut = px.pie(hasil, names="risk_category", hole=0.55, color="risk_category", 
                   color_discrete_map=RISK_COLOR, title="Komposisi kategori risiko", 
                   category_orders={"risk_category": ["Rendah", "Sedang", "Tinggi"]}) 
    donut.update_traces(textinfo="percent+label") 
    a.plotly_chart(donut.update_layout(height=330, showlegend=False), width="stretch") 
    pk = hasil.groupby("contract_type", as_index=False)["churn_probability"].mean() 
    bar = px.bar(pk, x="contract_type", y="churn_probability", text_auto=".1%", 
                 color_discrete_sequence=["#eb6834"], title="Rata-rata probabilitas churn per kontrak") 
    bar.update_yaxes(tickformat=".0%") 
    b.plotly_chart(bar.update_layout(height=330, template="plotly_white", xaxis_title=""), 
                   width="stretch") 
  
    risiko = st.multiselect("Tampilkan kategori risiko", ["Tinggi", "Sedang", "Rendah"], 
                            default=["Tinggi"]) 
    tampil = hasil[hasil.risk_category.isin(risiko)].sort_values("churn_probability", 
                                                                 ascending=False) 
    st.dataframe(tampil, width="stretch", height=320, 
                column_config={"churn_probability": st.column_config.ProgressColumn( 
                    "Probabilitas churn", min_value=0.0, max_value=1.0, format="%.2f")}) 
    st.download_button("⬇️ Unduh hasil prediksi", hasil.to_csv(index=False).encode("utf-8"), 
                    "hasil_prediksi_churn.csv", "text/csv") 