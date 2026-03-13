# Power BI Setup Guide

This guide covers connecting Power BI to your Databricks e-commerce analytics pipeline.

## Prerequisites

- Power BI Desktop (free) or Power BI Premium/Pro service
- Databricks workspace with completed ETL pipeline (bronze, silver, gold layers)
- Network connectivity between Power BI and Databricks (DirectQuery requires accessible endpoint)

## Connection Options

Power BI can connect to Databricks Delta tables using:
- **DirectQuery**: Real-time queries (recommended for large datasets, fresh data)
- **Import**: Data imported to Power BI (faster visuals, scheduled refresh)

This guide uses **DirectQuery** for real-time analytics.

## Step 1: Get Databricks Connection Details

From your Databricks workspace:

1. **Workspace URL**: Copy from browser address bar
   ```
   https://adb-1234567890123456.17.azuredatabricks.net
   ```

2. **Generate a Personal Access Token**:
   - Click user icon → Settings → Access Tokens
   - Generate new token (set long expiration)
   - Copy the token (you won't see it again)

3. **Identify your Delta table location**:
   - Gold layer tables: `dim_customer`, `dim_product`, `fact_sales`, `monthly_sales`
   - Unity Catalog format: `catalog.schema.table_name`
   - Or path format: `dbfs:/mnt/delta/gold/table_name`

## Step 2: Install the Databricks Connector in Power BI

1. Open Power BI Desktop
2. Go to **Get Data** → **More...**
3. Search for **Databricks** (may be under "Database" category)
4. Select **Databricks** → **Connect**

If the Databricks connector is not available:
- Install the "Databricks" custom connector from AppSource
- Or use **Get Data → Azure → Azure Databricks** (for Azure-hosted Databricks)

## Step 3: Configure the Connection

### For Unity Catalog Tables (Recommended)

If you're using Unity Catalog:

1. In Power BI Get Data dialog:
   - **Server**: Your workspace URL without https://
     ```
     adb-1234567890123456.17.azuredatabricks.net
     ```
   - **HTTP Path**: Found in Databricks SQLWarehouse or JDBC/ODBC connection details
     - Go to Databricks → SQL → SQL Warehouses → Connection Details → HTTP Path
     - Copy the path (starts with `/sql/1.0/...`)
   - **Databases**: Select your catalog and schema (e.g., `ecommerce.analytics`)
   - **Authentication**: **Personal Access Token**
   - **Token**: Paste your PAT

2. Select tables to import or use DirectQuery:
   - Choose **DirectQuery** for real-time (recommended for production)
   - Choose **Import** for faster performance with smaller datasets

### For Path-Based Tables (Legacy)

If using DBFS paths:

1. Use **Get Data → Other → ODBC** if you have Databricks ODBC driver installed
2. Configure DSN with:
   - Host: your workspace URL
   - HTTP Path: `/sql/1.0/endpoints/your-endpoint-id`
   - Authentication: Token
3. Alternatively, use the Databricks connector with server/path as above

## Step 4: Build Your Report

Once connected, you'll see the available tables:

### Recommended Data Model

Build a star schema in Power BI:

**Fact Tables:**
- `fact_sales`: Main transactional fact with order line items
  - Columns: order_id, customer_id, product_id, order_date, quantity, unit_price, line_total, etc.
- `monthly_sales`: Pre-aggregated monthly metrics (optional)
  - Columns: year_month, total_sales, order_count, avg_order_value

**Dimension Tables:**
- `dim_customer`: Customer attributes
  - Keys: customer_id
  - Attributes: first_name, last_name, email, city, state, customer_segment, signup_date
- `dim_product`: Product catalog
  - Keys: product_id
  - Attributes: product_name, category, price, cost, inventory_quantity

### Creating Relationships

In Power BI Model view:
1. Drag `fact_sales[customer_id]` to `dim_customer[customer_id]`
2. Drag `fact_sales[product_id]` to `dim_product[product_id]`
3. Set cross-filter direction to single (dim → fact)

### Sample Measures (DAX)

Create measures for KPI visuals:

```dax
Total Sales = SUM(fact_sales[line_total])
Total Orders = DISTINCTCOUNT(fact_sales[order_id])
Average Order Value = DIVIDE([Total Sales], [Total Orders])
Customer Count = DISTINCTCOUNT(dim_customer[customer_id])
Product Count = DISTINCTCOUNT(dim_product[product_id])

Monthly Sales = 
CALCULATE(
    [Total Sales],
    DATESMTD(fact_sales[order_date])
)

YoY Sales Growth =
VAR CurrentYear = TOTALYTD([Total Sales], fact_sales[order_date])
VAR PriorYear = TOTALYTD([Total Sales], SAMEPERIODLASTYEAR(fact_sales[order_date]))
RETURN
DIVIDE(CurrentYear - PriorYear, PriorYear)
```

## Step 5: Create Visualizations

Recommended dashboard pages:

### 1. Executive Summary
- KPI cards: Total Sales, Total Orders, Avg Order Value, Active Customers
- Line chart: Sales trend over time (monthly)
- Bar chart: Top 10 products by revenue
- Pie chart: Sales by customer segment

### 2. Customer Analytics
- Map: Sales by state/city
- Table: Customer details with RFM segmentation
- Bar: Customer segment performance

### 3. Product Performance
- Matrix: Product catalog with sales metrics
- Bar: Category performance
- Scatter: Price vs. quantity sold

### 4. Order Fulfillment
- Table: Orders by status (shipped, processing, cancelled, returned)
- Trend: Order volume over time
- Metrics: Fulfillment rate

## Step 6: Configure Refresh Schedule

If using **Import** mode (not DirectQuery):

1. In Power BI Service (online):
   - Publish your report to a workspace
   - Go to the dataset settings
   - Configure scheduled refresh (e.g., daily at 3 AM)
   - Enter Databricks credentials for the data source

2. For DirectQuery, data is always fresh (no refresh needed)

## Performance Tips

1. **Use aggregations**: The `monthly_sales` table provides pre-aggregated data for trend visuals
2. **Filter early**: Apply date filters in queries to reduce data scanned
3. **Optimize visuals**: Avoid too many visuals on one page with DirectQuery
4. **Use integer keys**: Ensure fact tables use integer foreign keys to dimensions
5. **Partition gold tables**: Large tables benefit from partitioning in Delta Lake

## Troubleshooting

### "Unable to connect to the server"
- Verify workspace URL and HTTP Path are correct
- Check network connectivity (firewall, VPC, etc.)
- Ensure token has not expired

### "Query timeout" or slow performance
- Use DirectQuery with incremental filters
- Verify Delta tables are optimized (OPTIMIZE + ZORDER)
- Check query complexity - simplify visuals or use aggregates
- Increase query timeout in Power BI dataset settings

### "The function 'DATATABLE' is not supported"
- This is a DirectQuery limitation. Use calculated tables in Power Query instead.

### Schema changes not reflected
- For DirectQuery, refresh the dataset schema in Power BI
- For Import mode, trigger a full refresh

### Missing tables in connector
- Verify tables exist in the selected catalog/schema
- Check permissions: your user needs SELECT on the tables
- If using Unity Catalog, ensure cluster access mode is set correctly

## Next Steps

- Set up data alerts in Power BI for threshold monitoring
- Create dashboards and share with your team
- Schedule email subscriptions for report distribution
- Integrate with Power BI Embedded for application embedding
