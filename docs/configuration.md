# Configuration Reference

This guide provides a comprehensive reference for all configuration files in the project.

## Table of Contents

- [Configuration Files Overview](#configuration-files-overview)
- [env.py](#envpy)
- [parameters.json](#parametersjson)
- [Configuration Hierarchy](#configuration-hierarchy)
- [Environment-Specific Configs](#environment-specific-configs)
- [Best Practices](#best-practices)

---

## Configuration Files Overview

The project uses two configuration files:

| File | Purpose | Format | Secrets | Version Control |
|------|---------|--------|---------|-----------------|
| `config/env.py` | Secrets and credentials | Python module | Yes | No (gitignored) |
| `config/parameters.json` | Pipeline parameters | JSON | No | Yes |

---

## env.py

**Location**: `config/env.py` (create from `config/env.example.py`)  
**Format**: Python module with variables  
**Version Control**: **DO NOT COMMIT** (listed in `.gitignore`)

### Variables

#### Databricks Connection

```python
DATABRICKS_HOST = "https://adb-1234567890123456.17.azuredatabricks.net"
```

Your Databricks workspace URL. Must include `https://`.

```python
DATABRICKS_TOKEN = "dapiXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
```

Personal Access Token from Databricks (User Settings → Access Tokens). Must have Workspace permissions.

```python
DATABRICKS_WORKSPACE_ID = "1234567890123456"
```

Azure workspace ID (optional). Used for Azure-specific operations.

#### Cloud Storage (Optional)

If using cloud storage (S3, ADLS) instead of DBFS:

```python
STORAGE_ACCOUNT = "yourstorageaccount"
STORAGE_CONTAINER = "ecommerce"
STORAGE_KEY = "storage-key-here"
```

#### Power BI Integration (Optional)

```python
POWERBI_WORKSPACE_ID = "your-powerbi-workspace-id"
POWERBI_DATASET_ID = "your-dataset-id"
```

Used for automated dataset management (not required for manual setup).

#### Notification Settings

```python
SLACK_WEBHOOK_URL = ""  # e.g., "https://hooks.slack.com/services/..."
EMAIL_SENDER = "pipeline-alerts@yourcompany.com"
EMAIL_RECIPIENTS = "data-team@yourcompany.com"
```

For pipeline failure notifications (must be enabled in parameters).

#### Feature Flags

```python
ENABLE_MONITORING = True
SEND_NOTIFICATIONS = False
```

---

## parameters.json

**Location**: `config/parameters.json`  
**Format**: JSON  
**Version Control**: Yes (template committed, local modifications OK)

### Schema

```json
{
  "environment": "dev",
  "databricks": {
    "workspace_url": "https://adb-1234567890123456.17.azuredatabricks.net",
    "cluster_id": "cluster-id-here",
    "catalog": "ecommerce",
    "schema": "analytics"
  },
  "data": {
    "bronze_path": "/mnt/bronze/ecommerce",
    "silver_path": "/mnt/silver/ecommerce",
    "gold_path": "/mnt/gold/ecommerce"
  },
  "powerbi": {
    "workspace_id": "powerbi-workspace-id",
    "dataset_id": "gold_dataset"
  },
  "scheduling": {
    "etl_frequency": "daily",
    "etl_time": "02:00"
  },
  "send_alerts": false
}
```

### Fields

#### Root

| Field | Type | Description |
|-------|------|-------------|
| `environment` | string | Environment name: `dev`, `staging`, `prod` |
| `send_alerts` | boolean | Enable failure notifications (requires notification config in env.py) |

#### databricks

| Field | Type | Description |
|-------|------|-------------|
| `workspace_url` | string | Databricks workspace URL (should match `DATABRICKS_HOST`) |
| `cluster_id` | string | Cluster ID for job execution (optional, can be configured in Databricks Jobs) |
| `catalog` | string | Unity Catalog catalog name (if using UC). Use `spark_catalog` for default. |
| `schema` | string | Schema/database name within catalog |

#### data

| Field | Type | Description |
|-------|------|-------------|
| `bronze_path` | string | DBFS or cloud storage path for bronze Delta tables |
| `silver_path` | string | Path for silver Delta tables |
| `gold_path` | string | Path for gold Delta tables |

**Path Formats:**
- DBFS: `/mnt/bronze/ecommerce`
- S3: `s3://bucket-name/bronze/`
- ADLS: `abfss://container@account.dfs.core.windows.net/bronze/`

#### powerbi

| Field | Type | Description |
|-------|------|-------------|
| `workspace_id` | string | Power BI workspace (app) ID |
| `dataset_id` | string | Power BI dataset ID (optional) |

#### scheduling

| Field | Type | Description |
|-------|------|-------------|
| `etl_frequency` | string | Recurrence: `hourly`, `daily`, `weekly` |
| `etl_time` | string | Cron-style time (HH:MM) when ETL should run |

---

## Configuration Hierarchy

Configuration is loaded with the following precedence (highest to lowest):

1. **Environment variables** (if implemented in code)
2. `config/parameters.json`
3. Default values in code

The system loads:
- `config/parameters.json` via `utils.load_config()`
- `config/env.py` directly (Python import) for secrets

---

## Environment-Specific Configs

For multi-environment deployments, create environment-specific parameter files:

```
config/
├── parameters.json           # Default (dev)
├── parameters.prod.json      # Production overrides
├── parameters.staging.json   # Staging overrides
```

Load a specific configuration:
```python
import sys
env = sys.argv[1] if len(sys.argv) > 1 else "dev"
config_path = f"config/parameters.{env}.json"
config = load_config(config_path)
```

---

## Best Practices

### Secrets Management

- **Never** store secrets in `parameters.json` or version control
- Use `env.py` (gitignored) for local development
- For production, use:
  - Databricks Secrets (mount as environment variables)
  - Azure Key Vault
  - AWS Secrets Manager
  - HashiCorp Vault

Example using Databricks Secrets:
```python
# In env.py or code
import os
DATABRICKS_TOKEN = os.environ.get("DATABRICKS_TOKEN", "")
```

### Path Consistency

Ensure paths in `parameters.json` match:
1. Storage locations mounted in Databricks workspace
2. Permissions granted to your user/service principal
3. Cluster access mode (Single User vs. Shared)

### Catalog and Schema

If using Unity Catalog:
- Create catalog: `CREATE CATALOG ecommerce;`
- Create schema: `CREATE SCHEMA ecommerce.analytics;`
- Grant privileges: `GRANT CREATE, USAGE ON CATALOG ecommerce TO <user>;`

If not using Unity Catalog:
- Set `"catalog": "spark_catalog"`
- Set `"schema": "default"` or your database name

### Parameter Validation

Before deployment, validate configuration:

```python
from utils import load_config
from dataclasses import dataclass

@dataclass
class Config:
    workspace_url: str
    catalog: str
    schema: str
    bronze_path: str
    silver_path: str
    gold_path: str

def validate_config(config: Dict) -> Config:
    required = [
        "databricks.workspace_url",
        "databricks.catalog",
        "databricks.schema",
        "data.bronze_path",
        "data.silver_path",
        "data.gold_path"
    ]
    # Check all required fields exist
    for field in required:
        keys = field.split(".")
        value = config
        for key in keys:
            value = value[key]
        if not value:
            raise ValueError(f"Missing required config: {field}")
    return Config(**{
        "workspace_url": config["databricks"]["workspace_url"],
        "catalog": config["databricks"]["catalog"],
        # ... etc
    })
```

### Parameter Templates

Use `parameters.json` as a template. For production:

```json
{
  "environment": "prod",
  "databricks": {
    "workspace_url": "https://adb-1234567890123456.17.azuredatabricks.net",
    "catalog": "ecommerce_prod",
    "schema": "analytics"
  },
  "data": {
    "bronze_path": "/mnt/delta/bronze/ecommerce",
    "silver_path": "/mnt/delta/silver/ecommerce",
    "gold_path": "/mnt/delta/gold/ecommerce"
  },
  "send_alerts": true
}
```

---

## Testing Configuration

Test your configuration without deploying:

```python
# test_config.py
from utils import load_config
from deploy_notebooks import deploy_all_notebooks
from monitor_pipeline import run_etl_pipeline

config = load_config("config/parameters.json")
print("Configuration loaded:", config["environment"])

# Test simulation mode (no databricks-sdk)
deploy_all_notebooks()  # Will simulate if SDK missing
run_etl_pipeline()      # Will simulate if SDK missing
```

---

## Troubleshooting

### "Config file not found"
- Verify `config/parameters.json` exists
- Check file permissions

### Missing keys
- Ensure `parameters.json` has all required fields
- Compare with the schema above

### Invalid paths
- Verify DBFS mount points or cloud storage URIs are accessible
- Test with Databricks CLI or notebook first

### Import errors in env.py
- `env.py` must be valid Python syntax
- Use `from config.env import DATABRICKS_HOST`
- Check for missing quotes or typos

---

## Next Steps

After configuring:
1. [Deploy the notebooks](deployment.md)
2. [Generate sample data](api-reference.md#generate_sample_data)
3. [Run the pipeline](api-reference.md#monitor_pipeline)
4. [Connect Power BI](powerbi-setup.md)
