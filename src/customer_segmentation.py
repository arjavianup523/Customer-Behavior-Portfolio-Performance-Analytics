from pathlib import Path
import pandas as pd
import numpy as np
import json

ROOT = Path(__file__).resolve().parent.parent
INPUT = ROOT / "data" / "processed" / "clean_transactions.csv"
OUT = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"

df = pd.read_csv(INPUT, parse_dates=["InvoiceDate"])
df["CustomerID"] = df["CustomerID"].astype(str)

# Use the day after the last transaction as the analysis reference date.
reference_date = df["InvoiceDate"].max().normalize() + pd.Timedelta(days=1)

rfm = (
    df.groupby("CustomerID")
    .agg(
        LastPurchase=("InvoiceDate", "max"),
        Frequency=("InvoiceNo", "nunique"),
        Monetary=("Revenue", "sum"),
        TotalItems=("Quantity", "sum"),
    )
    .reset_index()
)

rfm["Recency"] = (reference_date - rfm["LastPurchase"].dt.normalize()).dt.days
rfm["Monetary"] = rfm["Monetary"].round(2)

# Quantile scores: 1 is weakest and 5 is strongest.
# Recency is reversed because fewer days since purchase is better.
def quantile_score(series, reverse=False):
    ranks = series.rank(method="first", ascending=True)
    scores = pd.qcut(ranks, 5, labels=[1, 2, 3, 4, 5]).astype(int)
    return 6 - scores if reverse else scores

rfm["R_Score"] = quantile_score(rfm["Recency"], reverse=True)
rfm["F_Score"] = quantile_score(rfm["Frequency"])
rfm["M_Score"] = quantile_score(rfm["Monetary"])

rfm["RFM_Score"] = (
    rfm["R_Score"].astype(str)
    + rfm["F_Score"].astype(str)
    + rfm["M_Score"].astype(str)
)

def assign_segment(row):
    r, f, m = row["R_Score"], row["F_Score"], row["M_Score"]

    if r >= 4 and f >= 4 and m >= 4:
        return "Champions"
    if r >= 3 and f >= 4:
        return "Loyal Customers"
    if r >= 4 and f >= 2:
        return "Potential Loyalists"
    if r <= 2 and f >= 3:
        return "At Risk"
    if r <= 2 and f <= 2:
        return "Hibernating"
    if f == 1 and r >= 3:
        return "Recent Customers"
    return "Needs Attention"

rfm["Segment"] = rfm.apply(assign_segment, axis=1)
rfm = rfm.sort_values(["Monetary", "Frequency"], ascending=False)

rfm.to_csv(OUT / "customer_rfm_segments.csv", index=False)

segment_summary = (
    rfm.groupby("Segment")
    .agg(
        Customers=("CustomerID", "nunique"),
        Revenue=("Monetary", "sum"),
        Average_Recency_Days=("Recency", "mean"),
        Average_Invoices=("Frequency", "mean"),
        Average_Customer_Revenue=("Monetary", "mean"),
    )
    .reset_index()
)

segment_summary["Revenue"] = segment_summary["Revenue"].round(2)
segment_summary["Average_Recency_Days"] = segment_summary["Average_Recency_Days"].round(1)
segment_summary["Average_Invoices"] = segment_summary["Average_Invoices"].round(2)
segment_summary["Average_Customer_Revenue"] = segment_summary["Average_Customer_Revenue"].round(2)
segment_summary.to_csv(OUT / "segment_summary.csv", index=False)

report = {
    "reference_date": str(reference_date.date()),
    "customers_segmented": int(rfm["CustomerID"].nunique()),
    "total_customer_revenue": round(float(rfm["Monetary"].sum()), 2),
    "segments": int(rfm["Segment"].nunique()),
    "segment_customer_counts": {
        str(row["Segment"]): int(row["Customers"])
        for _, row in segment_summary.iterrows()
    },
}

with open(REPORTS / "rfm_summary.json", "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2)

print("\nRFM SEGMENTATION COMPLETE")
print(f"Reference date: {reference_date.date()}")
print(f"Customers segmented: {report['customers_segmented']:,}")
print(f"Total customer revenue: £{report['total_customer_revenue']:,.2f}")
print("\nCUSTOMER SEGMENT SUMMARY")
print(segment_summary.to_string(index=False))
print("\nSaved: data/processed/customer_rfm_segments.csv")
print("Saved: data/processed/segment_summary.csv")
print("Saved: reports/rfm_summary.json")
