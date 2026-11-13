# sesi6/app_dash_plotly.py — menampilkan chart Plotly di aplikasi Dash 
from pathlib import Path 
import pandas as pd 
import plotly.express as px 
import plotly.graph_objects as go 
from dash import Dash, html, dcc 
  
ROOT = Path(__file__).resolve().parents[1] 
df = pd.read_csv(ROOT / "data" / "customer_churn.csv", parse_dates=["signup_date"]) 
df["status"] = df["churn"].map({0: "Bertahan", 1: "Churn"}) 
WARNA = {"Bertahan": "#4C72B0", "Churn": "#C44E52"} 
  
hist = px.histogram(df, x="tenure_months", color="status", nbins=36, barmode="overlay", 
                    opacity=0.7, color_discrete_map=WARNA, template="plotly_white", 
                    labels={"tenure_months": "Tenure (bulan)", "status": "Status"}, 
                    title="Churn terkonsentrasi pada tenure pendek") 
  
scatter = px.scatter(df, x="tenure_months", y="monthly_charges", color="status", 
                     color_discrete_map=WARNA, opacity=0.55, template="plotly_white", 
                     size="support_calls", size_max=18, 
                     hover_name="customer_id", hover_data=["region", "contract_type", "num_complaints"], 
                     labels={"tenure_months": "Tenure (bulan)", "monthly_charges": "Tagihan (Rp)",
                             "support_calls": "Panggilan CS"}, 
                     title="Bubble: ukuran = jumlah panggilan ke CS · klik legenda untuk filter") 
  
# Churn rate per payment_method: horizontal, tertinggi di atas, garis rata-rata nasional
rata2 = df["churn"].mean()
pay = df.groupby("payment_method", as_index=False)["churn"].mean().sort_values("churn")  # asc -> tertinggi di atas
bar_pay = px.bar(pay, x="churn", y="payment_method", orientation="h", text_auto=".1%",
                 template="plotly_white", color_discrete_sequence=["#C44E52"],
                 labels={"churn": "Churn rate", "payment_method": ""},
                 title="Churn rate per metode pembayaran")
bar_pay.add_vline(x=rata2, line_dash="dot", annotation_text=f"rata-rata nasional {rata2:.1%}",
                  annotation_position="top")
bar_pay.update_xaxes(tickformat=".0%")

# Sunburst: ukuran irisan = jumlah pelanggan, warna = churn rate
sun = px.sunburst(df.assign(pelanggan=1), path=["region", "segment", "contract_type"],
                  values="pelanggan", color="churn", color_continuous_scale="Oranges",
                  labels={"churn": "Churn rate", "pelanggan": "Pelanggan"},
                  title="Sunburst: region → segmen → kontrak")
sun.update_traces(hovertemplate="<b>%{label}</b><br>Pelanggan: %{value}<br>Churn rate: %{color:.1%}")
sun.update_coloraxes(colorbar_tickformat=".0%", colorbar_title="Churn rate")
sun.update_layout(template="plotly_white", height=520)

# Gauge: churn rate keseluruhan
gauge = go.Figure(go.Indicator(
    mode="gauge+number", value=rata2 * 100,
    number={"suffix": "%", "valueformat": ".1f"},
    title={"text": "Churn rate keseluruhan"},
    gauge={"axis": {"range": [0, 100], "ticksuffix": "%"}, "bar": {"color": "#C44E52"},
           "steps": [{"range": [0, 20], "color": "#d9efe5"},
                     {"range": [20, 40], "color": "#fbeec7"},
                     {"range": [40, 100], "color": "#f6d5d6"}]}))
gauge.update_layout(template="plotly_white", height=520)

# Filter visual tanpa callback: tombol dropdown bawaan Plotly (updatemenus)
bar_df = df.groupby(["region", "contract_type"], as_index=False)["churn"].mean()
bar = px.bar(bar_df, x="region", y="churn", color="contract_type", barmode="group",
             template="plotly_white", labels={"churn": "Churn rate", "region": "Region",
                                              "contract_type": "Kontrak"},
             title="Churn rate per region dan kontrak")
bar.update_yaxes(tickformat=".0%")
# px memberi setiap trace offsetgroup sendiri -> batang tidak pernah ditumpuk walau barmode="stack".
# Hapus offsetgroup agar semua trace berbagi satu grup dan bisa ditumpuk.
bar.update_traces(offsetgroup=None, alignmentgroup=None)
bar.update_layout(updatemenus=[dict(type="buttons", direction="right", x=1, y=1.15, buttons=[
    dict(label="Grouped", method="relayout", args=[{"barmode": "group"}]),
    dict(label="Stacked", method="relayout", args=[{"barmode": "stack"}]),
])])

app = Dash(__name__, title="Plotly di Dash") 
app.layout = html.Div(style={"maxWidth": "1150px", "margin": "auto", "fontFamily": "Arial"}, children=[ 
    html.H1("Interactive Visualization with Plotly"), 
    html.P("Arahkan kursor (hover), zoom dengan drag, double-click untuk reset, klik legenda untuk filter."), 
    html.Div(style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "12px"}, children=[ 
        dcc.Graph(figure=hist), dcc.Graph(figure=scatter)]), 
    html.Div(style={"display": "grid", "gridTemplateColumns": "3fr 2fr", "gap": "12px"}, children=[
        dcc.Graph(figure=sun), dcc.Graph(figure=gauge)]),
    dcc.Graph(figure=bar_pay),
    dcc.Graph(figure=bar, config={"displaylogo": False,
                                  "toImageButtonOptions": {"format": "png", "scale": 2}}),
])

if __name__ == "__main__": 
    app.run(debug=False, port=8051)