# sesi2/app_eda.py — EDA interaktif di Streamlit dengan beragam visualisasi Plotly 
from pathlib import Path 
import pandas as pd 
import plotly.express as px 
import streamlit as st 
  
ROOT = Path(__file__).resolve().parents[1] 
st.set_page_config(page_title="EDA Churn", page_icon="🔎", layout="wide") 
  
STATUS = {"Bertahan": "#2a78d6", "Churn": "#eb6834"} 
KATEGORI = ["#2a78d6", "#1baf7a", "#eda100", "#4a3aa7", "#e87ba4"] 
KONTRAK = ["Bulanan", "Tahunan", "Dua Tahun"] 
  
@st.cache_data 
def load_data(): 
    df = pd.read_csv(ROOT / "data" / "customer_churn.csv", parse_dates=["signup_date"]) 
    df["total_charges_missing"] = df["total_charges"].isna()        # catat sebelum imputasi 
    df["total_charges"] = df["total_charges"].fillna(df["total_charges"].median()) 
    df["status"] = df["churn"].map({0: "Bertahan", 1: "Churn"}) 
    df["kelompok_tenure"] = pd.cut(df["tenure_months"], [0, 12, 24, 48, 72], 
                                   labels=["0-12", "13-24", "25-48", "49-72"]).astype(str) 
    return df 
  
def gaya(fig, tinggi=360): 
    fig.update_layout(template="plotly_white", height=tinggi, margin=dict(l=10, r=10, t=50, b=10), 
                      title_font_size=15, legend_title_text="") 
    return fig 
  
df = load_data() 
st.title("🔎 Exploratory Data Analysis — Customer Churn") 
st.caption("Data latihan sintetis · 3.000 pelanggan · pendaftaran Januari 2023 – Desember 2025") 
  
# ---------- KPI CARDS ---------- 
k1, k2, k3, k4, k5 = st.columns(5) 
k1.metric("Total pelanggan", f"{len(df):,}") 
k2.metric("Churn rate", f"{df.churn.mean():.1%}") 
k3.metric("Rata-rata tagihan", f"Rp{df.monthly_charges.mean():,.0f}".replace(",", ".")) 
k4.metric("Rata-rata tenure", f"{df.tenure_months.mean():.1f} bln") 
k5.metric("Missing total_charges", f"{df.total_charges_missing.sum()} baris", help="Diisi median") 
  
tab = st.tabs(["🥧 Komposisi", "📊 Perbandingan", "📈 Distribusi", "⏱️ Tren", "🔗 Hubungan", "📋 Data",
               "📣 Keluhan"])
  
# ---------- 1. KOMPOSISI: pie, donut, treemap ---------- 
with tab[0]: 
    c1, c2 = st.columns(2) 
    pie = px.pie(df, names="status", color="status", color_discrete_map=STATUS, 
                 title="Satu dari tiga pelanggan churn") 
    pie.update_traces(textinfo="percent+label", textfont_size=14) 
    c1.plotly_chart(gaya(pie), width="stretch") 
    donut = px.pie(df, names="contract_type", hole=0.55, color_discrete_sequence=KATEGORI, 
                   category_orders={"contract_type": KONTRAK}, 
                   title="Separuh pelanggan berkontrak bulanan") 
    donut.update_traces(textinfo="percent+label") 
    donut.add_annotation(text=f"<b>{len(df):,}</b><br>pelanggan", showarrow=False, font_size=16) 
    c2.plotly_chart(gaya(donut), width="stretch") 
    tm = df.groupby(["region", "segment"], as_index=False).agg(pelanggan=("customer_id", "count"), 
                                                              churn_rate=("churn", "mean")) 
    tree = px.treemap(tm, path=["region", "segment"], values="pelanggan", color="churn_rate", 
                      color_continuous_scale="Oranges", 
                      title="Treemap: luas = jumlah pelanggan, warna = churn rate") 
    st.plotly_chart(gaya(tree, 420), width="stretch")
    st.markdown("**Pie/donut vs bar horizontal terurut**")
    c3, c4 = st.columns(2)
    pie_is = px.pie(df, names="internet_service", color_discrete_sequence=KATEGORI,
                    title="Pie: internet_service (3 kategori)")
    pie_is.update_traces(textinfo="percent+label")
    c3.plotly_chart(gaya(pie_is), width="stretch")
    donut_rg = px.pie(df, names="region", hole=0.55, color_discrete_sequence=KATEGORI,
                      title="Donut: region (5 kategori)")
    donut_rg.update_traces(textinfo="percent+label")
    c4.plotly_chart(gaya(donut_rg), width="stretch")
    c5, c6 = st.columns(2)
    for kol, wadah in [("internet_service", c5), ("region", c6)]:
        porsi = (df[kol].value_counts(normalize=True).rename("porsi").reset_index().sort_values("porsi"))
        b = px.bar(porsi, x="porsi", y=kol, orientation="h", text_auto=".1%",
                   color_discrete_sequence=["#2a78d6"], title=f"Bar terurut: {kol}")
        b.update_xaxes(tickformat=".0%", range=[0, porsi["porsi"].max() * 1.2])
        b.update_layout(xaxis_title="", yaxis_title="")
        wadah.plotly_chart(gaya(b), width="stretch")
    st.caption("Untuk 5 kategori, bar terurut jauh lebih mudah dibaca: panjang batang bisa dibandingkan "
               "langsung dan urutannya jelas, sedangkan irisan kecil donut sulit dibedakan. Pie masih "
               "layak untuk 2–3 kategori.")

# ---------- 2. PERBANDINGAN: bar, grouped bar, stacked 100% ---------- 
with tab[1]: 
    kolom = st.selectbox("Bandingkan churn rate berdasarkan", 
                         ["contract_type", "region", "segment", "payment_method", "internet_service"]) 
    rk = (df.groupby(kolom, as_index=False).agg(pelanggan=("customer_id", "count"), 
                                                churn_rate=("churn", "mean")) 
            .sort_values("churn_rate")) 
    bar = px.bar(rk, x="churn_rate", y=kolom, orientation="h", text_auto=".1%", 
                 color_discrete_sequence=["#eb6834"], title=f"Churn rate per {kolom}") 
    bar.add_vline(x=df.churn.mean(), line_dash="dot", annotation_text="rata-rata") 
    bar.update_xaxes(tickformat=".0%") 
    c1, c2 = st.columns([3, 2]) 
    c1.plotly_chart(gaya(bar), width="stretch") 
    c2.dataframe(rk.sort_values("churn_rate", ascending=False) 
                   .style.format({"churn_rate": "{:.1%}"}) 
                   .background_gradient(subset=["churn_rate"], cmap="Oranges"),
                    width="stretch", hide_index=True) 
    c3, c4 = st.columns(2) 
    gb = df.groupby(["contract_type", "segment"], as_index=False)["churn"].mean() 
    grouped = px.bar(gb, x="contract_type", y="churn", color="segment", barmode="group", 
                     color_discrete_sequence=KATEGORI, category_orders={"contract_type": KONTRAK}, 
                     title="Grouped bar: kontrak × segmen") 
    grouped.update_yaxes(tickformat=".0%") 
    c3.plotly_chart(gaya(grouped), width="stretch") 
    stacked = px.histogram(df, y="payment_method", color="status", barnorm="percent", 
                           color_discrete_map=STATUS, title="Stacked bar 100%: status per pembayaran") 
    stacked.update_layout(xaxis_title="Proporsi (%)", yaxis_title="") 
    c4.plotly_chart(gaya(stacked), width="stretch")
    st.download_button("⬇️ Unduh tabel ringkasan (CSV)",
                       rk.assign(churn_rate=rk["churn_rate"].round(4)).to_csv(index=False).encode("utf-8"),
                       file_name=f"ringkasan_churn_per_{kolom}.csv", mime="text/csv")
    c7, c8 = st.columns(2)
    sis = px.histogram(df, y="internet_service", color="status", barnorm="percent",
                       color_discrete_map=STATUS, title="Stacked bar 100%: status per internet_service")
    sis.update_layout(xaxis_title="Proporsi (%)", yaxis_title="")
    c7.plotly_chart(gaya(sis), width="stretch")
    bx = px.box(df, x="status", y="support_calls", color="status", color_discrete_map=STATUS,
                category_orders={"status": ["Bertahan", "Churn"]}, title="Box plot support_calls per status")
    bx.update_layout(showlegend=False, xaxis_title="")
    c8.plotly_chart(gaya(bx), width="stretch")

# ---------- 3. DISTRIBUSI: histogram, box, violin ---------- 
with tab[2]: 
    num = st.selectbox("Variabel numerik", ["tenure_months", "monthly_charges", 
                                            "num_complaints", "support_calls"]) 
    c1, c2 = st.columns(2) 
    hist = px.histogram(df, x=num, color="status", barmode="overlay", opacity=0.7, nbins=30, 
                        color_discrete_map=STATUS, marginal="box", title=f"Histogram {num}") 
    c1.plotly_chart(gaya(hist, 400), width="stretch") 
    vio = px.violin(df, x="contract_type", y=num, color="contract_type", box=True, 
                    color_discrete_sequence=KATEGORI, category_orders={"contract_type": KONTRAK}, 
                    title=f"Violin {num} per kontrak") 
    c2.plotly_chart(gaya(vio, 400), width="stretch") 
  
# ---------- 4. TREN: line, area ---------- 
with tab[3]: 
    bulanan = (df.set_index("signup_date").resample("ME")["customer_id"].count() 
                 .rename("pelanggan").reset_index()) 
    bulanan["rata2_3bln"] = bulanan["pelanggan"].rolling(3).mean() 
    line = px.line(bulanan, x="signup_date", y=["pelanggan", "rata2_3bln"], markers=True, 
                   color_discrete_sequence=["#9dbbe6", "#2a78d6"], 
                   title="Pelanggan baru per bulan dan rata-rata bergerak 3 bulan") 
    st.plotly_chart(gaya(line), width="stretch") 
    c1, c2 = st.columns(2) 
    kt = df.groupby("kelompok_tenure", as_index=False)["churn"].mean() 
    lt = px.line(kt, x="kelompok_tenure", y="churn", markers=True, text=kt["churn"].map("{:.1%}".format), 
                 color_discrete_sequence=["#eb6834"], title="Churn rate per kelompok tenure") 
    lt.update_traces(textposition="top center", marker_size=10) 
    lt.update_yaxes(tickformat=".0%", range=[0, 0.65]) 
    c1.plotly_chart(gaya(lt), width="stretch") 
    q = (df.assign(kuartal=df.signup_date.dt.to_period("Q").astype(str)) 
           .groupby(["kuartal", "segment"], as_index=False)["customer_id"].count()) 
    area = px.area(q, x="kuartal", y="customer_id", color="segment", 
                   color_discrete_sequence=KATEGORI, title="Area: pelanggan baru per kuartal") 
    c2.plotly_chart(gaya(area), width="stretch")
    cq = (df.assign(kuartal=df.signup_date.dt.to_period("Q").astype(str))
            .groupby("kuartal", as_index=False)["churn"].mean())
    lq = px.line(cq, x="kuartal", y="churn", markers=True, text=cq["churn"].map("{:.1%}".format),
                 color_discrete_sequence=["#eb6834"], title="Churn rate per kuartal pendaftaran")
    lq.update_traces(textposition="top center")
    lq.add_hline(y=df.churn.mean(), line_dash="dot", annotation_text="rata-rata")
    lq.update_yaxes(tickformat=".0%", range=[0, 0.6])
    st.plotly_chart(gaya(lq), width="stretch")

# ---------- 5. HUBUNGAN: scatter, heatmap ---------- 
with tab[4]: 
    c1, c2 = st.columns(2) 
    sc = px.scatter(df, x="tenure_months", y="monthly_charges", color="status", opacity=0.55, 
                    color_discrete_map=STATUS, hover_name="customer_id", 
                    hover_data=["contract_type", "num_complaints"], title="Tenure vs tagihan") 
    c1.plotly_chart(gaya(sc, 420), width="stretch") 
    corr = df[["tenure_months", "monthly_charges", "num_complaints", "support_calls", "churn"]].corr() 
    hm = px.imshow(corr.round(2), text_auto=True, color_continuous_scale="RdBu_r", zmin=-1, zmax=1, 
                   title="Heatmap korelasi") 
    c2.plotly_chart(gaya(hm, 420), width="stretch") 
    pv = pd.pivot_table(df, values="churn", index="region", columns="segment", aggfunc="mean") 
    hm2 = px.imshow(pv * 100, text_auto=".1f", color_continuous_scale="Oranges", 
                    labels={"color": "Churn (%)"}, title="Heatmap churn rate region × segmen (%)") 
    st.plotly_chart(gaya(hm2, 360), width="stretch") 
  
# ---------- 6. DATA: profil + tabel ---------- 
with tab[5]: 
    profil = pd.DataFrame({"tipe": df.dtypes.astype(str), 
                           "missing": df.isna().sum().where(df.columns != "total_charges", 
                                                            df.total_charges_missing.sum()), 
                           "unik": df.nunique()}).reset_index(names="kolom") 
    c1, c2 = st.columns([2, 3]) 
    c1.markdown("**Profil kolom**") 
    c1.dataframe(profil, width="stretch", hide_index=True) 
    c2.markdown("**Statistik deskriptif**") 
    c2.dataframe(df.describe(include="number").T.round(1), width="stretch") 
    st.markdown("**10 baris pertama**")
    st.dataframe(df.head(10), width="stretch", hide_index=True)

# ---------- 7. KELUHAN: churn rate per jumlah keluhan ----------
with tab[6]:
    kl = df.groupby("num_complaints", as_index=False).agg(pelanggan=("customer_id", "count"),
                                                         churn_rate=("churn", "mean"))
    bk = px.bar(kl, x="num_complaints", y="churn_rate", text=kl["churn_rate"].map("{:.0%}".format),
                hover_data=["pelanggan"], color_discrete_sequence=["#eb6834"],
                title="Churn rate per jumlah keluhan")
    bk.add_hline(y=df.churn.mean(), line_dash="dot", annotation_text="rata-rata")
    bk.update_xaxes(dtick=1, title="Jumlah keluhan")
    bk.update_yaxes(tickformat=".0%", range=[0, 1.1], title="Churn rate")
    st.plotly_chart(gaya(bk, 420), width="stretch")
    st.caption("Churn naik dari sekitar 27% (tanpa keluhan) hingga 100% pada 6+ keluhan, "
               "tetapi kelompok keluhan tinggi sangat kecil (lihat jumlah pelanggan saat hover).")

