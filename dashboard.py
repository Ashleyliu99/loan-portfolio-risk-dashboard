import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import base64

# ── Page configutation ───────────────────────────────────────────────
st.set_page_config(
    page_title="Loan Portfolio Risk Dashboard",
    layout="wide",
    page_icon="🏦"
)

# ── Global CSS ────────────────────────────────────────────────
st.markdown("""
<style>
/* Page background */
[data-testid="stAppViewContainer"] { background-color: #F0F4F8; }
[data-testid="stHeader"] { background-color: transparent; }

/* Shrink main content padding so everything fits on one screen */
.block-container {
    padding-top: 1.2rem !important;
    padding-bottom: 0.5rem !important;
    padding-left: 1.5rem !important;
    padding-right: 1.5rem !important;
    max-width: 100% !important;
}

/* Narrow dark navy sidebar */
[data-testid="stSidebar"] {
    background-color: #1E3A5F;
    min-width: 190px !important;
    max-width: 190px !important;
}
[data-testid="stSidebar"] > div:first-child {
    min-width: 190px !important;
    max-width: 190px !important;
    width: 190px !important;
    padding: 1.2rem 0.9rem !important;
}
[data-testid="stSidebar"] * { color: #CBD9EC !important; }
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 { color: #FFFFFF !important; font-size: 0.85rem !important; }
[data-testid="stSidebar"] label {
    font-size: 0.7rem !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
    color: #93B8D8 !important;
}
[data-testid="stSidebar"] [data-baseweb="select"] > div {
    background-color: #2B4F7A;
    border-color: #3D6FA0;
    font-size: 0.78rem;
}
[data-testid="stSidebar"] [data-baseweb="tag"] {
    background-color: #3D6FA0 !important;
    font-size: 0.7rem !important;
}
[data-testid="stSidebar"] [data-baseweb="tag"] span { color: #FFFFFF !important; }
[data-testid="stSidebar"] hr { border-color: #2D5A8E !important; margin: 0.6rem 0 !important; }
[data-testid="stSidebar"] [data-baseweb="select"] [aria-label="Clear all"] { display: none !important; }

/* Centered page title */
h1 {
    color: #1E3A5F !important;
    font-weight: 800 !important;
    font-size: 1.75rem !important;
    margin-bottom: 0 !important;
    text-align: center !important;
}

/* KPI cards — uniform size, no text wrap */
.kpi-card {
    background: white;
    border-radius: 10px;
    padding: 0.85rem 1rem;
    border-left: 5px solid;
    box-shadow: 0 1px 5px rgba(0,0,0,0.09);
    min-width: 0;
}
.kpi-label {
    font-size: 0.65rem;
    color: #6B7280;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    margin-bottom: 0.35rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.kpi-value {
    font-size: 1.4rem;
    font-weight: 800;
    color: #111827;
    line-height: 1.15;
    white-space: nowrap;
}

/* Divider — tighter */
.divider {
    border: none;
    border-top: 1.5px solid #DDE3EC;
    margin: 1rem 0 0.6rem 0;
}

/* Chart section title — larger */
.chart-title {
    text-align: center;
    font-size: 1.05rem;
    font-weight: 700;
    color: #1E3A5F;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin: 0 0 0.3rem 0;
}

/* Watchlist heading — matches chart-title */
.watchlist-heading {
    font-size: 1.05rem;
    font-weight: 700;
    color: #1E3A5F;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    line-height: 2.4rem;
    margin: 0;
    padding: 0;
}

/* Download button */
.stDownloadButton > button {
    background-color: #1E3A5F !important;
    color: white !important;
    border: none !important;
    border-radius: 6px !important;
    padding: 0.42rem 1rem !important;
    font-weight: 600 !important;
    font-size: 0.83rem !important;
    margin-top: 0.3rem;
    float: right;
}
.stDownloadButton > button:hover { background-color: #2D5A8E !important; }
</style>
""", unsafe_allow_html=True)


def kpi_card(label, value, accent):
    st.markdown(f"""
    <div class="kpi-card" style="border-left-color:{accent};">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
    </div>
    """, unsafe_allow_html=True)


def centered_section_title(text, level=3):
    st.markdown(f"<p class='chart-title'>{text}</p>", unsafe_allow_html=True)


def divider():
    st.markdown('<hr class="divider">', unsafe_allow_html=True)


# ── Page header ───────────────────────────────────────────────
st.title("🏦 Loan Portfolio Risk Dashboard")
st.markdown(
    "<p style='color:#6B7280; font-size:0.85rem; margin-top:0.1rem; margin-bottom:0.8rem; text-align:center;'>"
    "Monthly snapshot · Risk monitoring &amp; delinquency analysis</p>",
    unsafe_allow_html=True
)

# ── Load data ─────────────────────────────────────────────────
loan_master = pd.read_csv("loan_master.csv")
snapshot    = pd.read_csv("loan_snapshot_monthly.csv")
snapshot["as_of_month"] = pd.to_datetime(snapshot["as_of_month"])

# ── Sidebar filters ───────────────────────────────────────────
st.sidebar.markdown("## Filters")
st.sidebar.markdown("---")

month_options = sorted(snapshot["as_of_month"].dt.strftime("%Y-%m-%d").dropna().unique())
default_month = "2025-10-31"
default_index = month_options.index(default_month) if default_month in month_options else len(month_options) - 1

selected_month = st.sidebar.selectbox(
    "Reporting Month",
    options=month_options,
    index=default_index
)

selected_region = st.sidebar.multiselect(
    "Region",
    options=sorted(snapshot["region"].dropna().unique()),
    default=sorted(snapshot["region"].dropna().unique())
)

selected_product = st.sidebar.multiselect(
    "Product Type",
    options=sorted(snapshot["product_type"].dropna().unique()),
    default=sorted(snapshot["product_type"].dropna().unique())
)

# ── Filter data ───────────────────────────────────────────────
df = snapshot[
    (snapshot["as_of_month"].dt.strftime("%Y-%m-%d") == selected_month) &
    (snapshot["region"].isin(selected_region)) &
    (snapshot["product_type"].isin(selected_product))
].copy()

total_balance = df["ending_balance"].sum()

if total_balance == 0:
    delq30_rate = delq90_rate = 0
else:
    delq30_rate = df.loc[df["dpd"] >= 30, "ending_balance"].sum() / total_balance
    delq90_rate = df.loc[df["dpd"] >= 90, "ending_balance"].sum() / total_balance

active_loans = df["loan_id"].nunique()

# ── Expected Loss calculation ─────────────────────────────────
def calculate_pd(row):
    if row["dpd"] >= 90:           return 0.70
    elif row["dpd"] >= 60:         return 0.35
    elif row["dpd"] >= 30:         return 0.15
    elif row["fico_score"] >= 720: return 0.01
    elif row["fico_score"] >= 680: return 0.03
    else:                          return 0.06

df["PD"]  = df.apply(calculate_pd, axis=1)
df["LGD"] = df["secured_flag"].apply(lambda x: 0.35 if x == 1 else 0.65)
df["EAD"] = df["ending_balance"]
df["Expected_Loss"] = df["PD"] * df["LGD"] * df["EAD"]
expected_loss = df["Expected_Loss"].sum()

# ── FICO band ─────────────────────────────────────────────────
df["fico_band"] = pd.cut(
    df["fico_score"],
    bins=[0, 659, 699, 739, 850],
    labels=["<660", "660-699", "700-739", "740+"]
)

fico_delq = df.groupby("fico_band", as_index=False).apply(
    lambda x: pd.Series({
        "total_balance":  x["ending_balance"].sum(),
        "delq30_balance": x.loc[x["dpd"] >= 30, "ending_balance"].sum(),
        "delq30_rate":    x.loc[x["dpd"] >= 30, "ending_balance"].sum() / x["ending_balance"].sum()
                          if x["ending_balance"].sum() != 0 else 0
    })
).reset_index(drop=True)

# ── KPI cards ─────────────────────────────────────────────────
c1, c2, c3, c4, c5 = st.columns(5)
with c1: kpi_card("Active Loans",      f"{active_loans:,}",       "#3B82F6")
with c2: kpi_card("Portfolio Balance", f"${total_balance:,.0f}",  "#10B981")
with c3: kpi_card("30+ Delinquency",   f"{delq30_rate:.2%}",      "#F59E0B")
with c4: kpi_card("90+ Delinquency",   f"{delq90_rate:.2%}",      "#EF4444")
with c5: kpi_card("Expected Loss",     f"${expected_loss:,.0f}",  "#8B5CF6")

divider()

# ── Delinquency Trend ─────────────────────────────────────────
trend_df = snapshot[
    (snapshot["region"].isin(selected_region)) &
    (snapshot["product_type"].isin(selected_product))
].copy()

trend_df["as_of_month"] = pd.to_datetime(trend_df["as_of_month"])

# 只保留 selected_month 往前 12 个月到 selected_month 本身，共 13 个月
trend_end = pd.to_datetime(selected_month)
trend_start = trend_end - pd.DateOffset(months=12)

trend_df = trend_df[
    (trend_df["as_of_month"] >= trend_start) &
    (trend_df["as_of_month"] <= trend_end)
].copy()

monthly_trend = trend_df.groupby("as_of_month").apply(
    lambda x: pd.Series({
        "total_balance": x["ending_balance"].sum(),
        "delq30_rate":   x.loc[x["dpd"] >= 30, "ending_balance"].sum() / x["ending_balance"].sum() if x["ending_balance"].sum() != 0 else 0,
        "delq60_rate":   x.loc[x["dpd"] >= 60, "ending_balance"].sum() / x["ending_balance"].sum() if x["ending_balance"].sum() != 0 else 0,
        "delq90_rate":   x.loc[x["dpd"] >= 90, "ending_balance"].sum() / x["ending_balance"].sum() if x["ending_balance"].sum() != 0 else 0
    })
).reset_index()

trend_chart_data = monthly_trend.melt(
    id_vars="as_of_month",
    value_vars=["delq30_rate", "delq60_rate", "delq90_rate"],
    var_name="Metric", value_name="Rate"
)
trend_chart_data["Metric"] = trend_chart_data["Metric"].map({
    "delq30_rate": "30+ Delinquency",
    "delq60_rate": "60+ Delinquency",
    "delq90_rate": "90+ Delinquency"
})

fig = px.line(
    trend_chart_data, x="as_of_month", y="Rate", color="Metric", markers=True,
    color_discrete_map={
        "30+ Delinquency": "#3B82F6",
        "60+ Delinquency": "#93C5FD",
        "90+ Delinquency": "#EF4444"
    }
)
fig.update_traces(
    line=dict(width=2.5), marker=dict(size=6),
    hovertemplate="%{fullData.name}<br>%{x|%b %Y}<br>%{y:.2%}<extra></extra>"
)

tick_dates = sorted(monthly_trend["as_of_month"].unique())
tick_dates_show = tick_dates[::2]

if tick_dates[-1] not in tick_dates_show:
    tick_dates_show.append(tick_dates[-1])

fig.update_layout(
    height=340,
    margin=dict(l=0, r=10, t=10, b=10),
    paper_bgcolor="white", plot_bgcolor="white",
    font=dict(size=12, color="#374151"),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, title=None),
    xaxis=dict(
    title="Reporting Month",
    showgrid=False,
    tickfont=dict(size=11),
    tickmode="array",
    tickvals=tick_dates_show,
    ticktext=[pd.to_datetime(d).strftime("%b %Y") for d in tick_dates_show]),
    yaxis=dict(title="Rate", tickformat=".1%", showgrid=True, gridcolor="#F0F4F8", zeroline=False, range=[0, 0.045])
)

# ── Roll-Rate Migration Matrix ────────────────────────────────
roll_df = snapshot[
    (snapshot["region"].isin(selected_region)) &
    (snapshot["product_type"].isin(selected_product))
].copy()

roll_df["as_of_month"] = pd.to_datetime(roll_df["as_of_month"])

roll_df["delq_bucket"] = pd.cut(
    roll_df["dpd"],
    bins=[-1, 29, 59, 89, float("inf")],
    labels=["Current", "30-59", "60-89", "90+"]
)

roll_df = roll_df.sort_values(["loan_id", "as_of_month"])

# 上一条记录的 bucket 和月份
roll_df["prev_delq_bucket"] = roll_df.groupby("loan_id")["delq_bucket"].shift(1)
roll_df["prev_as_of_month"] = roll_df.groupby("loan_id")["as_of_month"].shift(1)

# 计算上一条记录与当前记录之间是否正好相差 1 个月
roll_df["month_diff"] = (
    (roll_df["as_of_month"].dt.year - roll_df["prev_as_of_month"].dt.year) * 12 +
    (roll_df["as_of_month"].dt.month - roll_df["prev_as_of_month"].dt.month)
)

# 只保留：
# 1) 当前是 selected_month
# 2) 存在 previous month bucket
# 3) previous record 与 current record 正好相差 1 个月
roll_month = roll_df[
    (roll_df["as_of_month"] == pd.to_datetime(selected_month)) &
    (roll_df["prev_delq_bucket"].notna()) &
    (roll_df["month_diff"] == 1)
].copy()

bucket_order = ["Current", "30-59", "60-89", "90+"]

if roll_month.empty:
    fig_roll = px.imshow(
        pd.DataFrame(0, index=bucket_order, columns=bucket_order),
        text_auto=".1%",
        aspect="equal",
        color_continuous_scale=[[0, "#EFF6FF"], [0.5, "#3B82F6"], [1, "#1E3A5F"]]
    )

    fig_roll.update_layout(
        height=340,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(size=12, color="#374151"),
        xaxis=dict(title="Current Month Bucket", side="bottom"),
        yaxis=dict(title="Previous Month Bucket"),
        coloraxis_colorbar=dict(title="Rate", thickness=14, len=0.78)
    )
else:
    migration_matrix = pd.crosstab(
        roll_month["prev_delq_bucket"],
        roll_month["delq_bucket"],
        normalize="index"
    ).reindex(index=bucket_order, columns=bucket_order, fill_value=0)

    fig_roll = px.imshow(
        migration_matrix,
        text_auto=".1%",
        aspect="equal",
        color_continuous_scale=[[0, "#EFF6FF"], [0.5, "#3B82F6"], [1, "#1E3A5F"]]
    )

    fig_roll.update_traces(
        hovertemplate="Previous: %{y}<br>Current: %{x}<br>Rate: %{z:.2%}<extra></extra>"
    )

    fig_roll.update_layout(
        height=340,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(size=12, color="#374151"),
        xaxis=dict(title="Current Month Bucket", side="bottom"),
        yaxis=dict(title="Previous Month Bucket"),
        coloraxis_colorbar=dict(title="Rate",tickformat=".0%",thickness=14, len=0.78)
    )




fig_roll.update_layout(
    height=340,
    margin=dict(l=10, r=10, t=10, b=10),
    paper_bgcolor="white", plot_bgcolor="white",
    font=dict(size=12, color="#374151"),
    xaxis=dict(title="Current Month Bucket", side="bottom"),
    yaxis=dict(title="Previous Month Bucket"),
    coloraxis_colorbar=dict(title="Rate", thickness=14, len=0.78)
)

# ── Charts layout ─────────────────────────────────────────────
col_left, col_right = st.columns([1.15, 1])

with col_left:
    centered_section_title("Delinquency Trend")
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with col_right:
    centered_section_title("Roll-Rate Migration Matrix")
    st.plotly_chart(fig_roll, use_container_width=True, config={"displayModeBar": False})

divider()

# ── Watchlist ─────────────────────────────────────────────────
watchlist = df.sort_values("Expected_Loss", ascending=False).head(10)
csv = watchlist.to_csv(index=False).encode("utf-8")

csv_b64 = base64.b64encode(csv).decode()
st.markdown(f"""
<div style="display:flex; justify-content:center; align-items:center; gap:1rem; margin-bottom:0.5rem;">
    <p class="watchlist-heading" style="margin:0;">Top 10 Loans by Expected Loss</p>
    <a href="data:text/csv;base64,{csv_b64}" download="watchlist_top10.csv"
       style="background:#1E3A5F; color:white; padding:0.4rem 1rem; border-radius:6px;
              font-weight:600; font-size:0.83rem; text-decoration:none; white-space:nowrap;">
        ⬇ Download Watchlist CSV
    </a>
</div>
""", unsafe_allow_html=True)

# Format display columns
watchlist_display = watchlist[[
    "loan_id", "product_type", "region",
    "fico_score", "dpd", "ending_balance", "PD", "LGD", "Expected_Loss"
]].copy()
watchlist_display.columns = [
    "Loan ID", "Product", "Region",
    "FICO Score", "Days Past Due", "Balance", "PD", "LGD", "Expected Loss"
]
watchlist_display["Balance"]       = watchlist_display["Balance"].apply(lambda x: f"${x:,.0f}")
watchlist_display["Expected Loss"] = watchlist_display["Expected Loss"].apply(lambda x: f"${x:,.0f}")
watchlist_display["PD"]            = watchlist_display["PD"].apply(lambda x: f"{x:.0%}")
watchlist_display["LGD"]           = watchlist_display["LGD"].apply(lambda x: f"{x:.0%}")

st.dataframe(watchlist_display, use_container_width=True, hide_index=True)
