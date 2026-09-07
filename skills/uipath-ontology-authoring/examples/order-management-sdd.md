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

Digitally delivered products (software licences, e-books) carry two further fields on `Product`
itself rather than on a separate class:
- A download URL (text, optional — present only for digitally delivered products)
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
10. A digitally delivered product must have a download URL. Because there is no separate
    `DigitalProduct` class, this is not expressible as a SHACL cardinality on the class and is
    enforced by whatever populates the field.

11. An order is overdue once it has sat in its current status beyond that status's allowance:
    24 hours for `pending`, 72 hours for `confirmed`, 120 hours for `shipped`. Orders in
    `delivered` or `cancelled` are terminal and are never overdue.
12. Loyalty discount by customer tier: `enterprise` 10%, `premium` 5%, `standard` none. The rate
    follows the tier recorded against the customer, not any rate a caller supplies.
13. An order's total amount must equal the sum of its order lines' line totals.
14. Reserving stock for an order reduces each referenced product's stock quantity by the quantity
    ordered on that line. Stock must never fall below zero: if any one line cannot be satisfied in
    full, no stock is reserved for that order at all.
15. A cancellation must leave an audit trail on the order recording when it was cancelled and why.
    `Order` carries no dedicated audit fields, so the trail is appended to the delivery notes.

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

## Actions (write operations)

These are the changes the system should be able to make to order data, each invoked by name. Every
one is a governed operation: the caller names the operation and its parameters, never the tables or
the statement.

### 1. Set order status

**Name:** `setOrderStatus`
**Description:** Moves an order to a status the caller names. Used by ops staff correcting a status
by hand, and by the fulfilment integration as it reports progress.
**Parameters:** `orderNumber` (text, required), `status` (text, required)
**Changes:** the order's status

### 2. Record delivery notes

**Name:** `updateDeliveryNotes`
**Description:** Replaces the delivery notes on an order with text the caller supplies, for instance
a courier instruction taken over the phone.
**Parameters:** `orderNumber` (text, required), `notes` (text, required)
**Changes:** the order's delivery notes

### 3. Recalculate an order total

**Name:** `recalculateOrderTotal`
**Description:** Brings an order's total amount back in line with its order lines, per rule 13. Adds
up the line totals of every line on the order and stores the result. If the stored total already
agrees with the lines, nothing is changed.
**Parameters:** `orderNumber` (text, required)
**Changes:** the order's total amount

### 4. Escalate an overdue order

**Name:** `escalateOverdueOrder`
**Description:** Applies rule 11's per-status allowance to decide whether an order is overdue, and
records an escalation against it. An order inside its allowance, or in a terminal status, is left
alone.
**Parameters:** `orderNumber` (text, required)
**Changes:** the order's delivery notes (there is no dedicated escalation field)

### 5. Reserve stock for an order

**Name:** `reserveStockForOrder`
**Description:** Applies rule 14. Reduces each referenced product's stock by the quantity on that
line, all-or-nothing: if any single line cannot be satisfied in full, nothing is reserved.
**Parameters:** `orderNumber` (text, required)
**Changes:** each referenced product's stock quantity

### 6. Apply a loyalty discount

**Name:** `applyLoyaltyDiscount`
**Description:** Applies rule 12. Reads the customer's tier and reduces the order total by that
tier's rate. A `standard` customer gets no discount and the order is left unchanged.
**Parameters:** `orderNumber` (text, required)
**Changes:** the order's total amount

### 7. Cancel an order

**Name:** `cancelOrder`
**Description:** Cancels an order and records the audit trail rule 15 requires. Terminal orders are
left alone.
**Parameters:** `orderNumber` (text, required), `reason` (text, required)
**Changes:** the order's status, and its delivery notes (which carry the audit trail)

---

## Notes for ontology authoring

- There is no `DigitalProduct` class. Its two fields live on `Product` as optional properties, so a
  digitally delivered product is a `Product` with `downloadUrl` populated.
- The `status` field on `Order` is a controlled vocabulary but modelled as `xsd:string` for now (not a choice set).
- `customerTier` on `Customer` is likewise `xsd:string`.
- Order numbers are system-assigned strings, not auto-incrementing integers.
