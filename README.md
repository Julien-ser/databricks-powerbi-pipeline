# Databricks Power BI Pipeline

**End-to-end analytics solution connecting Databricks to Power BI for e-commerce analytics.**

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
# Edit config/env.py with your credentials

# Run tests
python -m pytest tests/

# Deploy notebooks to Databricks
python src/deploy_notebooks.py
```

### Using the Pipeline

1. **Ingest Data**: Upload sample e-commerce CSV files to your Databricks workspace
2. **Run ETL**: Execute notebooks in order: bronze → silver → gold
3. **Connect Power BI**: Use DirectQuery to connect to the gold Delta table
4. **Build Reports**: Create custom dashboards from the processed data

## Project Structure

```
databricks-powerbi-pipeline/
├── notebooks/
│   ├── 01_bronze/          # Raw data ingestion
│   ├── 02_silver/          # Data cleaning
│   └── 03_gold/            # Business aggregates
├── src/
│   ├── deploy_notebooks.py
│   ├── monitor_pipeline.py
│   └── utils.py
├── data/
│   ├── sample_orders.csv
│   ├── sample_customers.csv
│   └── sample_products.csv
├── config/
│   ├── env.example.py
│   └── parameters.json
├── tests/
│   ├── unit/
│   └── integration/
├── docs/
│   ├── architecture.md
│   └── deployment.md
├── requirements.txt
├── README.md
└── TASKS.md
```

## Sample Data

The project includes synthetic e-commerce data:
- **Orders**: Transaction records with timestamps, amounts, status
- **Customers**: Demographics and segmentation data
- **Products**: Catalog with categories and pricing

## Power BI Integration

After processing data through the Delta Lake pipeline:
1. Get your Databricks workspace URL and token
2. In Power BI Desktop: Get Data → Databricks
3. Enter server and database name pointing to gold Delta table
4. Use DirectQuery mode for real-time dashboard updates
5. Build visuals for sales trends, customer segmentation, product performance

## Testing

```bash
# Unit tests
pytest tests/unit/

# Integration tests (requires Databricks connection)
pytest tests/integration/

# Full test suite with coverage
pytest --cov=src tests/
```

## Development Status

See [TASKS.md](TASKS.md) for current progress and upcoming work.

## Documentation

- [Architecture Guide](docs/architecture.md)
- [Deployment Guide](docs/deployment.md)
- [Power BI Setup](docs/powerbi-setup.md)

## Contributing

1. Check TASKS.md for current priorities
2. Create feature branch from main
3. Add tests for new functionality
4. Submit changes with clear commit messages

## License

MIT License - see LICENSE file for details.
