from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed"


def test_clean_transactions_exist_and_have_required_columns():
    path = DATA / "clean_transactions.csv"
    assert path.exists(), "Clean transaction file is missing"

    df = pd.read_csv(path, nrows=10)
    required = {
        "InvoiceNo", "StockCode", "Quantity",
        "InvoiceDate", "UnitPrice", "CustomerID", "Revenue"
    }
    assert required.issubset(df.columns)


def test_clean_sales_have_valid_values():
    df = pd.read_csv(DATA / "clean_transactions.csv")

    assert not df.empty
    assert df["CustomerID"].notna().all()
    assert (df["Quantity"] > 0).all()
    assert (df["UnitPrice"] > 0).all()
    assert (df["Revenue"] >= 0).all()


def test_revenue_calculation():
    df = pd.read_csv(
        DATA / "clean_transactions.csv",
        usecols=["Quantity", "UnitPrice", "Revenue"]
    )
    expected = (df["Quantity"] * df["UnitPrice"]).round(2)
    actual = df["Revenue"].round(2)

    assert (expected == actual).all()


def test_rfm_customer_ids_are_unique():
    df = pd.read_csv(DATA / "customer_rfm_segments.csv")

    assert not df.empty
    assert df["CustomerID"].is_unique
    assert df["Segment"].notna().all()
    assert (df["Recency"] >= 0).all()
    assert (df["Frequency"] >= 1).all()


def test_monthly_performance_files_exist():
    path = DATA / "monthly_performance.csv"
    assert path.exists()

    df = pd.read_csv(path)
    assert len(df) > 0
    assert {"Month", "Revenue", "Orders", "Customers"}.issubset(df.columns)
    assert (df["Revenue"] >= 0).all()


def test_cohort_retention_file_exists():
    path = DATA / "cohort_retention.csv"
    assert path.exists()

    df = pd.read_csv(path, index_col=0)
    assert not df.empty
