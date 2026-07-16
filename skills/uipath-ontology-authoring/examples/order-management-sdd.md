# Software Design Document — Order Management Domain

## Purpose

This document describes the core domain model for a simple order management system.
It covers customers, products, orders, and the line items that link them.

---

## Domain Objects

### Customer

Represents a person or business that places orders.

A customer has:
- A full name (text, required)
- An email address (text, required)
- A phone number (text, optional)
- A billing address (text, optional)
- A customer tier: one of `standard`, `premium`, or `enterprise` (text, required)

Each customer can place many orders over time.

### Product

Represents a physical or digital item available for purchase.

A product has:
- A SKU (stock-keeping unit code, text, required, unique identifier)
- A display name (text, required)
- A description (text, optional)
- A unit price in USD (decimal, required, must be greater than or equal to 0)
- A stock quantity (integer, required, must be greater than or equal to 0)
- An active flag indicating whether the product is currently for sale (boolean, required)

A product belongs to exactly one category.

### DigitalProduct

A type of product that is delivered electronically (for example, software licences or e-books).
A digital product additionally has:
- A download URL (URL, required)
- A licence key (text, optional)

### Category

Groups related products together.

A category has:
- A name (text, required)
- A short description (text, optional)

A category can contain many products. Categories do not nest.

### Order

Represents a purchase made by a customer.

An order has:
- An order number (text, required — assigned at creation, e.g., `ORD-2024-0001`)
- An order date (date and time, required)
- A status (text, required) — one of: `pending`, `confirmed`, `shipped`, `delivered`, `cancelled`
- A total amount in USD (decimal, required, must be greater than or equal to 0)
- Optional delivery notes (text, optional)

Each order must be placed by exactly one customer.
Each order must contain at least one order line.

### OrderLine

Represents a single product entry within an order — how many of a given product were ordered, and at what price.

An order line has:
- A quantity (integer, required, must be at least 1)
- A unit price at time of purchase (decimal, required, must be greater than or equal to 0)
- A line total (decimal, required — quantity × unit price, must be greater than or equal to 0)

Each order line belongs to exactly one order.
Each order line refers to exactly one product.

---

## Relationships Summary

| From | Relationship | To | Required |
|---|---|---|---|
| Customer | places | Order | An order must have a customer |
| Order | contains | OrderLine | An order must have at least one line |
| OrderLine | refersTo | Product | A line must point to a product |
| Product | belongsTo | Category | A product must belong to a category |

---

## Business Rules

1. Every order must be linked to a customer.
2. Every order must have at least one order line.
3. Every order line must refer to exactly one product.
4. Every product must belong to exactly one category.
5. Unit price on an order line must be >= 0.
6. Quantity on an order line must be >= 1.
7. Line total on an order line must be >= 0.
8. Product unit price must be >= 0.
9. Product stock quantity must be >= 0.
10. A digital product must have a download URL.

---

## Functions (SPARQL read queries)

These are read-only queries the system should expose. Each becomes a function in `functions.ttl`.

### 1. Count orders by status

**Name:** `countOrdersByStatus`
**Description:** Returns the number of orders that are currently in a given status (e.g. `pending`, `shipped`). Use this to answer "how many orders are in status X". Returns a single count row.
**Parameters:** `status` (text, required)

### 2. List orders for a customer

**Name:** `listOrdersForCustomer`
**Description:** Returns all orders placed by a specific customer, including the order number, order date, total amount, and current status. Use this to answer "what orders does customer X have". Returns one row per order.
**Parameters:** `customerEmail` (text, required)

### 3. Total revenue per category

**Name:** `revenueByCategory`
**Description:** Returns one row per product category with the category name and the total revenue generated from order lines for products in that category. Revenue = sum of line totals. Takes no parameters. Use this to answer "how much revenue did each category generate".
**Parameters:** none

### 4. Low stock products

**Name:** `lowStockProducts`
**Description:** Returns all active products whose stock quantity is below a given threshold. Each row includes the product SKU, display name, and current stock quantity. Use this to answer "which products are running low on stock". Returns one row per matching product.
**Parameters:** `threshold` (integer, required)

### 5. Order line detail for an order

**Name:** `orderLineDetail`
**Description:** Returns all order lines for a given order number, joined to the product name and unit price at time of purchase. Each row includes the product name, quantity ordered, unit price, and line total. Use this to answer "what is in order X". Returns one row per order line.
**Parameters:** `orderNumber` (text, required)

---

## Notes for ontology authoring

- `DigitalProduct` is a subclass of `Product` and inherits all product properties.
- The `status` field on `Order` is a controlled vocabulary but modelled as `xsd:string` for now (not a choice set).
- `customerTier` on `Customer` is likewise `xsd:string`.
- Order numbers are system-assigned strings, not auto-incrementing integers.
