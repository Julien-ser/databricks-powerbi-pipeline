"""
Pipeline execution and monitoring.
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from .utils import setup_logging, ensure_directory, load_config

logger = logging.getLogger(__name__)

# Import databricks-sdk conditionally
try:
    from databricks.sdk import WorkspaceClient
    from databricks.sdk.core import DatabricksError

    DATABRICKS_SDK_AVAILABLE = True
except ImportError:
    DATABRICKS_SDK_AVAILABLE = False
    logger.warning(
        "databricks-sdk not installed. Pipeline execution will be simulated."
    )


class PipelineMonitor:
    """Monitor ETL pipeline execution and send alerts."""

    def __init__(self, config_path: str = "config/parameters.json"):
        """Initialize monitor with configuration."""
        self.config = load_config(config_path)
        self.start_time = None
        self.notebook_results = []
        ensure_directory("logs")

        # Initialize Databricks client if available
        self.client = None
        if DATABRICKS_SDK_AVAILABLE:
            try:
                from config.env import DATABRICKS_HOST, DATABRICKS_TOKEN

                self.client = WorkspaceClient(
                    host=DATABRICKS_HOST, token=DATABRICKS_TOKEN
                )
                logger.info("Connected to Databricks workspace")
            except Exception as e:
                logger.error(f"Failed to connect to Databricks: {e}")
                self.client = None

    def start_run(self) -> None:
        """Mark the start of a pipeline run."""
        self.start_time = datetime.now()
        logger.info("Pipeline run started")

    def run_notebook(self, workspace_path: str, timeout_seconds: int = 3600) -> Dict:
        """
        Execute a single notebook in Databricks workspace.

        Args:
            workspace_path: Path to notebook in workspace (e.g., /Users/.../bronze_ingestion)
            timeout_seconds: Maximum execution time before timeout

        Returns:
            dict: Result with status, execution_time, and other metadata
        """
        if not self.client:
            logger.warning(f"Simulating execution of {workspace_path}")
            return {
                "notebook": workspace_path,
                "status": "SIMULATED",
                "execution_time": 0,
                "error": None,
            }

        try:
            logger.info(f"Executing notebook: {workspace_path}")
            start_time = datetime.now()

            # Run notebook and wait for completion
            # Using workspace.run_notebook (synchronous execution)
            result = self.client.workspace.run_notebook(
                path=workspace_path,
                # Optional: pass parameters if needed
                # parameters={"key": "value"}
            )

            # The result contains run_id, state, etc.
            execution_time = (datetime.now() - start_time).total_seconds()

            status = result.get("result", "UNKNOWN")
            if status == "SUCCESS":
                logger.info(
                    f"Notebook {workspace_path} completed successfully in {execution_time:.2f}s"
                )
            else:
                logger.error(f"Notebook {workspace_path} failed with status {status}")

            return {
                "notebook": workspace_path,
                "status": status,
                "execution_time": execution_time,
                "run_id": result.get("run_id"),
                "error": result.get("error_message"),
            }

        except DatabricksError as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Databricks error executing {workspace_path}: {e}")
            return {
                "notebook": workspace_path,
                "status": "ERROR",
                "execution_time": execution_time,
                "error": str(e),
            }
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Error executing {workspace_path}: {e}")
            return {
                "notebook": workspace_path,
                "status": "ERROR",
                "execution_time": execution_time,
                "error": str(e),
            }

    def run_pipeline(self, notebooks: List[dict]) -> bool:
        """
        Run the full ETL pipeline by executing notebooks in sequence.

        Args:
            notebooks: List of dicts with 'path' and 'name' keys for each notebook

        Returns:
            bool: True if all notebooks succeeded
        """
        self.start_run()
        all_success = True

        for notebook in notebooks:
            result = self.run_notebook(notebook["path"])
            self.notebook_results.append(result)

            if result["status"] not in ["SUCCESS", "SIMULATED"]:
                all_success = False
                logger.error(f"Pipeline stopped due to failure in {notebook['name']}")
                break

        self.end_run(all_success)
        return all_success

    def end_run(self, success: bool) -> None:
        """
        Mark the end of a pipeline run and report status.

        Args:
            success: Whether the pipeline completed successfully
        """
        if self.start_time:
            duration = datetime.now() - self.start_time
            logger.info(f"Pipeline run completed in {duration}")
            logger.info(f"Status: {'SUCCESS' if success else 'FAILED'}")

            # Calculate total metrics
            if self.notebook_results:
                total_execution_time = sum(
                    r.get("execution_time", 0) for r in self.notebook_results
                )
                successful = sum(
                    1
                    for r in self.notebook_results
                    if r.get("status") in ["SUCCESS", "SIMULATED"]
                )
                total = len(self.notebook_results)
                logger.info(
                    f"Metrics: {successful}/{total} notebooks succeeded, total time: {total_execution_time:.2f}s"
                )

                # Detailed results
                for result in self.notebook_results:
                    status = result.get("status")
                    if status == "SUCCESS":
                        logger.info(
                            f"  ✓ {result['notebook']} ({result['execution_time']:.2f}s)"
                        )
                    elif status == "SIMULATED":
                        logger.info(f"  ○ {result['notebook']} (simulated)")
                    else:
                        logger.error(
                            f"  ✗ {result['notebook']} - {result.get('error', 'Unknown error')}"
                        )

            # Send alerts if configured and pipeline failed
            if not success and self.config.get("send_alerts", False):
                self._send_alert(f"Pipeline failed after {duration}")

    def _send_alert(self, message: str) -> None:
        """Send alert notification (to be implemented)."""
        # TODO: Implement email, Slack, or other notification methods
        logger.warning(f"ALERT: {message}")


def run_etl_pipeline() -> bool:
    """
    Execute the full ETL pipeline: bronze -> silver -> gold.

    Returns:
        bool: True if pipeline succeeded
    """
    setup_logging()
    ensure_directory("logs")

    monitor = PipelineMonitor()

    # Define pipeline notebooks in execution order
    pipeline_notebooks = [
        {
            "name": "Bronze Ingestion",
            "path": "/Users/default/01_bronze/bronze_ingestion",
        },
        {
            "name": "Silver Transformation",
            "path": "/Users/default/02_silver/silver_transformation",
        },
        {"name": "Gold Aggregation", "path": "/Users/default/03_gold/gold_aggregation"},
    ]

    logger.info("Starting ETL pipeline execution")
    success = monitor.run_pipeline(pipeline_notebooks)

    if success:
        logger.info("ETL pipeline completed successfully")
    else:
        logger.error("ETL pipeline failed")

    return success


if __name__ == "__main__":
    success = run_etl_pipeline()
    sys.exit(0 if success else 1)
