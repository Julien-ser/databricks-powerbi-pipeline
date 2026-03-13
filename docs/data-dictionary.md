# Data Dictionary

This document describes the e-commerce data model used throughout the pipeline, from raw source data to final gold layer aggregates.

## Table of Contents

- [Overview](#overview)
- [Source Data](#source-data)
- [Bronze Layer](#bronze-layer)
- [Silver Layer](#silver-layer)
- [Gold Layer](#gold-layer)
- [Data Lineage](#data-lineage)
- [Data Quality Rules](#data-quality-rules)

---

## Overview

The pipeline implements a **medallion architecture** with three layers:

1. **Bronze** (raw): Direct ingestion from source systems, stored as Delta Lake tables
2. **Silver** (cleansed): Validated, cleaned, and standardized data
3. **Gold** (business aggregates): Denormalized tables optimized for Power BI reporting

### Schema Naming

- **Database**: `{catalog}.{schema}` (configurable via `parameters.json`)
- **Bronze tables**: `bronze_*`
- **Silver tables**: `silver_*`
- **Gold tables**: `dim_*` (dimensions), `fact_*` (facts), `*_monthly` (aggregates)

---

## Source Data

### Source Files

The sample data consists of four CSV files:

| File | Description | Row Count (sample) | Primary Key |
|------|-------------|-------------------|-------------|
| `sample_customers.csv` | Customer master data | 100 | `customer_id` |
| `sample_products.csv` | Product catalog | 50 | `product_id` |
| `sample_orders.csv` | Order headers | 500 | `order_id` |
| `sample_order_items.csv` | Order line items | ~1,500 | (`order_id`, `product_id`) |

### Source Data Schemas

#### customers

| Column | Type | Description | Business Rule |
|--------|------|-------------|---------------|
| `customer_id` | STRING | Unique customer identifier | Format: `CUST0000` |
| `first_name` | STRING | Customer first name | Required, non-empty |
| `last_name` | STRING | Customer last name | Required, non-empty |
| `email` | STRING | Email address | Valid email format |
| `city` | STRING | City name | Required |
| `state` | STRING | State/province code | 2-letter format |
| `signup_date` | DATE | Date customer registered | Not future-dated |
| `customer_segment` | STRING | Customer tier | One of: `Premium`, `Standard`, `Basic` |

#### products

| Column | Type | Description | Business Rule |
|--------|------|-------------|---------------|
| `product_id` | STRING | Unique product identifier | Format: `PROD0000` |
| `product_name` | STRING | Product display name | Required |
| `category` | STRING | Product category | One of 6 categories |
| `price` | DECIMAL(10,2) | List price | ≥ 0 |
| `cost` | DECIMAL(10,2) | Unit cost | ≥ 0, ≤ price |
| `inventory_quantity` | INTEGER | Current stock level | ≥ 0 |

#### orders

| Column | Type | Description | Business Rule |
|--------|------|-------------|---------------|
| `order_id` | STRING | Unique order identifier | Format: `ORDER000000` |
| `customer_id` | STRING | FK to customer | Must exist in customers |
| `order_date` | TIMESTAMP | Order placement datetime | Not in future |
| `status` | STRING | Order fulfillment status | `completed`, `shipped`, `processing`, `cancelled`, `returned` |
| `total_amount` | DECIMAL(10,2) | Order total | ≥ 0, matches sum of line items |
| `shipping_address` | STRING | Delivery address | Required |
| `payment_method` | STRING | Payment type | `credit_card`, `paypal`, `debit_card` |

#### order_items

| Column | Type | Description | Business Rule |
|--------|------|-------------|---------------|
| `order_id` | STRING | FK to orders | Must exist in orders |
| `product_id` | STRING | FK to products | Must exist in products |
| `quantity` | INTEGER | Units ordered | 1-10, positive |
| `unit_price` | DECIMAL(10,2) | Price at time of order | Must match product price (snapshot) |
| `line_total` | DECIMAL(10,2) | quantity × unit_price | Calculated |

---

## Bronze Layer

### Purpose

Capture raw source data with minimal transformation, preserving original structure and enabling reprocessing if needed.

### Tables

#### bronze_customers

Direct copy of `sample_customers.csv` with added metadata:

| Column | Type | Description |
|--------|------|-------------|
| All source columns | Same | Copied verbatim |
| `_ingestion_timestamp` | TIMESTAMP | When data was ingested |
| `_source_file` | STRING | Original filename |

#### bronze_products

Copy of `sample_products.csv` + metadata.

#### bronze_orders

Copy of `sample_orders.csv` + metadata.

#### bronze_order_items

Copy of `sample_order_items.csv` + metadata.

### Data Retention

Bronze data is kept indefinitely (or per retention policy) to enable reprocessing and audit.

---

## Silver Layer

### Purpose

Cleanse, validate, and standardize raw data. Apply business rules, handle data quality issues, and establish relationships.

### Tables

#### silver_customers

Cleaned customer data:

| Column | Type | Description | Transformation |
|--------|------|-------------|----------------|
| `customer_id` | STRING | Unique ID (PK) | Trimmed, validated format |
| `first_name` | STRING | Normalized to title case | `title()` |
| `last_name` | STRING | Normalized to title case | `title()` |
| `email` | STRING | Lowercased, validated | `lower()`, regex check |
| `city` | STRING | Cleaned city name | `title()` |
| `state` | STRING | Uppercase state code | `upper()` |
| `signup_date` | DATE | Parsed date | `to_date()` |
| `customer_segment` | STRING | Standardized value | Case normalization |
| `record_created_at` | TIMESTAMP | Audit timestamp | Current timestamp |
| `record_updated_at` | TIMESTAMP | Last update | Current timestamp |

**Business Rules:**
- No duplicate `customer_id`
- Email must contain `@` and `.`
- `signup_date` cannot be in the future

#### silver_products

Cleaned product catalog:

| Column | Type | Description |
|--------|------|-------------|
| `product_id` | STRING | PK |
| `product_name` | STRING | Trimmed |
| `category` | STRING | Normalized |
| `price` | DECIMAL(10,2) | Non-negative |
| `cost` | DECIMAL(10,2) | Non-negative, ≤ price |
| `inventory_quantity` | INTEGER | Non-negative |
| `record_created_at` | TIMESTAMP |
| `record_updated_at` | TIMESTAMP |

#### silver_orders

Cleaned order headers:

| Column | Type | Description |
|--------|------|-------------|
| `order_id` | STRING | PK |
| `customer_id` | STRING | FK → `silver_customers` |
| `order_date` | TIMESTAMP | Parsed timestamp |
| `order_date_key` | INTEGER | Date key for joins (YYYYMMDD) |
| `status` | STRING | Normalized status |
| `total_amount` | DECIMAL(10,2) | Validated amount |
| `shipping_address` | STRING | Cleaned address |
| `payment_method` | STRING | Normalized payment type |
| `record_created_at` | TIMESTAMP |
| `record_updated_at` | TIMESTAMP |

#### silver_order_items

Cleaned line items with price snapshot:

| Column | Type | Description |
|--------|------|-------------|
| `order_id` | STRING | FK → `silver_orders` |
| `product_id` | STRING | FK → `silver_products` |
| `quantity` | INTEGER | 1-10 validated |
| `unit_price` | DECIMAL(10,2) | Snapshot from product price |
| `line_total` | DECIMAL(10,2) | Calculated |

---

## Gold Layer

### Purpose

Create business-level aggregates and denormalized structures optimized for Power BI reporting.

### Tables

#### dim_customer

Customer dimension:

| Column | Type | Description | Source |
|--------|------|-------------|--------|
| `customer_key` | INTEGER | Surrogate key (identity) | Auto-increment |
| `customer_id` | STRING | Natural key | silver_customers |
| `first_name` | STRING | |
| `last_name` | STRING | |
| `email` | STRING | |
| `city` | STRING | |
| `state` | STRING | |
| `signup_date` | DATE | |
| `customer_segment` | STRING | |
| `record_created_at` | TIMESTAMP | |
| `record_updated_at` | TIMESTAMP | |

**Indexes:** Z-Order on `customer_key`

#### dim_product

Product dimension:

| Column | Type | Description | Source |
|--------|------|-------------|--------|
| `product_key` | INTEGER | Surrogate key | Auto-increment |
| `product_id` | STRING | Natural key | silver_products |
| `product_name` | STRING | |
| `category` | STRING | |
| `price` | DECIMAL(10,2) | Current price |
| `cost` | DECIMAL(10,2) | Current cost |
| `inventory_quantity` | INTEGER | Current stock |
| `record_created_at` | TIMESTAMP | |
| `record_updated_at` | TIMESTAMP | |

**Indexes:** Z-Order on `product_key`, `category`

#### fact_sales

Transactional fact table (star schema):

| Column | Type | Description | Source |
|--------|------|-------------|--------|
| `order_line_key` | INTEGER | Surrogate key | Auto-increment |
| `order_id` | STRING | Order identifier | silver_order_items |
| `customer_key` | INTEGER | FK → dim_customer | Lookup from customer_id |
| `product_key` | INTEGER | FK → dim_product | Lookup from product_id |
| `order_date` | DATE | Order date (derived) | From order_date |
| `order_datetime` | TIMESTAMP | Full timestamp | From order_date |
| `quantity` | INTEGER | Units sold | silver_order_items |
| `unit_price` | DECIMAL(10,2) | Price at sale | silver_order_items |
| `line_total` | DECIMAL(10,2) | quantity × unit_price | Calculated |
| `status` | STRING | Order status | silver_orders |
| `payment_method` | STRING | | silver_orders |

**Partitioning**: By `order_date` (optional for large tables)

**Indexes**: Z-Order on `customer_key`, `product_key`, `order_date`

**Foreign Keys** (enforced by Power BI, not Delta):
- `customer_key` → `dim_customer.customer_key`
- `product_key` → `dim_product.product_key`

#### monthly_sales

Pre-aggregated monthly sales for faster trend queries:

| Column | Type | Description | Calculation |
|--------|------|-------------|-------------|
| `year_month` | INTEGER | Period key (YYYYMM) | Format: 202503 |
| `year` | INTEGER | Calendar year | From order_date |
| `month` | INTEGER | Calendar month | From order_date |
| `total_sales` | DECIMAL(12,2) | Sum of line_total | SUM(line_total) |
| `total_orders` | INTEGER | Distinct order count | COUNT(DISTINCT order_id) |
| `total_quantity` | INTEGER | Units sold | SUM(quantity) |
| `avg_order_value` | DECIMAL(10,2) | Avg order revenue | total_sales / total_orders |
| `avg_unit_price` | DECIMAL(10,2) | Average price | AVG(unit_price) |
| `top_category` | STRING | Best-selling category | Mode of product.category |
| `record_updated_at` | TIMESTAMP | Refresh timestamp | Current time |

**Aggregation Logic:**
```sql
SELECT
  DATE_FORMAT(order_date, 'yyyyMM') as year_month,
  YEAR(order_date) as year,
  MONTH(order_date) as month,
  SUM(line_total) as total_sales,
  COUNT(DISTINCT order_id) as total_orders,
  SUM(quantity) as total_quantity,
  SUM(line_total) / COUNT(DISTINCT order_id) as avg_order_value,
  AVG(unit_price) as avg_unit_price,
  -- Top category requires more complex aggregation
  MAX(category) as top_category
FROM fact_sales
JOIN dim_product USING (product_key)
GROUP BY year, month, order_date
```

---

## Data Lineage

```
Source CSV (data/)
    ↓
[Bronze Layer]
bronze_customers
bronze_products
bronze_orders
bronze_order_items
    ↓
[Silver Layer]
silver_customers ← cleansed from bronze_customers
silver_products  ← cleansed from bronze_products
silver_orders    ← cleansed from bronze_orders, with FK checks
silver_order_items ← cleansed from bronze_order_items
    ↓
[Gold Layer]
dim_customer    ← SCD Type 1 from silver_customers
dim_product     ← SCD Type 1 from silver_products
fact_sales      ← Denormalized from silver_orders + silver_order_items + dimension lookups
monthly_sales   ←Aggregated from fact_sales + dim_product
```

### Transformation Rules

**Silver from Bronze:**
- Drop `_source_file` column, keep `_ingestion_timestamp` as `record_created_at`
- Apply type conversions (strings to dates/timestamps)
- Trim whitespace from string columns
- Validate ranges and foreign keys

**Gold from Silver:**
- Look up dimension surrogate keys via `customer_id` / `product_id`
- Generate `order_date_key` and `year_month` for time-based partitioning
- Calculate `line_total` from quantity × unit_price
- Build monthly aggregates via GROUP BY

---

## Data Quality Rules

### Bronze Layer

| Rule | Check | Action on Failure |
|------|-------|-------------------|
| File exists | Pre-ingestion | Abort with error |
| Row count > 0 | Post-ingestion | Log warning, continue |
| Schema matches | Schema validation | Raise exception |

### Silver Layer

| Rule | Check | Threshold | Action |
|------|-------|-----------|--------|
| No duplicate PK | COUNT(DISTINCT pk) = COUNT(*) | 0 duplicates | Deduplicate or error |
| No NULL in required fields | COUNT(NULL column) | 0 | Replace or drop |
| Foreign key integrity | Matched FK ratio | 100% | Fail if orphaned rows |
| Date validity | Dates between 2000-01-01 and today | 100% | Set to NULL or default |

### Gold Layer

| Rule | Check | Threshold |
|------|-------|-----------|
| Fact table row count matches source | `COUNT(fact) = COUNT(order_items)` | 100% |
| Dimension FK completeness | All fact FKs resolve to dimension | 100% |
| Surrogate key uniqueness | `COUNT(DISTINCT key) = COUNT(*)` | 100% |
| Aggregate accuracy | Spot-check sums against source | Within 0.1% rounding |

### Data Quality Implementation

Add to notebooks:

```sql
-- Example: Check row count after transformation
INSERT INTO data_quality_audit
SELECT 'silver_customers', CURRENT_TIMESTAMP, COUNT(*), 'ROW_COUNT'
FROM silver_customers;

-- Example: Foreign key check
SELECT COUNT(*) as orphan_count
FROM silver_orders o
LEFT JOIN silver_customers c ON o.customer_id = c.customer_id
WHERE c.customer_id IS NULL;
```

---

## Table Sizes (Sample Data)

Estimated sizes for 100 customers, 50 products, 500 orders:

| Table | Rows | Approx. Size (Delta) |
|-------|------|---------------------|
| bronze_customers | 100 | ~10 KB |
| bronze_products | 50 | ~5 KB |
| bronze_orders | 500 | ~100 KB |
| bronze_order_items | ~1,500 | ~150 KB |
| silver_customers | 100 | ~10 KB |
| silver_products | 50 | ~5 KB |
| silver_orders | 500 | ~100 KB |
| silver_order_items | ~1,500 | ~150 KB |
| dim_customer | 100 | ~10 KB |
| dim_product | 50 | ~5 KB |
| fact_sales | ~1,500 | ~200 KB |
| monthly_sales | 12-36 | ~5 KB |

**Production scaling**: These tables will grow linearly with transaction volume. Partition large tables (fact_sales) by order_date for query performance.

---

## Schema Evolution

### Adding New Columns

1. Add column to bronze ingestion notebook (if source data has it)
2. Propagate through silver transformation (clean/validate)
3. Add to gold layer if needed for reporting
4. Update `parameters.json` schema version if breaking changes

### Handling Schema Changes

Delta Lake supports schema evolution:

```sql
-- Bronze ingestion with schema merge
INSERT INTO bronze_orders
SELECT * FROM source_data
WITH SCHEMA EVOLUTION;  -- Auto-add new columns
```

For breaking changes (renaming, type changes), use explicit ALTER TABLE:

```sql
ALTER TABLE silver_orders
ADD COLUMN new_column STRING;

-- Or change type (if compatible)
ALTER TABLE silver_orders
ALTER COLUMN existing_column TYPE STRING;
```

---

## Data Retention & Archiving

**Bronze Layer**: Retain indefinitely (raw data)

**Silver Layer**: Retain indefinitely (cleaned data)

**Gold Layer**: Retain indefinitely (aggregates)

**Log Files**: Rotate monthly, keep 12 months

**Archiving Strategy** (for large datasets):
- Move old partitions to cold storage (e.g., S3 Glacier)
- Use Delta's `ARCHIVE` command (if using Databricks)
- Maintain summarized historical data (e.g., keep 2 years detailed, older aggregated by month)

---

## Glossary

- **Medallion Architecture**: Multi-layer data lake pattern (bronze → silver → gold)
- **Delta Lake**: Open-source storage layer with ACID transactions for data lakes
- **DirectQuery**: Power BI mode that queries data in real-time without import
- **Surrogate Key**: Artificial primary key (integer) used in dimension tables
- **SCD Type 1**: Slowly Changing Dimension - overwrite on change
- **Z-Ordering**: Delta Lake optimization that clusters data by column values for faster queries
- **Data Quality**: Measures of accuracy, completeness, and consistency of data

---

## Next Steps

- Review the [API Reference](api-reference.md) for code-level data handling
- See [Monitoring Guide](monitoring.md) for data quality checks in production
- Consult [Configuration Reference](configuration.md) for table configuration options
