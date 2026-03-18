import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def centered_section_title(text, level=3):
    st.markdown(
        f"<h{level} style='text-align:center; margin-bottom: 0.2rem;'>{text}</h{level}>",
        unsafe_allow_html=True
    )

st.set_page_config(page_title="Loan Portfolio Risk Dashboard", layout="wide")

st.title("Loan Portfolio Risk Dashboard")

# 读取数据
loan_master = pd.read_csv("loan_master.csv")
snapshot = pd.read_csv("loan_snapshot_monthly.csv")

# 日期处理
snapshot["as_of_month"] = pd.to_datetime(snapshot["as_of_month"])

# Sidebar filters
st.sidebar.header("Filters")

selected_month = st.sidebar.selectbox(
    "Reporting Month",
    sorted(snapshot["as_of_month"].dropna().unique())
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

# 过滤当前月份数据
df = snapshot[
    (snapshot["as_of_month"] == selected_month) &
    (snapshot["region"].isin(selected_region)) &
    (snapshot["product_type"].isin(selected_product))
].copy()

# 避免除零错误
total_balance = df["ending_balance"].sum()

if total_balance == 0:
    delq30_rate = 0
    delq90_rate = 0
else:
    delq30_rate = df.loc[df["dpd"] >= 30, "ending_balance"].sum() / total_balance
    delq90_rate = df.loc[df["dpd"] >= 90, "ending_balance"].sum() / total_balance

active_loans = df["loan_id"].nunique()

# 简单 Expected Loss 规则
def calculate_pd(row):
    if row["dpd"] >= 90:
        return 0.70
    elif row["dpd"] >= 60:
        return 0.35
    elif row["dpd"] >= 30:
        return 0.15
    elif row["fico_score"] >= 720:
        return 0.01
    elif row["fico_score"] >= 680:
        return 0.03
    else:
        return 0.06

# PD — Probability of Default
df["PD"] = df.apply(calculate_pd, axis=1)

# LGD — Loss Given Default
df["LGD"] = df["secured_flag"].apply(lambda x: 0.35 if x == 1 else 0.65)

# EAD — Exposure at Default
df["EAD"] = df["ending_balance"]

df["Expected_Loss"] = df["PD"] * df["LGD"] * df["EAD"]

expected_loss = df["Expected_Loss"].sum()

# FICO band
df["fico_band"] = pd.cut(
    df["fico_score"],
    bins=[0, 659, 699, 739, 850],
    labels=["<660", "660-699", "700-739", "740+"]
)

fico_delq = df.groupby("fico_band", as_index=False).apply(
    lambda x: pd.Series({
        "total_balance": x["ending_balance"].sum(),
        "delq30_balance": x.loc[x["dpd"] >= 30, "ending_balance"].sum(),
        "delq30_rate": x.loc[x["dpd"] >= 30, "ending_balance"].sum() / x["ending_balance"].sum() if x["ending_balance"].sum() != 0 else 0
    })
).reset_index(drop=True)


# KPI cards
col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Active Loans", f"{active_loans:,}")
col2.metric("Portfolio Balance", f"${total_balance:,.0f}")
col3.metric("30+ Delinquency Rate", f"{delq30_rate:.2%}")
col4.metric("90+ Delinquency Rate", f"{delq90_rate:.2%}")
col5.metric("Expected Loss", f"${expected_loss:,.0f}")

# -----------------------------
# Delinquency Trend
# -----------------------------
trend_df = snapshot[
    (snapshot["region"].isin(selected_region)) &
    (snapshot["product_type"].isin(selected_product))
].copy()

trend_df["as_of_month"] = pd.to_datetime(trend_df["as_of_month"])

monthly_trend = trend_df.groupby("as_of_month").apply(
    lambda x: pd.Series({
        "total_balance": x["ending_balance"].sum(),
        "delq30_rate": x.loc[x["dpd"] >= 30, "ending_balance"].sum() / x["ending_balance"].sum() if x["ending_balance"].sum() != 0 else 0,
        "delq60_rate": x.loc[x["dpd"] >= 60, "ending_balance"].sum() / x["ending_balance"].sum() if x["ending_balance"].sum() != 0 else 0,
        "delq90_rate": x.loc[x["dpd"] >= 90, "ending_balance"].sum() / x["ending_balance"].sum() if x["ending_balance"].sum() != 0 else 0
    })
).reset_index()

trend_chart_data = monthly_trend.melt(
    id_vars="as_of_month",
    value_vars=["delq30_rate", "delq60_rate", "delq90_rate"],
    var_name="Metric",
    value_name="Rate"
)

metric_name_map = {
    "delq30_rate": "30+ Delinquency",
    "delq60_rate": "60+ Delinquency",
    "delq90_rate": "90+ Delinquency"
}
trend_chart_data["Metric"] = trend_chart_data["Metric"].map(metric_name_map)

fig = px.line(
    trend_chart_data,
    x="as_of_month",
    y="Rate",
    color="Metric",
    markers=True,
    color_discrete_map={
        "30+ Delinquency": "#1f77b4",
        "60+ Delinquency": "#6baed6",
        "90+ Delinquency": "#ef4444"
    }
)

fig.update_traces(
    line=dict(width=3),
    marker=dict(size=6),
    hovertemplate="%{fullData.name}<br>%{x|%b %Y}<br>%{y:.2%}<extra></extra>"
)

fig.update_layout(
    height=460,
    margin=dict(l=0, r=10, t=10, b=10),
    paper_bgcolor="white",
    plot_bgcolor="white",
    font=dict(size=13),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="left",
        x=0,
        title=None
    ),
    xaxis=dict(
        title="Reporting Month",
        showgrid=False,
        tickformat="%b %Y"
    ),
    yaxis=dict(
        title="Rate",
        tickformat=".1%",
        showgrid=True,
        gridcolor="#E5E7EB",
        zeroline=False,
        range=[0, 0.045]
    )
)

# -----------------------------
# Roll-Rate Migration Matrix
# -----------------------------
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
roll_df["next_delq_bucket"] = roll_df.groupby("loan_id")["delq_bucket"].shift(-1)
roll_df = roll_df.dropna(subset=["delq_bucket", "next_delq_bucket"])

bucket_order = ["Current", "30-59", "60-89", "90+"]

migration_matrix = pd.crosstab(
    roll_df["delq_bucket"],
    roll_df["next_delq_bucket"],
    normalize="index"
).reindex(index=bucket_order, columns=bucket_order, fill_value=0)

fig_roll = px.imshow(
    migration_matrix,
    text_auto=".1%",
    aspect="equal",
    color_continuous_scale="Blues"
)

fig_roll.update_traces(
    hovertemplate="Current: %{y}<br>Next: %{x}<br>Rate: %{z:.2%}<extra></extra>"
)

fig_roll.update_layout(
    height=460,
    margin=dict(l=10, r=10, t=10, b=10),
    paper_bgcolor="white",
    plot_bgcolor="white",
    font=dict(size=13),
    xaxis=dict(
        title="Next Month Bucket",
        side="bottom"
    ),
    yaxis=dict(
        title="Current Month Bucket"
    ),
    coloraxis_colorbar=dict(
        title="Rate",
        thickness=14,
        len=0.78
    )
)

# -----------------------------
# Portfolio Risk Monitoring Section
# -----------------------------

col_left, col_right = st.columns([1.15, 1])

with col_left:
    centered_section_title("Delinquency Trend", level=3)
    st.plotly_chart(
        fig,
        use_container_width=True,
        config={"displayModeBar": False}
    )

with col_right:
    centered_section_title("Roll-Rate Migration Matrix", level=3)
    st.plotly_chart(
        fig_roll,
        use_container_width=True,
        config={"displayModeBar": False}
    )

watchlist = df.sort_values("Expected_Loss", ascending=False).head(10)
csv = watchlist.to_csv(index=False).encode("utf-8")

col_title, col_btn = st.columns([3, 1])
with col_title:
    st.subheader("Top 10 high default rate loans")
with col_btn:
    st.download_button(
        label="Download Watchlist CSV",
        data=csv,
        file_name="watchlist_top20.csv",
        mime="text/csv",
    )

st.dataframe(
    watchlist[[
        "loan_id",
        "product_type",
        "region",
        "fico_score",
        "dpd",
        "ending_balance",
        "PD",
        "LGD",
        "Expected_Loss"
    ]]
)
