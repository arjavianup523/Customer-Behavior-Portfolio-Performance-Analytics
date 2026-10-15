
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "processed"

NAVY = "#0B1120"
PANEL = "#141E30"
TEAL = "#39D6C0"
TEXT = "#F0F4FA"
MUTED = "#9BAAC0"
BLUE = "#809BFF"

st.set_page_config(
    page_title="NEXUS | Customer Intelligence",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    f"""
    <style>
    .stApp {{ background:{NAVY}; color:{TEXT}; }}
    [data-testid="stSidebar"] {{
        background:#080E1A; border-right:1px solid #26334A;
    }}
    .block-container {{ padding-top:2.2rem; max-width:1500px; }}
    h1,h2,h3,p,label {{ color:{TEXT}; }}
    .eyebrow {{
        color:{TEAL}; letter-spacing:3px; font-size:11px;
        font-weight:800; text-transform:uppercase;
    }}
    .muted {{ color:{MUTED}; font-size:14px; }}
    .kpi {{
        background:linear-gradient(145deg,#18243A,#111A2B);
        border:1px solid #2B3950; border-radius:15px;
        padding:20px; min-height:135px;
    }}
    .kpi-label {{ color:{MUTED}; font-size:12px; letter-spacing:1px; }}
    .kpi-value {{ color:{TEXT}; font-size:29px; font-weight:750; margin-top:12px; }}
    .kpi-note {{ color:{TEAL}; font-size:12px; margin-top:5px; }}
    div[data-testid="stPlotlyChart"] {{
        background:{PANEL}; border:1px solid #26344A;
        border-radius:14px; padding:8px;
    }}
    div[data-testid="stDataFrame"] {{
        border:1px solid #26344A; border-radius:12px;
    }}
    div.stButton > button, div.stDownloadButton > button {{
        border-radius:9px; border:1px solid #34445E;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_data():
    transactions = pd.read_csv(
        DATA / "clean_transactions.csv",
        parse_dates=["InvoiceDate"],
    )
    rfm = pd.read_csv(DATA / "customer_rfm_segments.csv")
    monthly = pd.read_csv(DATA / "monthly_performance.csv")
    segments = pd.read_csv(DATA / "segment_summary.csv")
    retention = pd.read_csv(DATA / "cohort_retention.csv", index_col=0)
    return transactions, rfm, monthly, segments, retention


st.sidebar.markdown(
    '<p class="eyebrow">NEXUS INTELLIGENCE</p>',
    unsafe_allow_html=True,
)
st.sidebar.title("Customer Analytics")
st.sidebar.caption("Retail performance platform")
page = st.sidebar.radio(
    "WORKSPACE",
    [
        "Executive Overview",
        "Customer Segments",
        "Retention & Cohorts",
        "Product Performance",
        "Explore Transactions",
    ],
)
st.sidebar.divider()

try:
    transactions, rfm, monthly, segments, retention = load_data()
except FileNotFoundError as exc:
    st.error(f"Required project data is missing: {exc}")
    st.info(
        "Run src/clean_data.py, src/customer_segmentation.py, "
        "and src/retention_analysis.py first."
    )
    st.stop()
except Exception as exc:
    st.error(f"Unable to load the analytics files: {exc}")
    st.stop()

countries = sorted(transactions["Country"].dropna().unique())
default_countries = ["United Kingdom"] if "United Kingdom" in countries else countries[:1]
selected_countries = st.sidebar.multiselect(
    "Countries",
    countries,
    default=default_countries,
)
date_min = transactions["InvoiceDate"].min().date()
date_max = transactions["InvoiceDate"].max().date()
date_range = st.sidebar.date_input(
    "Purchase date range",
    value=(date_min, date_max),
    min_value=date_min,
    max_value=date_max,
)

if not selected_countries:
    st.warning("Select at least one country in the sidebar.")
    st.stop()

if not isinstance(date_range, (tuple, list)) or len(date_range) != 2:
    st.info("Select both a start date and an end date.")
    st.stop()

start_date, end_date = date_range
if start_date > end_date:
    st.error("The start date must be before the end date.")
    st.stop()

df = transactions[
    transactions["Country"].isin(selected_countries)
    & transactions["InvoiceDate"].dt.date.between(start_date, end_date)
].copy()

if df.empty:
    st.warning("No transactions match your selected filters.")
    st.stop()

df["CustomerID"] = df["CustomerID"].astype(str)
revenue = df["Revenue"].sum()
orders = df["InvoiceNo"].nunique()
customers = df["CustomerID"].nunique()
aov = revenue / orders if orders else 0


def money(value):
    return f"£{value:,.0f}"


def kpi(label, value, note):
    st.markdown(
        f'<div class="kpi"><div class="kpi-label">{label}</div>'
        f'<div class="kpi-value">{value}</div>'
        f'<div class="kpi-note">{note}</div></div>',
        unsafe_allow_html=True,
    )


def style_chart(fig, height=350):
    fig.update_layout(
        height=height,
        paper_bgcolor=PANEL,
        plot_bgcolor=PANEL,
        font=dict(color=TEXT, family="Arial"),
        margin=dict(l=18, r=18, t=48, b=20),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor="rgba(0,0,0,0)",
        ),
    )
    fig.update_xaxes(showgrid=False, linecolor="#344159")
    fig.update_yaxes(showgrid=True, gridcolor="#253249")
    return fig


st.markdown(
    '<p class="eyebrow">DATA-DRIVEN COMMERCIAL STRATEGY</p>',
    unsafe_allow_html=True,
)
st.title(page)
st.markdown(
    '<p class="muted">Customer behavior · Revenue intelligence · '
    'Retention performance</p>',
    unsafe_allow_html=True,
)

if page == "Executive Overview":
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi("SALES REVENUE", money(revenue), "Selected markets and dates")
    with c2:
        kpi("IDENTIFIED CUSTOMERS", f"{customers:,}", "Unique customer IDs")
    with c3:
        kpi("INVOICES", f"{orders:,}", "Distinct invoices")
    with c4:
        kpi("AVERAGE ORDER VALUE", f"£{aov:,.2f}", "Revenue per invoice")

    st.write("")
    left, right = st.columns([1.6, 1])

    monthly_view = df.assign(
        Month=df["InvoiceDate"].dt.to_period("M").astype(str)
    ).groupby("Month", as_index=False).agg(
        Revenue=("Revenue", "sum"),
        Orders=("InvoiceNo", "nunique"),
    )

    with left:
        st.subheader("Revenue momentum")
        fig = px.area(
            monthly_view,
            x="Month",
            y="Revenue",
            markers=True,
            color_discrete_sequence=[TEAL],
        )
        fig.update_traces(
            line=dict(width=3),
            fillcolor="rgba(57,214,192,0.13)",
        )
        st.plotly_chart(style_chart(fig), use_container_width=True)

    with right:
        st.subheader("Leading countries")
        country_view = (
            df.groupby("Country", as_index=False)["Revenue"]
            .sum()
            .nlargest(10, "Revenue")
            .sort_values("Revenue")
        )
        fig = px.bar(
            country_view,
            x="Revenue",
            y="Country",
            orientation="h",
            color_discrete_sequence=[TEAL],
        )
        st.plotly_chart(style_chart(fig), use_container_width=True)

    st.subheader("Commercial snapshot")
    best_month = monthly_view.loc[
        monthly_view["Revenue"].idxmax(), "Month"
    ]
    best_value = monthly_view["Revenue"].max()
    a, b = st.columns(2)
    with a:
        st.metric("Highest-revenue month in selected data", best_month)
    with b:
        st.metric("Revenue in that month", money(best_value))

    st.caption(
        "Revenue is quantity × unit price in the source currency (GBP). "
        "Cancelled invoices and invalid sales rows were excluded during cleaning."
    )

elif page == "Customer Segments":
    st.subheader("RFM segmentation")
    st.markdown(
        '<p class="muted">Recency, invoice frequency and customer monetary value.</p>',
        unsafe_allow_html=True,
    )

    names = sorted(rfm["Segment"].dropna().unique())
    chosen = st.multiselect("Customer segments", names, default=names)
    view = rfm[rfm["Segment"].isin(chosen)].copy()

    if view.empty:
        st.warning("Select one or more customer segments.")
        st.stop()

    left, right = st.columns(2)
    segment_counts = (
        view.groupby("Segment", as_index=False)
        .agg(Customers=("CustomerID", "nunique"))
        .sort_values("Customers")
    )
    with left:
        st.subheader("Customer distribution")
        fig = px.bar(
            segment_counts,
            x="Customers",
            y="Segment",
            orientation="h",
            color_discrete_sequence=[TEAL],
        )
        st.plotly_chart(style_chart(fig), use_container_width=True)

    with right:
        st.subheader("Frequency vs. value")
        fig = px.scatter(
            view,
            x="Frequency",
            y="Monetary",
            color="Segment",
            hover_data=["CustomerID", "Recency"],
        )
        st.plotly_chart(style_chart(fig), use_container_width=True)

    st.subheader("Customer-level explorer")
    st.dataframe(
        view.sort_values("Monetary", ascending=False),
        use_container_width=True,
        hide_index=True,
    )
    st.download_button(
        "Download customer segments",
        view.to_csv(index=False).encode("utf-8"),
        "customer_segments.csv",
        "text/csv",
    )

elif page == "Retention & Cohorts":
    st.subheader("Cohort retention heatmap")
    st.caption(
        "Month 0 is the first purchase month. Each cell shows the percentage "
        "of a cohort that purchased during that month."
    )
    heat = retention.copy()
    heat.index = heat.index.astype(str)
    heat.columns = [str(c) for c in heat.columns]

    fig = go.Figure(
        data=go.Heatmap(
            z=heat.values,
            x=heat.columns,
            y=heat.index,
            colorscale=[
                [0, "#18243A"],
                [0.5, "#167E83"],
                [1, TEAL],
            ],
            colorbar=dict(title="Retention %"),
            hovertemplate=(
                "Cohort: %{y}<br>Period: %{x}"
                "<br>Retention: %{z:.1f}%<extra></extra>"
            ),
        )
    )
    st.plotly_chart(style_chart(fig, 520), use_container_width=True)

    purchase_counts = (
        df.groupby("CustomerID")["InvoiceNo"].nunique()
    )
    repeat = int((purchase_counts >= 2).sum())
    one_time = int((purchase_counts == 1).sum())
    repeat_rate = repeat / len(purchase_counts) * 100 if len(purchase_counts) else 0

    a, b, c = st.columns(3)
    with a:
        kpi("REPEAT CUSTOMERS", f"{repeat:,}", "In selected data")
    with b:
        kpi("ONE-TIME CUSTOMERS", f"{one_time:,}", "In selected data")
    with c:
        kpi("REPEAT RATE", f"{repeat_rate:.1f}%", "Customers with 2+ invoices")

    fig = px.pie(
        names=["Repeat customers", "One-time customers"],
        values=[repeat, one_time],
        hole=0.68,
        color_discrete_sequence=[TEAL, BLUE],
    )
    fig.update_traces(textinfo="label+percent")
    st.plotly_chart(style_chart(fig), use_container_width=True)

elif page == "Product Performance":
    st.subheader("Product revenue ranking")
    product_view = (
        df.groupby("Description", as_index=False)
        .agg(
            Revenue=("Revenue", "sum"),
            Units=("Quantity", "sum"),
            Invoices=("InvoiceNo", "nunique"),
        )
        .sort_values("Revenue", ascending=False)
    )

    top_n = st.slider("Products to display", 5, 30, 15)
    top_products = product_view.head(top_n).sort_values("Revenue")
    fig = px.bar(
        top_products,
        x="Revenue",
        y="Description",
        orientation="h",
        color_discrete_sequence=[TEAL],
        hover_data=["Units", "Invoices"],
    )
    st.plotly_chart(style_chart(fig, 520), use_container_width=True)

    st.subheader("Product detail")
    st.dataframe(product_view, use_container_width=True, hide_index=True)
    st.download_button(
        "Download product analysis",
        product_view.to_csv(index=False).encode("utf-8"),
        "product_performance.csv",
        "text/csv",
    )

elif page == "Explore Transactions":
    st.subheader("Transaction-level explorer")
    search = st.text_input("Search product description")
    view = df.copy()

    if search.strip():
        view = view[
            view["Description"].fillna("").str.contains(
                search.strip(), case=False, regex=False
            )
        ]

    st.write(f"**{len(view):,}** transaction rows match your filters.")
    st.dataframe(
        view.sort_values("InvoiceDate", ascending=False),
        use_container_width=True,
        hide_index=True,
    )
    st.download_button(
        "Download filtered transactions",
        view.to_csv(index=False).encode("utf-8"),
        "filtered_transactions.csv",
        "text/csv",
    )

st.divider()
st.caption(
    "NEXUS Customer Intelligence · Built with Python, Pandas, Plotly and Streamlit · "
    "Dataset: UCI Online Retail"
)
