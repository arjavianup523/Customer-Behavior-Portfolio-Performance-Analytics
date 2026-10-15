# Customer Behavior & Portfolio Performance Analytics

An end-to-end retail analytics project using the UCI Online Retail dataset. The project transforms raw transactions into customer-level insights and an interactive executive dashboard.

## Business objectives

- Measure revenue, order volume, average order value, and customer activity.
- Segment customers using Recency, Frequency, and Monetary (RFM) analysis.
- Analyze customer retention through monthly cohorts.
- Identify repeat-purchase behavior and top-performing products.
- Present results in an interactive Streamlit dashboard.

## Technology stack

Python, Pandas, NumPy, Plotly, Streamlit, pytest, Git, and GitHub.

## Dataset

The project uses the UCI Online Retail dataset, covering transactions from December 2010 to December 2011.

Source: https://archive.ics.uci.edu/dataset/352/online+retail

## Data pipeline

1. Load and clean raw retail transactions.
2. Remove exact duplicate rows.
3. Exclude cancelled invoices and invalid rows from sales analysis.
4. Calculate revenue as quantity multiplied by unit price.
5. Generate customer RFM scores and segments.
6. Calculate monthly cohort retention and repeat-purchase metrics.
7. Explore results through an interactive dashboard.

## Repository structure

```text
.
├── dashboard/
│   └── app.py
├── data/
│   ├── raw/
│   └── processed/
├── reports/
├── src/
│   ├── clean_data.py
│   ├── customer_segmentation.py
│   └── retention_analysis.py
├── tests/
│   └── test_analytics.py
├── requirements.txt
└── README.md
```

## Initial dataset results

Results from the cleaning pipeline:

- Source rows: 541,909
- Exact duplicate rows removed: 5,268
- Clean sales rows: 392,692
- Identified customers: 4,338
- Distinct sales invoices: 18,532
- Calculated revenue: £8,887,208.89
- Automated tests: 6 passed

These metrics describe the full cleaned dataset, not necessarily a filtered dashboard view.

## Run locally

Create and activate a virtual environment, then install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Run the pipeline in order:

```powershell
python .\src\clean_data.py
python .\src\customer_segmentation.py
python .\src\retention_analysis.py
```

Launch the dashboard:

```powershell
python -m streamlit run .\dashboard\app.py
```

Run automated tests:

```powershell
python -m pytest .\tests\test_analytics.py -v
```

## Methodology notes

- Revenue is calculated from transaction quantity and unit price.
- Cancelled invoices, missing customer IDs, non-positive quantities, non-positive prices, and invalid dates are excluded from the clean sales dataset.
- RFM segments are rule-based groups derived from customer recency, invoice frequency, and monetary value.
- Customer-level results depend on the available customer IDs in the source data.
- This project is analytical and educational; its findings should be validated before making real business decisions.

## Future improvements

- Add more data-quality and metric-validation tests.
- Add a reproducible database/SQL analytics layer.
- Deploy the dashboard publicly.
- Add screenshots and documented business recommendations after final verification.
