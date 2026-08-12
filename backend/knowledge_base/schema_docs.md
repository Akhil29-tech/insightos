# InsightOS Schema Documentation

## customers
- customer_id: unique identifier for a customer's order (note: Olist
  creates a new customer_id per order, not per person)
- customer_unique_id: the true unique person across all their orders
  (use this, not customer_id, when counting distinct customers or
  repeat purchases)
- customer_city, customer_state: customer's location

## orders
- order_id: unique order identifier
- order_status: delivered, shipped, canceled, unavailable, invoiced,
  processing, created, approved
- order_purchase_timestamp: when the order was placed
- order_delivered_customer_date: actual delivery date
- order_estimated_delivery_date: estimated delivery date shown at purchase

## order_items
- order_id, product_id, seller_id: links order to product and seller
- price: item price, excludes freight
- freight_value: shipping cost for that item
- shipping_limit_date: seller's shipping deadline

## order_payments
- payment_type: credit_card, boleto, voucher, debit_card
- payment_installments: number of installments chosen
- payment_value: amount paid

## order_reviews
- review_score: 1-5 customer rating
- review_comment_message: free-text customer feedback
- Note: review_id is not guaranteed unique in this dataset (a small
  number of duplicates exist)

## products
- product_id, product_category_name: links to category translation table
- product_weight_g, dimensions: physical attributes, relevant for
  freight analysis

## product_category_translation
- Maps Portuguese category names to English. Olist is a Brazilian
  dataset, so raw category names are in Portuguese.

## sellers
- seller_id, seller_city, seller_state: seller location, used for
  regional seller analysis

## geolocation
- Zip-code-level lat/long for customers and sellers, supports mapping
  and regional visualizations

## Important schema notes
- order_items has NO quantity column. Each row represents one unit of
  one product. To get total quantity sold, use COUNT(*), not SUM(quantity).
  To get revenue, use SUM(price) directly - never multiply by quantity.
- When displaying category names, use product_category_name_english
  from product_category_translation, not the raw Portuguese
  product_category_name.
