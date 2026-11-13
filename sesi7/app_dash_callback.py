
from pathlib import Path

import pandas as pd
import plotly.express as px

from dash import (
    Dash,
    html,
    dcc,
    dash_table,
    Input,
    Output,
    State,
    callback,
    ctx,
    no_update,
)
from dash.exceptions import PreventUpdate


# ============================================================
# 1. LOAD DATA
# ============================================================

ROOT = Path(__file__).resolve().parents[1]

df = pd.read_csv(
    ROOT / "data" / "customer_churn.csv",
    parse_dates=["signup_date"]
)

df["status"] = df["churn"].map({
    0: "Bertahan",
    1: "Churn"
})

WARNA = {
    "Bertahan": "#4C72B0",
    "Churn": "#C44E52"
}

KARTU = {
    "flex": 1,
    "padding": "14px",
    "borderRadius": "10px",
    "background": "#F4F6FA",
    "textAlign": "center"
}

INTERNET = sorted(df.internet_service.unique())

TABEL_COLS = [
    "customer_id",
    "region",
    "segment",
    "contract_type",
    "tenure_months",
    "monthly_charges",
    "num_complaints",
    "status"
]

# kolom yang disimpan di dcc.Store (cukup untuk KPI, grafik, tabel, dan detail)
STORE_COLS = TABEL_COLS + ["churn"]


# ============================================================
# 2. INITIALIZE DASH APP
# ============================================================

app = Dash(__name__, title="Dash Callback")

app.layout = html.Div(
    style={
        "maxWidth": "1200px",
        "margin": "auto",
        "fontFamily": "Arial"
    },
    children=[

        html.H1("Dash Callback System — Dashboard Churn"),

        # ----------------------------------------------------
        # PANEL FILTER
        # ----------------------------------------------------

        html.Div(
            style={
                "display": "grid",
                "gridTemplateColumns": "1fr 1fr 1fr",
                "gap": "16px"
            },
            children=[

                html.Div([
                    html.Label("Region"),
                    dcc.Dropdown(
                        id="dd-region",
                        options=sorted(df.region.unique()),
                        multi=True,
                        placeholder="Semua region"
                    )
                ]),

                html.Div([
                    html.Label("Segmen (opsi bergantung region)"),
                    dcc.Dropdown(
                        id="dd-segment",
                        multi=True,
                        placeholder="Semua segmen"
                    )
                ]),

                html.Div([
                    html.Label("Jenis kontrak"),
                    dcc.RadioItems(
                        id="rd-kontrak",
                        inline=True,
                        value="Semua",
                        options=[
                            "Semua",
                            "Bulanan",
                            "Tahunan",
                            "Dua Tahun"
                        ]
                    )
                ])
            ]
        ),

        # INTERNET SERVICE FILTER

        html.Div(
            style={"marginTop": "12px"},
            children=[
                html.Label("Layanan internet"),
                dcc.Checklist(
                    id="cl-internet",
                    options=INTERNET,
                    value=INTERNET,
                    inline=True,
                    inputStyle={"marginLeft": "12px", "marginRight": "4px"}
                )
            ]
        ),

        # TENURE FILTER

        html.Div(
            style={"marginTop": "12px"},
            children=[
                html.Label("Tenure (bulan)"),
                dcc.RangeSlider(
                    id="rs-tenure",
                    min=1,
                    max=72,
                    step=1,
                    value=[1, 72],
                    marks={
                        i: str(i)
                        for i in (1, 12, 24, 36, 48, 60, 72)
                    }
                )
            ]
        ),

        # COMPLAINT FILTER

        html.Div(
            style={
                "display": "flex",
                "gap": "8px",
                "alignItems": "center"
            },
            children=[

                html.Label("Minimal jumlah keluhan:"),

                dcc.Input(
                    id="in-keluhan",
                    type="number",
                    min=0,
                    max=10,
                    value=0,
                    style={"width": "70px"}
                ),

                html.Button(
                    "Terapkan",
                    id="btn-terapkan",
                    n_clicks=0
                ),

                html.Button(
                    "Reset filter",
                    id="btn-reset",
                    n_clicks=0
                ),

                html.Span(
                    id="info-keluhan",
                    style={"color": "#666"}
                )
            ]
        ),

        dcc.Store(
            id="store-keluhan",
            data=0
        ),

        # hasil filter (list of records) — dihitung sekali, dibaca banyak callback
        dcc.Store(id="store-filter"),

        # ----------------------------------------------------
        # KPI SECTION
        # ----------------------------------------------------

        html.Div(
            id="kpi",
            style={
                "display": "flex",
                "gap": "12px",
                "margin": "16px 0"
            }
        ),

        # ----------------------------------------------------
        # CHARTS
        # ----------------------------------------------------

        html.Div(
            style={
                "display": "grid",
                "gridTemplateColumns": "1fr 1fr",
                "gap": "12px"
            },
            children=[
                dcc.Graph(id="g-bar"),
                dcc.Graph(id="g-scatter")
            ]
        ),

        html.Div(
            style={
                "display": "grid",
                "gridTemplateColumns": "1fr 1fr",
                "gap": "12px",
                "marginTop": "12px"
            },
            children=[
                dcc.Graph(id="g-hist"),
                html.Div(
                    id="detail-pelanggan",
                    style={
                        "padding": "16px",
                        "borderRadius": "10px",
                        "background": "#F4F6FA"
                    }
                )
            ]
        ),

        html.P(
            "Tip: klik batang region, atau pilih titik scatter dengan box/lasso select, "
            "untuk memfilter tabel di bawah. Klik satu titik scatter untuk melihat detailnya.",
            style={"color": "#666"}
        ),

        # ----------------------------------------------------
        # DATA TABLE
        # ----------------------------------------------------

        html.H3(id="judul-tabel"),

        html.Button(
            "⬇️ Unduh data tabel (CSV)",
            id="btn-unduh",
            n_clicks=0,
            style={"marginBottom": "8px"}
        ),

        dcc.Download(id="unduh-csv"),

        dash_table.DataTable(
            id="tbl",
            page_size=10,
            sort_action="native",

            columns=[
                {"name": c, "id": c}
                for c in TABEL_COLS
            ],

            style_cell={
                "padding": "6px",
                "textAlign": "left"
            },

            style_header={
                "fontWeight": "bold",
                "background": "#E9EDF5"
            },

            style_data_conditional=[
                {
                    "if": {
                        "filter_query": "{status} = 'Churn'"
                    },
                    "backgroundColor": "#FBE9EA"
                }
            ]
        )
    ]
)


# ============================================================
# 3. FILTER FUNCTION
# ============================================================

def filter_df(region, segment, kontrak, tenure, min_keluhan, internet=None):

    d = df

    if region:
        d = d[d.region.isin(region)]

    if segment:
        d = d[d.segment.isin(segment)]

    if kontrak and kontrak != "Semua":
        d = d[d.contract_type == kontrak]

    if internet is not None:
        d = d[d.internet_service.isin(internet)]

    d = d[
        d.tenure_months.between(
            tenure[0],
            tenure[1]
        )
    ]

    return d[
        d.num_complaints >= (min_keluhan or 0)
    ]


# ============================================================
# 4. CALLBACK 1
# CHAINED CALLBACK:
# SEGMENT OPTIONS DEPEND ON SELECTED REGION
# ============================================================

@callback(
    Output("dd-segment", "options"),
    Input("dd-region", "value")
)
def update_segment_options(region):

    d = df[df.region.isin(region)] if region else df

    return sorted(d.segment.unique())


# ============================================================
# 5. CALLBACK 2
# STATE + BUTTON + CTX
# APPLY FILTER OR RESET FILTER
# ============================================================

@callback(
    Output("store-keluhan", "data"),
    Output("in-keluhan", "value"),
    Output("dd-region", "value"),
    Output("dd-segment", "value"),
    Output("rd-kontrak", "value"),
    Output("rs-tenure", "value"),
    Output("cl-internet", "value"),

    Input("btn-terapkan", "n_clicks"),
    Input("btn-reset", "n_clicks"),

    State("in-keluhan", "value"),

    prevent_initial_call=True
)
def terapkan_atau_reset(n_apply, n_reset, nilai):

    if ctx.triggered_id == "btn-reset":

        return (
            0,
            0,
            None,
            None,
            "Semua",
            [1, 72],
            INTERNET
        )

    if nilai is None:
        raise PreventUpdate

    return (
        nilai,
        no_update,
        no_update,
        no_update,
        no_update,
        no_update,
        no_update
    )


# ============================================================
# 6. CALLBACK 3a
# HITUNG FILTER SEKALI -> SIMPAN DI dcc.Store (to_dict("records"))
# ============================================================

@callback(
    Output("store-filter", "data"),

    Input("dd-region", "value"),
    Input("dd-segment", "value"),
    Input("rd-kontrak", "value"),
    Input("rs-tenure", "value"),
    Input("store-keluhan", "data"),
    Input("cl-internet", "value")
)
def simpan_hasil_filter(region, segment, kontrak, tenure, min_keluhan, internet):

    d = filter_df(
        region,
        segment,
        kontrak,
        tenure,
        min_keluhan,
        internet
    )

    return d[STORE_COLS].to_dict("records")


# ============================================================
# 7. CALLBACK 3b
# MAIN CALLBACK (BACA DARI STORE):
# UPDATE KPI + BAR + SCATTER + INFO + HISTOGRAM TENURE
# ============================================================

@callback(
    Output("kpi", "children"),
    Output("g-bar", "figure"),
    Output("g-scatter", "figure"),
    Output("info-keluhan", "children"),
    Output("g-hist", "figure"),

    Input("store-filter", "data"),
    State("store-keluhan", "data")
)
def update_dashboard(data, min_keluhan):

    d = pd.DataFrame(data or [])

    info = f"Filter keluhan aktif: ≥ {min_keluhan}"

    # HANDLE EMPTY DATA

    if d.empty:

        kosong = px.scatter(
            title="Tidak ada data untuk filter ini"
        )

        return (
            [html.Div("Data kosong", style=KARTU)],
            kosong,
            kosong,
            info,
            kosong
        )

    # KPI CARD FUNCTION

    def kartu(j, v):

        return html.Div(
            [
                html.Small(j),
                html.H2(
                    v,
                    style={"margin": "4px 0"}
                )
            ],
            style=KARTU
        )

    # KPI CALCULATIONS

    kpi = [
        kartu("Pelanggan", f"{len(d):,}"),

        kartu(
            "Churn rate",
            f"{d.churn.mean():.1%}"
        ),

        kartu(
            "Rata-rata tagihan",
            f"Rp{d.monthly_charges.mean():,.0f}".replace(",", ".")
        ),

        kartu(
            "Rata-rata keluhan",
            f"{d.num_complaints.mean():.2f}"
        )
    ]

    # BAR CHART: CHURN RATE PER REGION

    reg = (
        d.groupby("region", as_index=False)["churn"]
        .mean()
        .sort_values("churn", ascending=False)
    )

    bar = px.bar(
        reg,
        x="region",
        y="churn",
        template="plotly_white",
        title="Churn rate per region",
        labels={
            "churn": "Churn rate",
            "region": ""
        },
        color_discrete_sequence=["#C44E52"]
    )

    bar.update_yaxes(
        tickformat=".0%"
    )

    # SCATTER CHART: TENURE VS MONTHLY CHARGES
    # custom_data=customer_id dipakai untuk klik (detail) dan select (filter tabel)

    sc = px.scatter(
        d,
        x="tenure_months",
        y="monthly_charges",
        color="status",
        opacity=0.6,
        color_discrete_map=WARNA,
        template="plotly_white",
        hover_name="customer_id",
        custom_data=["customer_id"],
        title="Tenure vs tagihan (klik = detail, box/lasso = filter tabel)",
        labels={
            "tenure_months": "Tenure (bulan)",
            "monthly_charges": "Tagihan (Rp)"
        }
    )

    sc.update_layout(dragmode="select")

    # HISTOGRAM TENURE (IKUT TERFILTER)

    hist = px.histogram(
        d,
        x="tenure_months",
        color="status",
        nbins=36,
        barmode="overlay",
        opacity=0.7,
        color_discrete_map=WARNA,
        template="plotly_white",
        title="Distribusi tenure",
        labels={
            "tenure_months": "Tenure (bulan)",
            "status": "Status"
        }
    )

    return kpi, bar, sc, info, hist


# ============================================================
# 8. CALLBACK 4
# KLIK TITIK SCATTER -> DETAIL PELANGGAN
# ============================================================

DETAIL_AWAL = "Klik satu titik pada scatter untuk melihat detail pelanggan."

@callback(
    Output("detail-pelanggan", "children"),

    Input("g-scatter", "clickData"),
    Input("store-filter", "data")
)
def detail_pelanggan(click, _data):

    # filter berubah -> titik lama mungkin sudah tidak ada: reset
    if ctx.triggered_id != "g-scatter" or not click:
        return DETAIL_AWAL

    cid = click["points"][0]["customdata"][0]

    baris = df[df.customer_id == cid]

    if baris.empty:
        return DETAIL_AWAL

    r = baris.iloc[0]

    return [
        html.H3("Detail pelanggan", style={"marginTop": 0}),
        html.P([html.B("ID: "), r.customer_id]),
        html.P([html.B("Region: "), r.region]),
        html.P([html.B("Kontrak: "), r.contract_type]),
        html.P([html.B("Jumlah keluhan: "), str(int(r.num_complaints))]),
        html.P([html.B("Status: "), r.status])
    ]


# ============================================================
# 9. CALLBACK 5
# TABEL: BACA DARI STORE, DIFILTER OLEH KLIK BAR / SELECT SCATTER
# ============================================================

@callback(
    Output("tbl", "data"),
    Output("judul-tabel", "children"),

    Input("store-filter", "data"),
    Input("g-bar", "clickData"),
    Input("g-scatter", "selectedData")
)
def update_tabel(data, click, selected):

    d = pd.DataFrame(data or [], columns=STORE_COLS)

    judul = "Detail pelanggan (semua region terpilih)"

    if ctx.triggered_id == "g-bar" and click:

        reg = click["points"][0]["x"]

        d = d[d.region == reg]

        judul = f"Detail pelanggan — region {reg}"

    elif ctx.triggered_id == "g-scatter" and selected and selected.get("points"):

        ids = {p["customdata"][0] for p in selected["points"]}

        d = d[d.customer_id.isin(ids)]

        judul = f"Detail pelanggan — {len(d):,} titik terpilih di scatter"

    return (
        d[TABEL_COLS].to_dict("records"),
        judul
    )


# ============================================================
# 10. CALLBACK 6
# UNDUH CSV SESUAI ISI TABEL (SIDEBAR + KLIK BAR + SELECT SCATTER)
# ============================================================

@callback(
    Output("unduh-csv", "data"),

    Input("btn-unduh", "n_clicks"),
    State("tbl", "data"),

    prevent_initial_call=True
)
def unduh_csv(n_clicks, data):

    if not data:
        raise PreventUpdate

    return dcc.send_data_frame(
        pd.DataFrame(data).to_csv,
        "churn_terfilter.csv",
        index=False
    )


# ============================================================
# 11. RUN APP
# ============================================================

if __name__ == "__main__":

    app.run(
        debug=True,
        port=8052
    )
