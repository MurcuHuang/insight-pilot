# Data

By default this project runs on **synthetic Olist-style data** (`python scripts/generate_synthetic_data.py`), so everything works offline with zero setup.

## Using the real Kaggle Olist dataset

1. Download the [Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) (free Kaggle account required).
2. Copy these 7 CSVs into `data/raw/` (same filenames):
   - `olist_customers_dataset.csv`
   - `olist_orders_dataset.csv`
   - `olist_order_items_dataset.csv`
   - `olist_products_dataset.csv`
   - `olist_order_payments_dataset.csv`
   - `olist_order_reviews_dataset.csv`
   - `olist_sellers_dataset.csv`
3. Rerun `python scripts/build_db.py`.

Notes for real data: `product_category_name` is in Portuguese (the dataset ships a `product_category_name_translation.csv` you can join if you want English names), and the eval set's gold answers assume the synthetic data — re-validate gold SQL results after switching.
