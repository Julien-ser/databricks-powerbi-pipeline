# Deployment Guide

This guide covers deploying the databricks-powerbi-pipeline to a Databricks workspace.

## Prerequisites

- Databricks workspace (Cloud or Community Edition)
- Python 3.8+ with pip
- Databricks Personal Access Token or Azure AD authentication
- Access to create workspace objects (notebooks, storage)

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy the example environment configuration and fill in your credentials:

```bash
cp config/env.example.py config/env.py
```

Edit `config/env.py` with your actual values:

- `DATABRICKS_HOST`: Your Databricks workspace URL (e.g., `https://adb-1234567890123456.17.azuredatabricks.net`)
- `DATABRICKS_TOKEN`: Generate a Personal Access Token from Databricks User Settings > Access Tokens
- Optional: Configure storage, Power BI, and notification settings

### 3. Configure Parameters

Edit `config/parameters.json` to set:

- `databricks.workspace_url`: Should match your host
- `databricks.catalog`: Target Unity Catalog catalog name (create if needed)
- `databricks.schema`: Target schema name (e.g., `analytics`)
- `data.*_path`: Storage paths for Delta tables (must be accessible from your workspace)

## Storage Configuration

### Option A: DBFS Mount Points

If using DBFS, ensure the paths exist in your workspace:

1. Create mount points or directories:
   ```
   /mnt/data/raw/       # Upload sample CSVs here
   /mnt/delta/bronze/   # Bronze Delta tables
   /mnt/delta/silver/   # Silver Delta tables
   /mnt/delta/gold/     # Gold Delta tables
   ```

2. Upload sample data to `/mnt/data/raw/`:
   - `sample_customers.csv`
   - `sample_products.csv`
   - `sample_orders.csv`
   - `sample_order_items.csv`

### Option B: Cloud Storage (S3/ADLS)

Configure cloud storage credentials in Databricks and update paths in `parameters.json` to use cloud URIs (e.g., `s3://bucket/path/`, `abfss://container@account.dfs.core.windows.net/path/`).

## Deployment Steps

### 1. Generate Sample Data (Optional)

If you need to regenerate the sample e-commerce data:

```bash
python src/generate_sample_data.py
```

This creates synthetic data in the `data/` directory for local testing.

### 2. Deploy Notebooks to Databricks

Deploy all notebooks to your Databricks workspace in the correct order:

```bash
python src/deploy_notebooks.py
```

This will upload notebooks to:
```
/Users/<your-username>/01_bronze/bronze_ingestion
/Users/<your-username>/02_silver/silver_transformation
/Users/<your-username>/03_gold/gold_aggregation
```

**Note:** If `databricks-sdk` is not available, the script runs in simulation mode and skips actual deployment.

### 3. Run the Pipeline

Execute the ETL pipeline to process data through bronze → silver → gold layers:

```bash
python src/monitor_pipeline.py
```

This will:
- Run the bronze ingestion notebook
- Run the silver transformation notebook (if bronze succeeds)
- Run the gold aggregation notebook (if silver succeeds)
- Track execution metrics and log results

The script exits with code 0 on success, non-zero on failure.

### 4. Schedule the Pipeline (Optional)

To run the pipeline automatically on a schedule:

**Using Databricks Jobs:**
1. In your Databricks workspace, go to Jobs
2. Create a new job
3. Add a task that runs `monitor_pipeline.py` as a Python script on a cluster
4. Set the schedule in the job settings (e.g., daily at 2 AM)

**Using External Scheduler (cron/Airflow):**
```bash
# Add to crontab with proper environment
0 2 * * * cd /path/to/project && /usr/bin/python3 src/monitor_pipeline.py >> logs/cron.log 2>&1
```

## Verification

After running the pipeline, verify the Delta tables were created:

```python
# In a Databricks notebook or via databricks-sdk
spark.sql("SHOW TABLES IN ecommerce.analytics").show()
```

Expected tables:
- `bronze_customers`, `bronze_products`, `bronze_orders`, `bronze_order_items`
- `silver_customers`, `silver_products`, `silver_orders`, `silver_order_items`
- `dim_customer`, `dim_product`, `fact_sales`, `monthly_sales`

## Troubleshooting

### "databricks-sdk not installed"
Install the SDK:
```bash
pip install databricks-sdk
```

### Authentication Errors
- Verify your token is valid and not expired
- Check that the token has Workspace permissions
- Ensure `DATABRICKS_HOST` matches the workspace URL exactly

### Permission Errors
- Ensure your user has Can Manage permission on the target workspace directory
- For Unity Catalog, verify you have USAGE on catalog and CREATE on schema

### Path Not Found Errors
- Verify mount points or cloud storage paths exist and are accessible
- Check cluster IAM roles or instance profiles have read/write permissions
- For DBFS, ensure the path starts with `/mnt/` and is correctly mounted

### Notebook Execution Failures
Check the execution logs in the Databricks workspace UI for detailed error messages. Common issues:
- Missing libraries on the cluster (install pyspark, delta-spark)
- Insufficient cluster size or auto-scaling issues
- Data format mismatches in source CSVs

## Simulation Mode

If you don't have a Databricks workspace available, the deployment and pipeline scripts run in simulation mode:

- `deploy_notebooks.py` will log what it would deploy without making API calls
- `monitor_pipeline.py` will simulate successful execution of all notebooks

This is useful for testing the code structure, running unit tests, and development without cloud resources.

## Next Steps

After successful deployment and pipeline execution:

1. Connect Power BI to the gold Delta tables (see `docs/powerbi-setup.md`)
2. Build your dashboards and reports
3. Set up alerts and monitoring (see `docs/monitoring.md` if available)
4. Customize the business logic for your specific needs
