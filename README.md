# Databricks Power BI Pipeline

**Production-ready end-to-end analytics solution connecting Databricks to Power BI for e-commerce analytics.**

**Status: Phase 3 (Testing) Complete ✅**

## Overview

This project provides a production-ready pipeline that transforms raw e-commerce data into actionable Power BI dashboards using Databricks as the analytics engine.

### Problem Statement
Organizations need to analyze e-commerce data (orders, customers, products) to make data-driven decisions about inventory, marketing, and customer experience.

### Solution
Automated ETL pipeline with:
- Bronze layer: Raw data ingestion
- Silver layer: Cleaned and validated data
- Gold layer: Business-level aggregates for reporting
- Power BI integration with DirectQuery for real-time analytics

## Architecture

```
Data Sources → Databricks (ETL) → Delta Tables → Power BI → Dashboards
     ↓              ↓              ↓           ↓          ↓
  CSV/API     Notebooks    Optimized   DirectQuery   KPIs &
              (PySpark)     Layer                   Reports
```

### Components

- **notebooks/** - Databricks notebooks (bronze, silver, gold transformations)
- **src/** - Python automation scripts for deployment and monitoring
- **data/** - Sample datasets and schema definitions
- **config/** - Configuration files for environments
- **tests/** - Unit and integration tests
- **docs/** - Architecture and deployment guides

## Quick Start

### Prerequisites
- Databricks workspace (Community Edition or paid)
- Power BI Desktop (free) or Power BI Premium
- Python 3.8+ with pip

### Setup

```bash
# Clone and navigate
cd databricks-powerbi-pipeline

# Install dependencies
pip install -r requirements.txt

# Configure Databricks connection
cp config/env.example.py config/env.py
# Edit config/env.py with your credentials (DATABRICKS_HOST and DATABRICKS_TOKEN)

# Optional: Generate sample data (or upload your own)
python src/generate_sample_data.py

# Run tests (unit and integration)
python -m pytest tests/

# Deploy notebooks to Databricks workspace
python src/deploy_notebooks.py

# Execute the ETL pipeline (bronze → silver → gold)
python src/monitor_pipeline.py
```

### Using the Pipeline

**Quickest path to production:**

1. **Configure & Deploy**:
   - Set your Databricks credentials in `config/env.py`
   - Run `python src/deploy_notebooks.py` to upload notebooks to workspace
   - Upload sample data to `/mnt/data/raw/` in your Databricks workspace

2. **Execute ETL**:
   - Run `python src/monitor_pipeline.py` to execute the full pipeline
   - The script runs bronze → silver → gold notebooks automatically
   - Monitor logs in `logs/pipeline.log` for progress

3. **Connect Power BI**:
   - Follow the [Power BI Setup Guide](docs/powerbi-setup.md)
   - Connect to gold Delta tables using DirectQuery
   - Import the data model and build reports

4. **Schedule** (optional):
   - Use `monitor_pipeline.py` in a scheduled job for regular refreshes
   - Set up alerts via email or Slack (configure in `config/env.py`)

## Project Structure

```
databricks-powerbi-pipeline/
├── notebooks/                    # Databricks ETL notebooks (Medallion Architecture)
│   ├── 01_bronze/
│   │   └── bronze_ingestion.ipynb      # Raw data → Delta bronze tables
│   ├── 02_silver/
│   │   └── silver_transformation.ipynb # Cleaned data → Delta silver tables
│   └── 03_gold/
│       └── gold_aggregation.ipynb      # Business aggregates → Delta gold tables
├── src/                          # Python automation scripts
│   ├── deploy_notebooks.py       # Deploy notebooks to Databricks
│   ├── monitor_pipeline.py       # Execute pipeline with monitoring
│   ├── generate_sample_data.py   # Generate synthetic e-commerce data
│   └── utils.py                  # Shared utilities (logging, config, etc.)
├── data/                         # Sample datasets (CSV format)
│   ├── sample_customers.csv
│   ├── sample_products.csv
│   ├── sample_orders.csv
│   └── sample_order_items.csv
├── config/                       # Configuration files
│   ├── env.py                    # Environment credentials (gitignored)
│   ├── env.example.py            # Template for env.py
│   └── parameters.json           # Pipeline parameters (paths, catalog, etc.)
├── tests/                        # Automated tests
│   ├── unit/                     # Unit tests (utils, data generation)
│   │   ├── test_utils.py
│   │   └── test_data_generation.py
│   └── integration/              # Integration tests (end-to-end)
│       └── test_integration.py
├── docs/                         # Documentation
│   ├── architecture.md           # System design and architecture
│   ├── deployment.md             # Step-by-step deployment guide
│   └── powerbi-setup.md          # Power BI connection and dashboard setup
├── logs/                         # Pipeline execution logs (auto-generated)
├── requirements.txt              # Python dependencies
├── README.md                     # This file
└── TASKS.md                      # Project roadmap and progress tracking
```

## Sample Data

The project includes synthetic e-commerce data:
- **Orders**: Transaction records with timestamps, amounts, status
- **Customers**: Demographics and segmentation data
- **Products**: Catalog with categories and pricing

## Power BI Integration

After processing data through the Delta Lake pipeline, connect Power BI for analytics. See the **[Power BI Setup Guide](docs/powerbi-setup.md)** for detailed instructions.

**Quick steps:**
1. Get your Databricks workspace URL and token
2. In Power BI Desktop: Get Data → Databricks
3. Enter server and database name pointing to gold Delta table
4. Use DirectQuery mode for real-time dashboard updates
5. Build visuals for sales trends, customer segmentation, product performance

Or, for step-by-step instructions with screenshots, follow the complete guide in `docs/powerbi-setup.md`.

## Testing

The project includes comprehensive tests:

```bash
# Unit tests (fast, no external dependencies)
pytest tests/unit/

# Integration tests (run in simulation mode by default, no Databricks required)
pytest tests/integration/

# Full test suite with coverage report
pytest --cov=src tests/
```

**Note:** Integration tests run in *simulation mode* when databricks-sdk is not installed, making them suitable for CI/CD and local development without cloud credentials. To test against a real Databricks workspace, install `databricks-sdk` and configure your credentials.

## Development Status

See [TASKS.md](TASKS.md) for current progress and upcoming work.

## Documentation

- [Architecture Guide](docs/architecture.md)
- [Deployment Guide](docs/deployment.md)
- [Power BI Setup](docs/powerbi-setup.md)
- [API Reference](docs/api-reference.md)
- [Configuration Reference](docs/configuration.md)
- [Monitoring & Operations](docs/monitoring.md)
- [Data Dictionary](docs/data-dictionary.md)
- [Contributing Guide](CONTRIBUTING.md)

## Contributing

1. Check TASKS.md for current priorities
2. Create feature branch from main
3. Add tests for new functionality
4. Submit changes with clear commit messages

## License

MIT License - see LICENSE file for details.
