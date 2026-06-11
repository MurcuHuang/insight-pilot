"""Generate a realistic Olist-style synthetic e-commerce dataset (7 CSVs in data/raw/).

Built-in signals so demo questions have real answers:
- Nov/Dec seasonality + ~25% YoY growth (2024 -> 2025)
- ~13% late deliveries; late delivery strongly lowers review scores
- customer_id is per-order (Olist quirk); customer_unique_id identifies the person,
  so repeat-purchase analyses must use customer_unique_id (documented in docs/).
"""
import uuid
from pathlib import Path

import numpy as np
import pandas as pd

rng = np.random.default_rng(42)
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)

N_ORDERS, N_PERSONS, N_PRODUCTS, N_SELLERS = 18_000, 32_000, 600, 180

STATES = ["SP", "RJ", "MG", "RS", "PR", "SC", "BA", "DF", "GO", "ES", "PE", "CE"]
STATE_W = [0.42, 0.13, 0.12, 0.05, 0.05, 0.04, 0.04, 0.03, 0.03, 0.03, 0.03, 0.03]
CITY = {"SP": "sao paulo", "RJ": "rio de janeiro", "MG": "belo horizonte",
        "RS": "porto alegre", "PR": "curitiba", "SC": "florianopolis",
        "BA": "salvador", "DF": "brasilia", "GO": "goiania", "ES": "vitoria",
        "PE": "recife", "CE": "fortaleza"}

CATEGORIES = {  # category -> (min_price, max_price)
    "electronics": (80, 900), "computers_accessories": (30, 500),
    "home_decor": (20, 250), "furniture": (100, 1200), "sports_leisure": (25, 400),
    "health_beauty": (15, 200), "toys": (20, 300), "fashion_apparel": (25, 350),
    "watches_gifts": (50, 800), "pet_supplies": (15, 180),
    "office_supplies": (10, 150), "kitchen_dining": (20, 350),
}


def uid(n):
    return [uuid.uuid4().hex for _ in range(n)]


# ---------------- products & sellers ----------------
cat_names = list(CATEGORIES)
prod_cat = rng.choice(cat_names, size=N_PRODUCTS)
prod_base_price = np.array([rng.uniform(*CATEGORIES[c]) for c in prod_cat])
products = pd.DataFrame({
    "product_id": uid(N_PRODUCTS),
    "product_category_name": prod_cat,
    "product_weight_g": rng.integers(100, 8000, N_PRODUCTS),
    "product_photos_qty": rng.integers(1, 7, N_PRODUCTS),
})

seller_state = rng.choice(STATES, p=STATE_W, size=N_SELLERS)
sellers = pd.DataFrame({
    "seller_id": uid(N_SELLERS),
    "seller_zip_code_prefix": rng.integers(1000, 99999, N_SELLERS),
    "seller_city": [CITY[s] for s in seller_state],
    "seller_state": seller_state,
})

# ---------------- persons (repeat-purchase structure) ----------------
person_ids = uid(N_PERSONS)
person_state = rng.choice(STATES, p=STATE_W, size=N_PERSONS)
w = rng.pareto(2.5, N_PERSONS) + 1.0  # heavy tail -> some loyal repeat buyers
person_idx = rng.choice(N_PERSONS, size=N_ORDERS, p=w / w.sum())

# ---------------- order timestamps (seasonality + growth) ----------------
months = [(y, m) for y in (2024, 2025) for m in range(1, 13)]
season = np.array([0.8, 0.8, 0.9, 0.9, 1.0, 1.0, 1.0, 1.1, 1.0, 1.1, 1.5, 1.4])
mw = np.concatenate([season, season * 1.25])
midx = rng.choice(len(months), size=N_ORDERS, p=mw / mw.sum())
purchase = (
    pd.to_datetime([f"{months[i][0]}-{months[i][1]:02d}-01" for i in midx])
    + pd.to_timedelta(rng.integers(0, 28, N_ORDERS), unit="D")
    + pd.to_timedelta(rng.integers(0, 86400, N_ORDERS), unit="s")
)

status = rng.choice(["delivered", "shipped", "canceled", "processing"],
                    p=[0.94, 0.03, 0.02, 0.01], size=N_ORDERS)
est_days = rng.integers(10, 31, N_ORDERS)
late = rng.random(N_ORDERS) < 0.13
actual_days = np.where(late, est_days + rng.integers(1, 15, N_ORDERS),
                       np.maximum(3, est_days - rng.integers(1, 10, N_ORDERS)))

approved = purchase + pd.to_timedelta(rng.integers(30, 720, N_ORDERS), unit="m")
carrier = purchase + pd.to_timedelta(rng.integers(2, 6, N_ORDERS), unit="D")
delivered = purchase + pd.to_timedelta(actual_days, unit="D")
estimated = purchase + pd.to_timedelta(est_days, unit="D")

is_delivered = status == "delivered"
orders = pd.DataFrame({
    "order_id": uid(N_ORDERS),
    "customer_id": uid(N_ORDERS),  # per-order, the Olist quirk
    "order_status": status,
    "order_purchase_timestamp": purchase,
    "order_approved_at": approved,
    "order_delivered_carrier_date": pd.Series(carrier).where(np.isin(status, ["delivered", "shipped"])),
    "order_delivered_customer_date": pd.Series(delivered).where(is_delivered),
    "order_estimated_delivery_date": estimated,
})

customers = pd.DataFrame({
    "customer_id": orders["customer_id"],
    "customer_unique_id": [person_ids[i] for i in person_idx],
    "customer_zip_code_prefix": rng.integers(1000, 99999, N_ORDERS),
    "customer_city": [CITY[person_state[i]] for i in person_idx],
    "customer_state": [person_state[i] for i in person_idx],
})

# ---------------- order items ----------------
n_items = rng.choice([1, 2, 3], p=[0.78, 0.16, 0.06], size=N_ORDERS)
rep = np.repeat(np.arange(N_ORDERS), n_items)
pidx = rng.integers(0, N_PRODUCTS, len(rep))
price = (prod_base_price[pidx] * rng.uniform(0.9, 1.15, len(rep))).round(2)
freight = (8 + 0.04 * price + rng.uniform(0, 7, len(rep))).round(2)
items = pd.DataFrame({
    "order_id": orders["order_id"].to_numpy()[rep],
    "product_id": products["product_id"].to_numpy()[pidx],
    "seller_id": sellers["seller_id"].to_numpy()[rng.integers(0, N_SELLERS, len(rep))],
    "shipping_limit_date": purchase[rep] + pd.Timedelta(days=3),
    "price": price,
    "freight_value": freight,
})
items.insert(1, "order_item_id", items.groupby("order_id").cumcount() + 1)

# ---------------- payments ----------------
totals = items.groupby("order_id", sort=False)[["price", "freight_value"]].sum().sum(axis=1)
ptype = rng.choice(["credit_card", "boleto", "voucher", "debit_card"],
                   p=[0.74, 0.18, 0.04, 0.04], size=N_ORDERS)
installments = np.where(
    ptype == "credit_card",
    rng.choice([1, 2, 3, 4, 5, 6, 8, 10], p=[0.35, 0.15, 0.12, 0.10, 0.10, 0.08, 0.06, 0.04], size=N_ORDERS),
    1,
)
payments = pd.DataFrame({
    "order_id": orders["order_id"],
    "payment_sequential": 1,
    "payment_type": ptype,
    "payment_installments": installments,
    "payment_value": orders["order_id"].map(totals).round(2),
})

# ---------------- reviews (delivered orders only; late -> unhappy) ----------------
rev_mask = is_delivered & (rng.random(N_ORDERS) < 0.95)
low = rng.choice([1, 2, 3], p=[0.45, 0.35, 0.20], size=N_ORDERS)
high = rng.choice([2, 3, 4, 5], p=[0.02, 0.08, 0.25, 0.65], size=N_ORDERS)
score = np.where(late, low, high)

BAD = ["Arrived very late, disappointed.", "Package delayed and no tracking updates.",
       "Slow delivery, product was okay though."]
GOOD = ["Great product, fast delivery!", "Exactly as described.",
        "Good value for money.", "Five stars, would buy again."]
has_msg = rng.random(N_ORDERS) < 0.4
msgs = np.where(score <= 3, rng.choice(BAD, N_ORDERS), rng.choice(GOOD, N_ORDERS))
reviews = pd.DataFrame({
    "review_id": uid(N_ORDERS),
    "order_id": orders["order_id"],
    "review_score": score,
    "review_comment_title": "",
    "review_comment_message": np.where(has_msg, msgs, ""),
    "review_creation_date": delivered + pd.to_timedelta(rng.integers(1, 6, N_ORDERS), unit="D"),
    "review_answer_timestamp": delivered + pd.to_timedelta(rng.integers(2, 9, N_ORDERS), unit="D"),
})[rev_mask].reset_index(drop=True)

# ---------------- write ----------------
FILES = {
    "olist_customers_dataset.csv": customers,
    "olist_orders_dataset.csv": orders,
    "olist_order_items_dataset.csv": items,
    "olist_products_dataset.csv": products,
    "olist_order_payments_dataset.csv": payments,
    "olist_order_reviews_dataset.csv": reviews,
    "olist_sellers_dataset.csv": sellers,
}
for name, df in FILES.items():
    df.to_csv(RAW / name, index=False, date_format="%Y-%m-%d %H:%M:%S")
    print(f"{name:<38} {len(df):>7,} rows")

# sanity summary (also validates the built-in signals)
counts = np.bincount(person_idx, minlength=N_PERSONS)
active = counts[counts > 0]
gmv = float((items["price"] + items["freight_value"]).sum())
rev_late = late[rev_mask.to_numpy() if hasattr(rev_mask, "to_numpy") else rev_mask]
print(f"\nGMV (all orders): ${gmv:,.0f}")
print(f"Repeat purchase rate: {(active >= 2).mean():.1%}")
print(f"Late delivery rate: {late[is_delivered].mean():.1%}")
print(f"Avg review score — on-time: {score[rev_mask & ~late].mean():.2f}, late: {score[rev_mask & late].mean():.2f}")
