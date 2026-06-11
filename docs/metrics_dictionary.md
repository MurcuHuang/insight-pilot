# Metrics Dictionary (指标口径字典)

Authoritative metric definitions for the e-commerce warehouse. The text-to-SQL layer retrieves these chunks and must follow them exactly — this is how the company keeps numbers consistent across teams.

## GMV — Gross Merchandise Value (商品交易总额)

Definition: total value of goods sold, including freight, excluding canceled orders.
Formula: `SUM(order_items.price + order_items.freight_value)` joined to `orders`, with `order_status <> 'canceled'`.
Time bucketing always uses `orders.order_purchase_timestamp`.
Caveat: GMV includes freight by company convention; "category revenue" does not.

## AOV — Average Order Value (客单价)

Definition: GMV divided by the number of distinct non-canceled orders in the same period.
Formula: `SUM(price + freight_value) / COUNT(DISTINCT order_id)` with `order_status <> 'canceled'`.

## Repeat Purchase Rate (复购率)

Definition: share of customers (people) who placed 2 or more orders, over all customers who placed at least 1 order.
Critical caliber note: `customer_id` is unique **per order**, NOT per person. A person is identified by `customers.customer_unique_id`. Always join `orders.customer_id = customers.customer_id` and aggregate by `customer_unique_id`.
Formula: customers with `COUNT(DISTINCT order_id) >= 2` / all customers, grouped by `customer_unique_id`.
Reference SQL (two-step: aggregate per person first, then compute the rate — do NOT reference a per-customer order count without computing it in a subquery/CTE):

```sql
WITH per_person AS (
  SELECT c.customer_unique_id, count(DISTINCT o.order_id) AS n_orders
  FROM orders o JOIN customers c ON o.customer_id = c.customer_id
  GROUP BY 1
)
SELECT round(avg(CASE WHEN n_orders >= 2 THEN 1.0 ELSE 0.0 END), 4) AS repeat_rate
FROM per_person;
```

## Late Delivery Rate (延迟交付率)

Definition: among delivered orders, the share where the customer received the package after the promised date.
Formula: `order_delivered_customer_date > order_estimated_delivery_date`, filtered to `order_status = 'delivered'`.

## Delivery Days (配送时长)

Definition: days from purchase to customer delivery, for delivered orders only.
Formula: `date_diff('day', order_purchase_timestamp, order_delivered_customer_date)`.

## Average Review Score (平均评分)

Definition: mean of `order_reviews.review_score` (1–5). Reviews exist (mostly) for delivered orders only, so review-based metrics implicitly condition on delivery.

## Category Revenue (品类收入)

Definition: item revenue by product category, **excluding freight** (company convention — note this differs from GMV).
Formula: `SUM(order_items.price)` joined to `products.product_category_name`, `order_status <> 'canceled'`.

## Freight Ratio (运费占比)

Definition: freight as a share of item revenue.
Formula: `SUM(freight_value) / SUM(price)` over `order_items` (non-canceled orders).

## Monthly Active Customers (月活跃客户数)

Definition: distinct people (`customer_unique_id`) with at least one non-canceled order in the calendar month.

## Payment Mix (支付方式构成)

Definition: share of payment value by `payment_type`.
Formula: `SUM(payment_value)` grouped by `payment_type` from `order_payments`. An order can have multiple payment rows (`payment_sequential`); sum them for order totals.
