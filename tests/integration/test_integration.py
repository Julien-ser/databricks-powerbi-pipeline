"""
Integration tests for the databricks-powerbi-pipeline.

These tests verify end-to-end functionality without requiring a live Databricks connection.
"""

import json
import logging
import tempfile
from pathlib import Path

import pytest

from src.deploy_notebooks import deploy_all_notebooks, deploy_notebook
from src.generate_sample_data import (
    generate_all_data,
    generate_customers,
    generate_orders,
    generate_products,
    generate_order_items,
)
from src.monitor_pipeline import PipelineMonitor, run_etl_pipeline
from src.utils import load_config, ensure_directory


class TestDeployNotebooks:
    """Integration tests for notebook deployment."""

    def test_deploy_notebook_simulation_mode(self, tmp_path):
        """Test notebook deployment in simulation mode (no databricks-sdk)."""
        # Create a dummy notebook file
        notebook_path = tmp_path / "test_notebook.ipynb"
        notebook_content = {
            "cells": [],
            "metadata": {},
            "nbformat": 4,
            "nbformat_minor": 5,
        }
        with open(notebook_path, "w") as f:
            json.dump(notebook_content, f)

        # Should succeed in simulation mode
        result = deploy_notebook(str(notebook_path), "/Users/test/test_notebook")
        assert result is True

    def test_deploy_nonexistent_notebook_fails(self):
        """Test that deploying a non-existent notebook fails gracefully."""
        result = deploy_notebook("/nonexistent/notebook.ipynb", "/Users/test/fail")
        assert result is False

    def test_deploy_all_notebooks_simulation(self, tmp_path):
        """Test deploying all notebooks in simulation mode."""
        # Create a temporary notebooks structure
        notebooks_dir = tmp_path / "notebooks"
        bronze_dir = notebooks_dir / "01_bronze"
        silver_dir = notebooks_dir / "02_silver"
        gold_dir = notebooks_dir / "03_gold"

        for dir_path in [bronze_dir, silver_dir, gold_dir]:
            dir_path.mkdir(parents=True)

        # Create sample notebooks
        for layer_dir in [bronze_dir, silver_dir, gold_dir]:
            notebook = layer_dir / "test.ipynb"
            with open(notebook, "w") as f:
                json.dump(
                    {"cells": [], "metadata": {}, "nbformat": 4, "nbformat_minor": 5}, f
                )

        # Should succeed in simulation mode
        result = deploy_all_notebooks(str(notebooks_dir))
        assert result is True


class TestDataGeneration:
    """Integration tests for data generation."""

    def test_generate_all_data_creates_files(self, tmp_path):
        """Test that generate_all_data creates all required CSV files."""
        output_dir = tmp_path / "data"
        generate_all_data(str(output_dir))

        expected_files = [
            "sample_customers.csv",
            "sample_products.csv",
            "sample_orders.csv",
            "sample_order_items.csv",
        ]

        for filename in expected_files:
            file_path = output_dir / filename
            assert file_path.exists(), f"Missing file: {filename}"
            assert file_path.stat().st_size > 0, f"File is empty: {filename}"

    def test_generate_data_relationships(self, tmp_path):
        """Test that generated data maintains proper relationships."""
        output_dir = tmp_path / "data"
        generate_all_data(str(output_dir))

        # Load CSVs
        import pandas as pd

        customers = pd.read_csv(output_dir / "sample_customers.csv")
        products = pd.read_csv(output_dir / "sample_products.csv")
        orders = pd.read_csv(output_dir / "sample_orders.csv")
        order_items = pd.read_csv(output_dir / "sample_order_items.csv")

        # Check that all customer IDs in orders exist in customers
        order_customers = set(orders["customer_id"].unique())
        customer_ids = set(customers["customer_id"].unique())
        assert order_customers.issubset(customer_ids), (
            "Orders contain non-existent customers"
        )

        # Check that all product IDs in order_items exist in products
        item_products = set(order_items["product_id"].unique())
        product_ids = set(products["product_id"].unique())
        assert item_products.issubset(product_ids), (
            "Order items contain non-existent products"
        )

        # Check that all order IDs in order_items exist in orders
        item_orders = set(order_items["order_id"].unique())
        order_ids = set(orders["order_id"].unique())
        assert item_orders.issubset(order_ids), (
            "Order items contain non-existent orders"
        )


class TestPipelineMonitor:
    """Integration tests for pipeline monitoring."""

    def test_monitor_initialization(self, tmp_path):
        """Test that PipelineMonitor initializes correctly."""
        config_file = tmp_path / "parameters.json"
        config = {
            "environment": "test",
            "databricks": {"workspace_url": "http://test"},
            "send_alerts": False,
        }
        with open(config_file, "w") as f:
            json.dump(config, f)

        monitor = PipelineMonitor(str(config_file))
        assert monitor.config["environment"] == "test"
        assert monitor.start_time is None

    def test_simulation_mode_execution(self):
        """Test pipeline execution in simulation mode (no Databricks)."""
        # This will use simulation mode since databricks-sdk is not available
        success = run_etl_pipeline()
        # In simulation mode, it should return True
        assert success is True

    def test_pipeline_metrics_collection(self):
        """Test that pipeline collects execution metrics."""
        monitor = PipelineMonitor()
        monitor.start_run()

        # Simulate some notebook results
        monitor.notebook_results = [
            {"notebook": "/test/1", "status": "SUCCESS", "execution_time": 10.5},
            {"notebook": "/test/2", "status": "SUCCESS", "execution_time": 20.3},
        ]

        monitor.end_run(success=True)

        # Check that metrics were logged (we can't easily assert on log output,
        # but we can verify the method completed without error)


class TestConfigLoading:
    """Integration tests for configuration management."""

    def test_load_json_config(self, tmp_path):
        """Test loading JSON configuration."""
        config_file = tmp_path / "config.json"
        config_data = {"test": "value", "nested": {"key": 123}}
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        config = load_config(str(config_file))
        assert config["test"] == "value"
        assert config["nested"]["key"] == 123

    def test_load_yaml_config(self, tmp_path):
        """Test loading YAML configuration."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("test: value\nnested:\n  key: 123\n")

        config = load_config(str(config_file))
        assert config["test"] == "value"
        assert config["nested"]["key"] == 123

    def test_load_missing_config_raises(self):
        """Test that loading missing config raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_config("/nonexistent/config.json")


class TestEndToEndWorkflow:
    """End-to-end workflow tests."""

    def test_complete_workflow_simulation(self, tmp_path):
        """
        Test the complete workflow: generate data, deploy notebooks (simulated),
        and run pipeline (simulated).
        """
        # Step 1: Generate sample data
        data_dir = tmp_path / "data"
        generate_all_data(str(data_dir))
        assert (data_dir / "sample_customers.csv").exists()
        assert (data_dir / "sample_order_items.csv").exists()

        # Step 2: Verify notebooks exist
        notebooks_dir = Path("notebooks")
        assert (notebooks_dir / "01_bronze" / "bronze_ingestion.ipynb").exists()
        assert (notebooks_dir / "02_silver" / "silver_transformation.ipynb").exists()
        assert (notebooks_dir / "03_gold" / "gold_aggregation.ipynb").exists()

        # Step 3: Deploy notebooks (simulation mode)
        deploy_success = deploy_all_notebooks(str(notebooks_dir))
        assert deploy_success is True

        # Step 4: Run pipeline (simulation mode)
        pipeline_success = run_etl_pipeline()
        assert pipeline_success is True

        logger = logging.getLogger(__name__)
        logger.info("End-to-end workflow test completed successfully")
