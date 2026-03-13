# Monitoring and Operations Guide

This guide covers monitoring, maintaining, and troubleshooting the databricks-powerbi-pipeline in production.

## Table of Contents

- [Pipeline Monitoring](#pipeline-monitoring)
- [Logging](#logging)
- [Alerting](#alerting)
- [Troubleshooting](#troubleshooting)
- [Performance Optimization](#performance-optimization)
- [Maintenance Tasks](#maintenance-tasks)
- [Disaster Recovery](#disaster-recovery)

---

## Pipeline Monitoring

### Monitoring Points

Monitor these key components:

1. **Pipeline Execution Success/Failure**
   - Did all notebooks run without errors?
   - Check exit codes and logs

2. **Execution Duration**
   - Track how long each stage takes
   - Set baseline and alert on significant deviations

3. **Data Volume Metrics**
   - Row counts at each layer (bronze → silver → gold)
   - Compare against expected volumes

4. **Data Quality**
   - Null percentages in key fields
   - Duplicate counts
   - Referential integrity between fact and dimension tables

5. **Databricks Cluster Health**
   - Cluster uptime and auto-scaling
   - Job queue times
   - Resource utilization (CPU, memory, disk)

### Quick Health Check Script

```python
# check_health.py
from utils import load_config, setup_logging
from monitor_pipeline import PipelineMonitor
import json

setup_logging()
config = load_config("config/parameters.json")

# Check if we can connect
monitor = PipelineMonitor()
if monitor.client:
    print("✓ Databricks connection OK")
else:
    print("✗ Cannot connect to Databricks")
    exit(1)

# Check recent job runs (requires databricks-sdk)
# This would need to be implemented based on your needs

# Check Delta table existence
# (run SQL queries via monitor.client if available)
```

---

## Logging

### Log Locations

- **Console**: Standard output when running scripts
- **File**: `logs/pipeline.log` (rotated manually)

### Log Format

```
2025-03-13 10:30:45,123 - module_name - INFO - Message
2025-03-13 10:30:46,456 - module_name - ERROR - Something failed
```

### Log Levels

- `DEBUG`: Detailed debugging information
- `INFO`: General progress and status (default)
- `WARNING`: Non-critical issues
- `ERROR`: Failures and exceptions
- `CRITICAL`: Severe errors requiring immediate attention

### Setting Log Level

```python
from utils import setup_logging
setup_logging("DEBUG")  # Set globally
```

Or via environment variable:
```bash
export PYTHON_LOG_LEVEL=DEBUG
python src/deploy_notebooks.py
```

### Reading Logs

```bash
# Tail the log file
tail -f logs/pipeline.log

# Search for errors
grep -i error logs/pipeline.log

# Count recent errors
tail -100 logs/pipeline.log | grep -c ERROR

# View last successful run
grep "Pipeline run completed" logs/pipeline.log | tail -1
```

---

## Alerting

### Built-in Alerting

The pipeline can send alerts on failures via:

- **Email** (SMTP)
- **Slack** (webhook)

### Email Setup

1. Configure in `config/env.py`:

```python
EMAIL_SENDER = "pipeline-alerts@yourcompany.com"
EMAIL_RECIPIENTS = "data-team@yourcompany.com"
```

2. Add SMTP configuration (if needed). The code currently logs alerts; to implement email:

```python
# In monitor_pipeline.py, implement _send_alert():
import smtplib
from email.mime.text import MIMEText

def _send_alert(self, message: str) -> None:
    if not self.config.get("send_alerts", False):
        return
    # Implement SMTP using config.env SMTP_* settings
```

### Slack Setup

1. Create Slack Incoming Webhook:
   - Go to https://api.slack.com/apps
   - Create new app → Incoming Webhooks
   - Enable and copy webhook URL

2. Add to `config/env.py`:

```python
SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/..."
```

3. Set `send_alerts: true` in `parameters.json`.

### External Monitoring

For enterprise monitoring, consider:

- **Databricks Job Alerts**: Native email notifications on job failures
- **Azure Monitor / CloudWatch**: Collect metrics and set up alerts
- **PagerDuty / Opsgenie**: Critical alert escalation
- **Grafana / Datadog**: dashboards with metrics

---

## Troubleshooting

### Common Issues

#### 1. "databricks-sdk not installed"

**Symptom**: Scripts run in simulation mode, no actual deployment.

**Solution**:
```bash
pip install databricks-sdk
```

#### 2. Authentication Errors

**Symptom**: "Failed to connect to Databricks" or "Invalid token"

**Causes and Solutions**:
- Token expired → Generate new PAT in Databricks
- Wrong host URL → Verify workspace URL matches exactly
- Token lacks permissions → Ensure token has Workspace access
- Network/firewall → Check connectivity to `*.azuredatabricks.net` or `*.databricks.com`

**Debug**:
```python
from databricks.sdk import WorkspaceClient
client = WorkspaceClient(host="...", token="...")
# Should succeed without error
```

#### 3. Path Not Found

**Symptom**: "Path does not exist" when running notebooks.

**Causes**:
- DBFS mount point not created
- Cloud storage not mounted or permissions denied
- Typo in `parameters.json`

**Debug**:
- In Databricks notebook, run: `dbutils.fs.ls("/mnt/data/raw")`
- Check cluster logs for mount errors
- Verify IAM roles/instance profiles

#### 4. Notebook Execution Failure

**Symptom**: Notebook runs but fails with errors.

**Debug Steps**:

1. Check Databricks workspace UI → Job → Run history
2. View notebook output in UI for full stack trace
3. Common issues:
   - Missing libraries on cluster (install `pyspark`, `delta-spark`)
   - Data format mismatches in source CSVs
   - Insufficient cluster size (scale up)
   - Table already exists (use `OVERWRITE` mode)

4. Run notebook manually in workspace to isolate issues

#### 5. Slow Performance

**Causes**:
- Small cluster (auto-scale or use larger instance)
- Unoptimized Delta tables (no Z-Ordering, many small files)
- Complex SQL queries
- DirectQuery in Power BI fetching too much data

**Solutions**:
- Optimize Delta tables: `OPTIMIZE table_name ZORDER BY (date_column)`
- Increase cluster worker count or use larger instance types
- Use Power BI aggregations or import mode
- Add filters to Power BI visuals

#### 6. Permission Errors

**Symptom**: "Access denied" when deploying or running notebooks.

**Required Permissions**:
- **Workspace**: CanManage on target directory
- **Unity Catalog** (if used):
  - USAGE on catalog
  - CREATE on schema
  - SELECT/INSERT on tables

**Grant permissions** in Databricks admin console or via SQL:
```sql
GRANT USAGE ON CATALOG ecommerce TO user@example.com;
GRANT CREATE ON SCHEMA ecommerce.analytics TO user@example.com;
```

---

## Performance Optimization

### Delta Lake Optimizations

The gold layer notebooks should implement:

```sql
-- Optimize for query performance
OPTIMIZE fact_sales ZORDER BY (order_date, customer_id);

-- Vacuum old files (after 7 days)
VACUUM fact_sales RETAIN 168 HOURS;

-- Compact small files
OPTIMIZE dim_customer;

-- Analyze for query planning
ANALYZE TABLE fact_sales COMPUTE STATISTICS;
```

**Schedule optimizations as separate jobs** or include in pipeline (if tables are large).

### Cluster Configuration

Recommended cluster for production:

- **Cluster Mode**: Single User (for job isolation)
- **Databricks Runtime**: 13.3+ with Photon
- **Workers**: Auto-scaling (2-8) based on workload
- **Worker Type**: `Standard_DS3_v2` or `Standard_DS4_v2` (Azure), equivalent on AWS/GCP
- **Auto-termination**: 30 minutes (for job clusters)
- **Spot instances**: Enable for cost savings (if workflow allows interruptions)

### Power BI Performance

- **Use DirectQuery with filters**: Always filter by date
- **Import for small dimension tables**: `dim_customer`, `dim_product` can be imported
- **Pre-aggregate**: Use `monthly_sales` for trend visuals instead of querying `fact_sales`
- **Avoid high-cardinality columns**: Too many distinct values slow DirectQuery

---

## Maintenance Tasks

### Daily

- **Monitor pipeline success**: Check logs or set up alerts
- **Review cluster usage**: Ensure clusters auto-terminate properly

### Weekly

- **Check data freshness**: Verify new data is arriving in bronze layer
- **Review job durations**: Ensure ETL completes within SLA
- **Monitor storage growth**: Delta tables growing as expected?

### Monthly

- **Optimize Delta tables** (if not automated):
  ```sql
  OPTIMIZE fact_sales ZORDER BY (order_date);
  VACUUM fact_sales;
  ```

- **Update statistics**:
  ```sql
  ANALYZE TABLE fact_sales COMPUTE STATISTICS;
  ```

- **Review and archive logs**: Compress or delete old `logs/pipeline.log` files

- **Refresh Power BI datasets**: If using Import mode, ensure scheduled refreshes are working

### Quarterly

- **Review cluster sizing**: Scale up or down based on usage patterns
- **Cost optimization**: Check for unused resources, spot instance usage
- **Security audit**: Rotate tokens, review permissions

---

## Disaster Recovery

### Backup Strategy

1. **Source Data**:
   - Keep raw data in persistent storage (S3, ADLS, not ephemeral DBFS)
   - Enable bucket versioning if using cloud storage

2. **Delta Tables**:
   - Delta Lake provides ACID transactions and time travel
   - To restore to previous version:
     ```sql
     RESTORE fact_sales TO VERSION AS OF 123;
     -- or
     RESTORE fact_sales TO TIMESTAMP AS OF '2025-03-01T00:00:00';
     ```

3. **Configuration**:
   - Version control all code, parameters.json, and notebooks
   - Backup secrets separately (secure location)

### Recovery Procedures

#### If Databricks workspace is unavailable

1. Wait for Databricks incident resolution (check status.databricks.com)
2. Pipeline will automatically resume when workspace is back
3. For missed runs, manually trigger catch-up processing

#### If data is corrupted or lost

1. Identify corrupted tables via `DESCRIBE HISTORY table_name`
2. Restore from previous version or re-run ETL from bronze layer
3. Re-generate gold layer if necessary

#### If pipeline is failing repeatedly

1. Pause scheduled jobs (if any)
2. Investigate root cause via logs
3. Run notebooks manually to isolate failing stage
4. Fix issue, then resume scheduled execution

---

## Metrics to Track

Track these metrics over time:

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| `pipeline_success_rate` | % of successful runs | < 95% |
| `pipeline_duration_minutes` | Total ETL time | > 2× baseline |
| `bronze_row_count` | Rows ingested | Outside expected range |
| `gold_row_count` | Rows in fact table | < 90% of bronze |
| `cluster_autoscaling_events` | Frequent scale events | > 5 per day |
| `query_duration_seconds` | Power BI query times | > 30 seconds |

---

## Health Dashboard

Create a simple monitoring dashboard:

```python
# health_dashboard.py
from utils import load_config, setup_logging
from datetime import datetime, timedelta
import json

setup_logging()
config = load_config("config/parameters.json")

# Check recent log entries for failures
def check_recent_failures(hours=24):
    # Parse logs and count errors
    pass

# Check if pipeline ran as scheduled
def check_schedule_adherence():
    # Compare last run time with expected schedule
    pass

# Generate health report
print(f"Health Check: {datetime.now()}")
print(f"Environment: {config['environment']}")
# Add more checks...
```

---

## Support Resources

- **Databricks Documentation**: https://docs.databricks.com/
- **Delta Lake Guide**: https://docs.delta.io/
- **Power BI DirectQuery**: https://learn.microsoft.com/power-bi/connect-data/desktop-directquery-about
- **Project Issues**: Check GitHub Issues for known problems

---

## Next Steps

- Set up alerting to notify on failures
- Create runbooks for common issues
- Schedule regular maintenance tasks
- Document site-specific configurations (company-specific details)
