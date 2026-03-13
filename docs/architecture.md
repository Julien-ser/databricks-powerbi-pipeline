# Architecture Design

## Overview

This document describes the architecture of the Databricks Power BI e-commerce analytics pipeline.

### Problem Statement
Organizations need unified analytics on e-commerce data to:
- Track sales performance and trends
- Understand customer behavior and segmentation
- Optimize product inventory and pricing
- Make data-driven marketing decisions

### Solution Approach
Build an automated ETL pipeline using Databricks for processing and Power BI for visualization, with Delta Lake as the storage layer.

## Architecture Layers

### 1. Data Sources
- **Input**: CSV files, API endpoints, or streaming data
- **Sample datasets**:
  - `orders.csv` - Transaction data with order_id, customer_id, product_id, quantity, price, order_date, status
  - `customers.csv` - Customer demographics with customer_id, name, email, city, state, segment
  - `products.csv` - Product catalog with product_id, name, category, price, stock_quantity

### 2. Bronze Layer (Raw)
- **Purpose**: Ingest raw data as-is from sources
- **Storage**: Databricks File System (DBFS) or cloud storage (S3/ADLS)
- **Format**: CSV/JSON stored as Delta Lake tables
- **Notebook**: `notebooks/01_bronze/01_ingest_data`
- **Operations**:
  - Load raw files into bronze tables
  - Add ingestion timestamp and metadata
  - Preserve original data structure
  - Handle schema evolution

### 3. Silver Layer (Cleansed)
- **Purpose**: Clean, validate, and standardize data
- **Storage**: Delta tables with schema enforcement
- **Notebook**: `notebooks/02_silver/02_cleanse_data`
- **Operations**:
  - Remove duplicates
  - Handle nulls and invalid values
  - Standardize data types (dates, numbers)
  - Add surrogate keys
  - Apply business rules and validations
  - Slowly Changing Dimension (SCD) handling

### 4. Gold Layer (Business Aggregate)
- **Purpose**: Create business-level aggregates optimized for reporting
- **Storage**: Denormalized Delta tables for Power BI consumption
- **Notebook**: `notebooks/03_gold/03_create_aggregates`
- **Tables**:
  - `sales_summary_daily` - Daily sales metrics by product/category
  - `customer_analysis` - Customer RFM analysis and segments
  - `product_performance` - Product KPIs and ranking
- **Optimizations**:
  - Z-Ordering for query performance
  - Data skipping indexes
  - Partitioning by date/category
  - VACUUM and OPTIMIZE maintenance

### 5. Power BI Layer
- **Connection**: DirectQuery to Databricks SQL or Delta Lake
- **Authentication**: Azure AD or personal access token
- **Datasets**:
  - Gold layer tables as semantic model
  - Relationships between fact and dimension tables
- **Reports**:
  - Executive Dashboard (KPIs, trends)
  - Sales Analysis (by product, region, time)
  - Customer Segmentation (RFM analysis)
  - Inventory Management (stock levels, reorder points)

## Technology Stack

### Databricks
- Runtime: 10.4+ with Photon acceleration
- Delta Lake: 2.0+
- Cluster: Standard_DS3_v2 or equivalent
- Unity Catalog (optional for enterprise governance)

### Power BI
- Power BI Desktop (free development)
- Power BI Premium or Pro with Premium Per User
- Gateway: On-premises data gateway if needed
- DirectQuery mode for real-time data

### Python
- databricks-sdk: For automation and deployment
- pandas: For local data processing and testing
- pytest: Testing framework
- azure-identity: Authentication (if using Azure)

## Deployment Architecture

### Manual Deployment
1. Upload notebooks to Databricks workspace
2. Manually run notebooks in sequence (bronze → silver → gold)
3. Schedule jobs using Databricks Jobs UI

### Automated Deployment (Planned)
- Python scripts in `src/` for programmatic notebook deployment
- CI/CD pipeline with GitHub Actions
- Environment-specific configuration management
- Automated testing and validation

### Monitoring
- Databricks Job run history and notifications
- Pipeline duration metrics
- Data quality checks (row counts, null percentages)
- Alerting on failures via email/Slack

## Security Considerations

- Never store credentials in version control
- Use secrets management (Databricks Secrets, Azure Key Vault)
- Implement least-privilege access with Unity Catalog
- Encrypt data at rest and in transit
- Audit logs for compliance

## Scalability

- Databricks auto-scaling clusters handle data volume growth
- Delta Lake's partitioning and Z-Ordering optimize large tables
- Power BI aggregations for high-cardinality datasets
- Separate clusters for dev/test/prod environments

## Cost Optimization

- Use spot instances for non-critical workloads
- Auto-terminate clusters after inactivity
- Power BI Premium capacity for large datasets
- Delta Lake's data compaction reduces storage costs

## Future Enhancements

- Streaming data pipeline with Auto Loader
- MLflow for predictive models (customer churn, demand forecasting)
- Delta Live Tables for declarative ETL
- Data quality framework with Great Expectations
- Data vault modeling for enterprise data warehouse

## References

- [Databricks Delta Lake Documentation](https://docs.databricks.com/delta/index.html)
- [Power BI DirectQuery Best Practices](https://learn.microsoft.com/power-bi/connect-data/desktop-directquery-about)
- [Lakehouse Architecture](https://docs.databricks.com/lakehouse/index.html)