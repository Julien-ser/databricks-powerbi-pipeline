"""
Deploy notebooks to Databricks workspace.
"""

import logging
import os
import sys
from pathlib import Path

# Add project root to path for config import
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.env import DATABRICKS_HOST, DATABRICKS_TOKEN
from .utils import setup_logging, ensure_directory

logger = logging.getLogger(__name__)

# Import databricks-sdk conditionally to handle missing dependency
try:
    from databricks.sdk import WorkspaceClient
    from databricks.sdk.core import DatabricksError

    DATBRICKS_SDK_AVAILABLE = True
except ImportError:
    DATBRICKS_SDK_AVAILABLE = False
    logger.warning("databricks-sdk not installed. Deployment will be simulated.")


def deploy_notebook(notebook_path: str, workspace_path: str, client=None) -> bool:
    """
    Deploy a single notebook to Databricks workspace.

    Args:
        notebook_path: Local path to the notebook file
        workspace_path: Target path in Databricks workspace
        client: Optional WorkspaceClient instance

    Returns:
        bool: True if deployment succeeded
    """
    try:
        notebook_file = Path(notebook_path)
        if not notebook_file.exists():
            logger.error(f"Notebook file not found: {notebook_path}")
            return False

        logger.info(f"Deploying {notebook_path} to {workspace_path}")

        # If databricks-sdk is not available, simulate deployment
        if not DATBRICKS_SDK_AVAILABLE:
            logger.warning("Running in simulation mode (databricks-sdk not installed)")
            return True

        # Initialize client if not provided
        if client is None:
            client = WorkspaceClient(host=DATABRICKS_HOST, token=DATABRICKS_TOKEN)

        # Read notebook content
        with open(notebook_path, "rb") as f:
            content = f.read()

        # Determine notebook format (ipynb) and language (PYTHON)
        # Databricks workspace import_notebook API
        try:
            # Try to import as workspace notebook
            client.workspace.import_notebook(
                path=workspace_path,
                content=content,
                format="SOURCE",  # For .ipynb files
                language="PYTHON",
            )
        except Exception as e:
            # Fallback: try using the workspace import API
            logger.warning(f"Primary import failed: {e}, trying alternative method")
            client.workspace.import_workspace_notebook(
                path=workspace_path,
                content=content,
                format="DBC",  # or AUTO
            )

        logger.info(f"Successfully deployed: {workspace_path}")
        return True

    except DatabricksError as e:
        logger.error(f"Databricks API error deploying {notebook_path}: {e}")
        return False
    except Exception as e:
        logger.error(f"Failed to deploy notebook {notebook_path}: {e}")
        return False


def deploy_all_notebooks(notebooks_dir: str = "notebooks") -> bool:
    """
    Deploy all notebooks to Databricks workspace in order.

    Args:
        notebooks_dir: Local directory containing notebook folders
    """
    setup_logging()
    ensure_directory("logs")

    logger.info("Starting notebook deployment")

    # Initialize client if databricks-sdk is available
    client = None
    if DATBRICKS_SDK_AVAILABLE:
        try:
            client = WorkspaceClient(host=DATABRICKS_HOST, token=DATABRICKS_TOKEN)
            logger.info("Connected to Databricks workspace")
        except Exception as e:
            logger.error(f"Failed to connect to Databricks: {e}")
            logger.warning("Proceeding in simulation mode")
            client = None

    # Define deployment order
    layers = ["01_bronze", "02_silver", "03_gold"]
    notebooks_path = Path(notebooks_dir)

    success_count = 0
    total_count = 0

    for layer in layers:
        layer_path = notebooks_path / layer
        if not layer_path.exists():
            logger.warning(f"Layer directory not found: {layer_path}")
            continue

        # Deploy notebooks in this layer
        for notebook_file in layer_path.glob("*.ipynb"):
            total_count += 1
            # Construct workspace path: /Users/<username>/<layer>/<notebook_name>
            # Use a generic path if os.getlogin() fails
            try:
                username = os.getlogin()
            except OSError:
                username = "default"
            workspace_path = f"/Users/{username}/{layer}/{notebook_file.stem}"

            success = deploy_notebook(str(notebook_file), workspace_path, client)
            if success:
                logger.info(f"Successfully deployed: {workspace_path}")
                success_count += 1
            else:
                logger.error(f"Failed to deploy: {workspace_path}")

    logger.info(
        f"Notebook deployment complete: {success_count}/{total_count} succeeded"
    )

    if success_count < total_count:
        logger.warning("Some notebooks failed to deploy. Check logs for details.")
        return False
    return True


if __name__ == "__main__":
    deploy_all_notebooks()
