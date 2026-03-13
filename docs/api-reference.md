# API Reference

This document provides a comprehensive reference for the Python modules in the databricks-powerbi-pipeline project.

## Table of Contents

- [deploy_notebooks](#deploy_notebooks)
- [monitor_pipeline](#monitor_pipeline)
- [generate_sample_data](#generate_sample_data)
- [utils](#utils)

---

## deploy_notebooks

Module for deploying Databricks notebooks to a workspace.

### Functions

#### `deploy_notebook(notebook_path: str, workspace_path: str, client=None) -> bool`

Deploy a single notebook to Databricks workspace.

**Parameters:**
- `notebook_path` (str): Local path to the notebook file (.ipynb)
- `workspace_path` (str): Target path in Databricks workspace (e.g., `/Users/username/01_bronze/bronze_ingestion`)
- `client` (WorkspaceClient, optional): Pre-initialized WorkspaceClient instance

**Returns:**
- `bool`: True if deployment succeeded, False otherwise

**Example:**
```python
from deploy_notebooks import deploy_notebook

success = deploy_notebook(
    notebook_path="notebooks/01_bronze/bronze_ingestion.ipynb",
    workspace_path="/Users/john.doe/01_bronze/bronze_ingestion"
)
```

#### `deploy_all_notebooks(notebooks_dir: str = "notebooks") -> bool`

Deploy all notebooks to Databricks workspace in the correct layer order (bronze → silver → gold).

**Parameters:**
- `notebooks_dir` (str): Local directory containing notebook layer folders

**Returns:**
- `bool`: True if all notebooks deployed successfully

**Behavior:**
- Deploys notebooks from `01_bronze`, `02_silver`, `03_gold` in order
- Constructs workspace paths as `/Users/<username>/<layer>/<notebook_name>`
- Logs deployment status and summary

**Example:**
```python
from deploy_notebooks import deploy_all_notebooks

success = deploy_all_notebooks("notebooks")
if success:
    print("All notebooks deployed successfully")
```

---

## monitor_pipeline

Module for executing and monitoring the ETL pipeline.

### Classes

#### `PipelineMonitor`

Monitor ETL pipeline execution with Databricks integration.

##### `__init__(config_path: str = "config/parameters.json")`

Initialize monitor with configuration.

**Parameters:**
- `config_path` (str): Path to configuration file (JSON)

**Attributes:**
- `config` (Dict): Loaded configuration
- `start_time` (datetime): Pipeline start timestamp
- `notebook_results` (List[Dict]): Execution results for each notebook
- `client` (WorkspaceClient): Databricks client (if available)

##### `start_run() -> None`

Mark the start of a pipeline run and record start time.

##### `run_notebook(workspace_path: str, timeout_seconds: int = 3600) -> Dict`

Execute a single notebook in Databricks workspace.

**Parameters:**
- `workspace_path` (str): Path to notebook in workspace
- `timeout_seconds` (int): Maximum execution time (currently unused)

**Returns:**
- `dict` with keys:
  - `notebook` (str): Notebook path
  - `status` (str): One of `SUCCESS`, `FAILED`, `ERROR`, `SIMULATED`
  - `execution_time` (float): Seconds taken
  - `run_id` (str, optional): Databricks run ID
  - `error` (str, optional): Error message if failed

##### `run_pipeline(notebooks: List[dict]) -> bool`

Run the full ETL pipeline by executing notebooks in sequence.

**Parameters:**
- `notebooks` (List[dict]): List of dicts with `name` and `path` keys

**Returns:**
- `bool`: True if all notebooks succeeded

**Behavior:**
- Executes notebooks in order
- Stops on first failure (no rollback)
- Collects results and calls `end_run()`

##### `end_run(success: bool) -> None`

Mark the end of a pipeline run and log summary.

**Parameters:**
- `success` (bool): Whether pipeline completed successfully

**Logs:**
- Total duration
- Success/failure status
- Per-notebook metrics (success count, total time)
- Detailed results for each notebook
- Alert if configured and failed

### Functions

#### `run_etl_pipeline() -> bool`

Execute the full ETL pipeline: bronze → silver → gold.

**Returns:**
- `bool`: True if pipeline succeeded

**Usage:**
```bash
python src/monitor_pipeline.py
```

Or as a module:
```python
from monitor_pipeline import run_etl_pipeline

success = run_etl_pipeline()
sys.exit(0 if success else 1)
```

**Pipeline Order:**
1. Bronze Ingestion (`/Users/default/01_bronze/bronze_ingestion`)
2. Silver Transformation (`/Users/default/02_silver/silver_transformation`)
3. Gold Aggregation (`/Users/default/03_gold/gold_aggregation`)

---

## generate_sample_data

Module for generating synthetic e-commerce datasets.

### Functions

#### `generate_customers(num_customers: int = 100) -> pd.DataFrame`

Generate sample customer data.

**Parameters:**
- `num_customers` (int): Number of customer records to generate

**Returns:**
- `pd.DataFrame`: DataFrame with columns:
  - `customer_id` (str): Format `CUST0000`
  - `first_name` (str)
  - `last_name` (str)
  - `email` (str)
  - `city` (str)
  - `state` (str)
  - `signup_date` (str): YYYY-MM-DD format
  - `customer_segment` (str): One of `Premium`, `Standard`, `Basic`

#### `generate_products(num_products: int = 50) -> pd.DataFrame`

Generate sample product catalog.

**Parameters:**
- `num_products` (int): Number of products to generate

**Returns:**
- `pd.DataFrame`: DataFrame with columns:
  - `product_id` (str): Format `PROD0000`
  - `product_name` (str)
  - `category` (str): One of 6 categories
  - `price` (float)
  - `cost` (float)
  - `inventory_quantity` (int)

#### `generate_orders(num_orders: int = 500, customers: Optional[List[str]] = None, products: Optional[List[str]] = None) -> pd.DataFrame`

Generate sample order headers.

**Parameters:**
- `num_orders` (int): Number of orders to generate
- `customers` (List[str], optional): List of customer IDs to use
- `products` (List[str], optional): List of product IDs (for reference)

**Returns:**
- `pd.DataFrame`: DataFrame with columns:
  - `order_id` (str): Format `ORDER000000`
  - `customer_id` (str)
  - `order_date` (str): Timestamp format
  - `status` (str): One of `completed`, `shipped`, `processing`, `cancelled`, `returned`
  - `total_amount` (float)
  - `shipping_address` (str)
  - `payment_method` (str): One of `credit_card`, `paypal`, `debit_card`

#### `generate_order_items(orders_df: pd.DataFrame, products_df: pd.DataFrame) -> pd.DataFrame`

Generate order line items from orders and products.

**Parameters:**
- `orders_df` (pd.DataFrame): Orders DataFrame
- `products_df` (pd.DataFrame): Products DataFrame

**Returns:**
- `pd.DataFrame`: DataFrame with columns:
  - `order_id` (str)
  - `product_id` (str)
  - `quantity` (int): 1-3 units per item
  - `unit_price` (float)
  - `line_total` (float): quantity × unit_price

#### `generate_all_data(output_dir: str = "data") -> None`

Generate all sample datasets and save to CSV files.

**Parameters:**
- `output_dir` (str): Directory to save CSV files

**Output Files:**
- `sample_customers.csv`
- `sample_products.csv`
- `sample_orders.csv`
- `sample_order_items.csv`

**Example:**
```python
from generate_sample_data import generate_all_data

generate_all_data("data")
```

---

## utils

Common utility functions used across the project.

### Functions

#### `load_config(config_path: str) -> Dict[str, Any]`

Load configuration from JSON or YAML file.

**Parameters:**
- `config_path` (str): Path to configuration file

**Returns:**
- `Dict`: Configuration dictionary

**Raises:**
- `FileNotFoundError`: If config file doesn't exist
- `ValueError`: If file format is unsupported

**Supported Formats:**
- `.json` - JSON configuration
- `.yaml`, `.yml` - YAML configuration

**Example:**
```python
from utils import load_config

config = load_config("config/parameters.json")
catalog = config["databricks"]["catalog"]
```

#### `setup_logging(log_level: str = "INFO") -> None`

Configure logging for the application.

**Parameters:**
- `log_level` (str): Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`)

**Behavior:**
- Configures both console and file logging
- Logs to `logs/pipeline.log`
- Removes existing handlers to allow reconfiguration

**Example:**
```python
from utils import setup_logging

setup_logging("DEBUG")  # Enable debug logging
```

#### `ensure_directory(directory_path: str) -> Path`

Ensure a directory exists, creating it if necessary.

**Parameters:**
- `directory_path` (str): Directory path

**Returns:**
- `Path`: Path object for the directory

**Example:**
```python
from utils import ensure_directory

log_dir = ensure_directory("logs")
```

#### `get_project_root() -> Path`

Get the project root directory.

**Returns:**
- `Path`: Absolute path to project root

**Example:**
```python
from utils import get_project_root

root = get_project_root()
```

---

## Error Handling

All modules implement graceful degradation:

- **Simulation Mode**: If `databricks-sdk` is not installed, functions operate in simulation mode without making API calls
- **Logging**: All operations are logged with appropriate levels (INFO, WARNING, ERROR)
- **Exceptions**: Functions catch and log exceptions, returning sensible defaults

---

## Logging

All modules use Python's standard logging configured via `setup_logging()`.

Logs are written to:
- Console (stdout)
- File: `logs/pipeline.log`

Log format:
```
2025-03-13 10:30:45,123 - module_name - INFO - Message
```

---

## Configuration

Configuration is loaded from:
- `config/parameters.json` (JSON, required)
- `config/env.py` (Python module, for secrets)

See [Configuration Guide](configuration.md) for complete reference.

---

## Simulation Mode

When `databricks-sdk` is not installed, the deployment and pipeline modules operate in simulation mode:

- `deploy_notebook()` returns `True` without uploading
- `monitor_pipeline.PipelineMonitor.run_notebook()` returns simulated results
- Useful for development, testing, and CI/CD without cloud credentials

To enable real operations:
```bash
pip install databricks-sdk
```
