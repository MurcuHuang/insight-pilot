# Table Notes (数据表说明)

Warehouse table semantics, grains, and join keys. The text-to-SQL layer relies on these notes.

## orders

One row per order. Key columns: `order_id`, `customer_id`, `order_status` (delivered / shipped / processing / canceled), and the timestamp lifecycle: `order_purchase_timestamp` → `order_approved_at` → `order_delivered_carrier_date` → `order_delivered_customer_date`, plus the promise date `order_estimated_delivery_date`.
Caveat: non-delivered orders have NULL delivery dates — filter `order_status = 'delivered'` before computing delivery metrics.

## customers

One row per **order's** `customer_id` (an Olist quirk: customer_id is per-order, not per-person). The person is identified by `customer_unique_id`. Location: `customer_city`, `customer_state` (two-letter Brazilian state code, e.g. SP, RJ).
Join: `orders.customer_id = customers.customer_id`. For any person-level analysis (repeat purchase, active customers), aggregate by `customer_unique_id`.

## order_items

Grain: one row per item within an order (`order_id` + `order_item_id`). `price` is the item price excluding freight; `freight_value` is the freight charged for that item. Links to `product_id` and `seller_id`.
Caveat: a multi-item order has multiple rows — joining orders to order_items multiplies rows; use aggregation or DISTINCT order counts deliberately.

## products

One row per product: `product_id`, `product_category_name`, `product_weight_g`, `product_photos_qty`.

## order_payments

One or more rows per order (`payment_sequential`). `payment_type` ∈ credit_card / boleto / voucher / debit_card; `payment_installments`; `payment_value`. Sum `payment_value` over rows for an order's paid total.

## order_reviews

About one review per delivered order: `review_score` (1–5), optional `review_comment_title` / `review_comment_message`, `review_creation_date`.

## sellers

One row per seller: `seller_id`, `seller_city`, `seller_state`.

## Join map

`orders.customer_id → customers.customer_id`; `order_items.order_id → orders.order_id`; `order_items.product_id → products.product_id`; `order_items.seller_id → sellers.seller_id`; `order_payments.order_id → orders.order_id`; `order_reviews.order_id → orders.order_id`.
