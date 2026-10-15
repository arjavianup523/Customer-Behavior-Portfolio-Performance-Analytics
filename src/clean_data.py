from pathlib import Path
import pandas as pd
import json

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw" / "Online Retail.xlsx"
OUT = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"

OUT.mkdir(parents=True, exist_ok=True)
REPORTS.mkdir(parents=True, exist_ok=True)

df = pd.read_excel(RAW)
rows_loaded = len(df)

# Standardize column names and remove exact duplicate rows.
df.columns = df.columns.str.strip()
duplicates = int(df.duplicated().sum())
df = df.drop_duplicates().copy()

# Convert fields to their intended types.
df["InvoiceNo"] = df["InvoiceNo"].astype(str).str.strip()
df["CustomerID"] = df["CustomerID"].astype("string").str.strip()
df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], errors="coerce")
df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce")
df["UnitPrice"] = pd.to_numeric(df["UnitPrice"], errors="coerce")

# Identify cancelled invoices; these typically begin with C.
cancelled_mask = df["InvoiceNo"].str.upper().str.startswith("C", na=False)
cancelled_invoices = int(cancelled_mask.sum())

# Exclude cancellations, invalid dates, missing customer IDs,
# non-positive quantities and non-positive prices from sales analysis.
valid_mask = (
    ~cancelled_mask
    & df["CustomerID"].notna()
    & df["CustomerID"].ne("")
    & df["InvoiceDate"].notna()
    & df["Quantity"].gt(0)
    & df["UnitPrice"].gt(0)
)

sales = df.loc[valid_mask].copy()
sales["Revenue"] = (sales["Quantity"] * sales["UnitPrice"]).round(2)

# Save a clean transaction dataset.
sales.to_csv(OUT / "clean_transactions.csv", index=False)

# Produce a data-quality summary.
quality_report = {
    "source_rows": int(rows_loaded),
    "duplicate_rows_removed": duplicates,
    "cancelled_invoice_rows_identified": cancelled_invoices,
    "rows_after_deduplication": int(len(df)),
    "clean_sales_rows": int(len(sales)),
    "rows_excluded_from_sales_analysis": int(len(df) - len(sales)),
    "unique_customers": int(sales["CustomerID"].nunique()),
    "unique_invoices": int(sales["InvoiceNo"].nunique()),
    "total_revenue": round(float(sales["Revenue"].sum()), 2),
    "date_min": str(sales["InvoiceDate"].min()),
    "date_max": str(sales["InvoiceDate"].max()),
    "missing_values_in_clean_data": {
        str(k): int(v)
        for k, v in sales.isna().sum().items()
        if v > 0
    },
}

with open(REPORTS / "data_quality_report.json", "w", encoding="utf-8") as f:
    json.dump(quality_report, f, indent=2)

print("\nDATA CLEANING COMPLETE")
for key, value in quality_report.items():
    print(f"{key}: {value}")

print("\nSaved: data/processed/clean_transactions.csv")
print("Saved: reports/data_quality_report.json")
