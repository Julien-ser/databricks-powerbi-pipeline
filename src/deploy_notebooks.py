"""
Deploy notebooks to Databricks workspace.
"""

import logging
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.env import DATABRICKS_HOST, DATABRICKS_TOKEN
from utils import setup_logging, ensure_directory

logger = logging.getLogger(__name__)


def deploy_notebook(notebook_path: str, workspace_path: str) -> bool:
    """
    Deploy a single notebook to Databricks workspace.

    Args:
        notebook_path: Local path to the notebook file
        workspace_path: Target path in Databricks workspace

    Returns:
        bool: True if deployment succeeded
    """
    try:
        # Implementation would use databricks-sdk
        logger.info(f"Deploying {notebook_path} to {workspace_path}")
        # TODO: Implement actual deployment using databricks-sdk
        return True
    except Exception as e:
        logger.error(f"Failed to deploy notebook {notebook_path}: {e}")
        return False


def deploy_all_notebooks(notebooks_dir: str = "notebooks") -> None:
    """
    Deploy all notebooks to Databricks workspace in order.

    Args:
        notebooks_dir: Local directory containing notebook folders
    """
    setup_logging()
    ensure_directory("logs")

    logger.info("Starting notebook deployment")

    # Define deployment order
    layers = ["01_bronze", "02_silver", "03_gold"]
    notebooks_path = Path(notebooks_dir)

    for layer in layers:
        layer_path = notebooks_path / layer
        if not layer_path.exists():
            logger.warning(f"Layer directory not found: {layer_path}")
            continue

        # Deploy notebooks in this layer
        for notebook_file in layer_path.glob("*.ipynb"):
            workspace_path = f"/Users/{os.getlogin()}/{layer}/{notebook_file.stem}"
            success = deploy_notebook(str(notebook_file), workspace_path)
            if success:
                logger.info(f"Successfully deployed: {workspace_path}")
            else:
                logger.error(f"Failed to deploy: {workspace_path}")

    logger.info("Notebook deployment complete")


if __name__ == "__main__":
    deploy_all_notebooks()
