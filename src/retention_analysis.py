from pathlib import Path
import pandas as pd
import json

ROOT = Path(__file__).resolve().parent.parent
INPUT = ROOT / "data" / "processed" / "clean_transactions.csv"
OUT = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"

df = pd.read_csv(INPUT, parse_dates=["InvoiceDate"])
df["CustomerID"] = df["CustomerID"].astype(str)

# Monthly customer activity
df["InvoiceMonth"] = df["InvoiceDate"].dt.to_period("M")
df["CohortMonth"] = (
    df.groupby("CustomerID")["InvoiceDate"]
    .transform("min")
    .dt.to_period("M")
)

df["CohortIndex"] = (
    (df["InvoiceMonth"].dt.year - df["CohortMonth"].dt.year) * 12
    + (df["InvoiceMonth"].dt.month - df["CohortMonth"].dt.month)
)

# Count each customer once per active month and cohort.
cohort_data = (
    df.groupby(["CohortMonth", "CohortIndex"])["CustomerID"]
    .nunique()
    .reset_index(name="ActiveCustomers")
)

cohort_sizes = (
    df.groupby("CohortMonth")["CustomerID"]
    .nunique()
    .rename("CohortCustomers")
)

cohort_data = cohort_data.join(
    cohort_sizes, on="CohortMonth"
)
cohort_data["RetentionRate"] = (
    cohort_data["ActiveCustomers"] / cohort_data["CohortCustomers"] * 100
).round(2)

retention = cohort_data.pivot(
    index="CohortMonth",
    columns="CohortIndex",
    values="RetentionRate",
).sort_index()

retention.index = retention.index.astype(str)
retention.columns = [f"Month_{int(c)}" for c in retention.columns]
retention.to_csv(OUT / "cohort_retention.csv")

# Repeat-purchase behavior at customer level
customer_orders = (
    df.groupby("CustomerID")["InvoiceNo"]
    .nunique()
    .rename("InvoiceCount")
    .reset_index()
)
customer_orders["PurchaseType"] = customer_orders["InvoiceCount"].apply(
    lambda n: "Repeat Customer" if n >= 2 else "One-Time Customer"
)

customer_orders.to_csv(OUT / "customer_purchase_frequency.csv", index=False)

repeat_rate = (
    customer_orders["InvoiceCount"].ge(2).mean() * 100
)

# Monthly revenue trend
monthly = (
    df.groupby("InvoiceMonth")
    .agg(
        Revenue=("Revenue", "sum"),
        Orders=("InvoiceNo", "nunique"),
        Customers=("CustomerID", "nunique"),
    )
    .reset_index()
)
monthly["Month"] = monthly["InvoiceMonth"].astype(str)
monthly["Revenue"] = monthly["Revenue"].round(2)
monthly = monthly.drop(columns=["InvoiceMonth"])
monthly.to_csv(OUT / "monthly_performance.csv", index=False)

summary = {
    "repeat_customer_count": int(customer_orders["InvoiceCount"].ge(2).sum()),
    "one_time_customer_count": int(customer_orders["InvoiceCount"].eq(1).sum()),
    "repeat_customer_rate_pct": round(float(repeat_rate), 2),
    "cohort_months": int(cohort_data["CohortMonth"].nunique()),
    "monthly_periods": int(monthly["Month"].nunique()),
    "revenue_total": round(float(monthly["Revenue"].sum()), 2),
}

with open(REPORTS / "retention_summary.json", "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2)

print("\nRETENTION ANALYSIS COMPLETE")
for key, value in summary.items():
    print(f"{key}: {value}")

print("\nMONTHLY PERFORMANCE")
print(monthly.to_string(index=False))
print("\nSaved: data/processed/cohort_retention.csv")
print("Saved: data/processed/customer_purchase_frequency.csv")
print("Saved: data/processed/monthly_performance.csv")
print("Saved: reports/retention_summary.json")
