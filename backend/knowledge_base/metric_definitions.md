# InsightOS Metric Definitions

## Revenue
Sum of order_items.price for orders where order_status = 'delivered'.
Freight/shipping charges are tracked separately and excluded.

## Order Volume
Count of distinct order_id values, filtered by the requested status
(default: all statuses unless "completed orders" is specified).

## Average Order Value (AOV)
Total Revenue divided by Order Volume, calculated over delivered orders only.

## Return Rate (proxy)
Olist has no explicit returns field. Defined as: orders with a review_score
of 2 or less, divided by total delivered orders in the same period.
This is a deliberate proxy/assumption, not a true return metric.

## Active Seller
A seller with at least 1 order placed in the last 90 days relative to the
query date.

## Delivery Time
Days between order_purchase_timestamp and order_delivered_customer_date,
delivered orders only.

## Late Delivery Rate
Percentage of delivered orders where order_delivered_customer_date exceeds
order_estimated_delivery_date.

## Top Category
Product category (via product_category_translation) ranked by total
Revenue for the requested time period.

## Customer Region
Derived from customer_state in the customers table (Brazilian state codes).

## Payment Type Breakdown
Distribution of order_payments.payment_type (credit_card, boleto,
voucher, debit_card) as a share of total transactions.
