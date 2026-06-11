"""Load raw CSVs (synthetic or real Kaggle Olist) into the DuckDB warehouse."""
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
DB = ROOT / "data" / "warehouse.duckdb"

TABLES = {
    "customers": "olist_customers_dataset.csv",
    "orders": "olist_orders_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "products": "olist_products_dataset.csv",
    "order_payments": "olist_order_payments_dataset.csv",
    "order_reviews": "olist_order_reviews_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
}


def main():
    con = duckdb.connect(str(DB))
    for table, fname in TABLES.items():
        path = RAW / fname
        if not path.exists():
            print(f"!! missing {fname} — run scripts/generate_synthetic_data.py or see data/README.md")
            continue
        con.execute(f"CREATE OR REPLACE TABLE {table} AS SELECT * FROM read_csv_auto(?)", [str(path)])
        n = con.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
        print(f"{table:<16} {n:>8,} rows")
    con.close()
    print(f"\nWarehouse ready: {DB}")


if __name__ == "__main__":
    main()
