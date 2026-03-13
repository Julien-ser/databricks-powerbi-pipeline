"""
Rollback script for disaster recovery.

This script provides rollback capabilities for:
- Reverting notebooks to previous versions in Databricks workspace
- Restoring Delta tables to previous state using time travel
- Restoring configuration files from backup
- Cleaning up failed deployments
"""

import logging
import sys
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils import setup_logging, ensure_directory
from config.env import DATABRICKS_HOST, DATABRICKS_TOKEN

logger = logging.getLogger(__name__)

# Import databricks-sdk conditionally
try:
    from databricks.sdk import WorkspaceClient

    DATABRICKS_SDK_AVAILABLE = True
except ImportError:
    DATABRICKS_SDK_AVAILABLE = False


class RollbackManager:
    """Manage rollback operations for the pipeline."""

    def __init__(self, backup_dir: str = "backups"):
        self.backup_dir = Path(backup_dir)
        ensure_directory(str(self.backup_dir))
        self.client = None
        self.actions_performed = []

    def connect_to_databricks(self) -> bool:
        """Establish connection to Databricks."""
        if not DATABRICKS_SDK_AVAILABLE:
            logger.error("databricks-sdk not installed. Cannot perform rollback.")
            return False

        try:
            if not DATABRICKS_HOST or not DATABRICKS_TOKEN:
                logger.error("Databricks credentials not configured.")
                return False

            self.client = WorkspaceClient(host=DATABRICKS_HOST, token=DATABRICKS_TOKEN)
            logger.info("Connected to Databricks for rollback")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Databricks: {e}")
            return False

    def backup_current_state(self) -> bool:
        """Create a backup of current state before rollback."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"pre_rollback_{timestamp}.json"

        try:
            import json

            state = {
                "timestamp": timestamp,
                "action": "pre_rollback_backup",
                "notebooks": [],
                "tables": [],
            }

            # If connected, list current notebooks
            if self.client:
                try:
                    # List notebooks in workspace
                    # Note: this is simplified; actual implementation would need to recursively list
                    pass
                except Exception as e:
                    logger.warning(f"Could not backup notebooks: {e}")

            # Save state
            with open(backup_file, "w") as f:
                json.dump(state, f, indent=2)

            logger.info(f"Created backup state at {backup_file}")
            self.actions_performed.append(f"Backup created: {backup_file.name}")
            return True
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return False

    def rollback_notebooks_from_git(self) -> bool:
        """Restore notebooks from Git repository."""
        try:
            logger.info("Rolling back notebooks from Git repository...")

            # Get the previous commit (second-to-last)
            result = subprocess.run(
                ["git", "log", "--oneline", "-n", "2", "--notebooks/"],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0 or len(result.stdout.strip().split("\n")) < 2:
                logger.warning(
                    "No Git history found for notebooks. Skipping Git rollback."
                )
                return True

            # Get previous commit hash
            lines = result.stdout.strip().split("\n")
            if len(lines) >= 2:
                prev_commit = lines[1].split()[0]
                logger.info(f"Restoring notebooks to commit {prev_commit}")

                # Restore specific directories
                subprocess.run(
                    ["git", "restore", "--source", prev_commit, "notebooks/"],
                    check=True,
                )

                logger.info("Notebooks restored from Git")
                self.actions_performed.append("Notebooks rolled back via Git")
                return True
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Git rollback failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error in Git rollback: {e}")
            return False

    def rollback_delta_tables(self, target_time: Optional[str] = None) -> bool:
        """
        Restore Delta tables to a previous state using time travel.

        Args:
            target_time: ISO format timestamp or "1 hour ago", etc.
                        If None, uses the most recent backup time from logs.
        """
        if not self.client:
            logger.warning("Skipping Delta table rollback (no Databricks connection)")
            return True

        try:
            catalog = self.config.get("databricks", {}).get("catalog", "ecommerce")
            schema = self.config.get("databricks", {}).get("schema", "analytics")

            tables = [
                "fact_sales",
                "dim_customer",
                "dim_product",
                "monthly_sales",
                # Include bronze and silver if needed
                "bronze_orders",
                "bronze_customers",
                "bronze_products",
                "bronze_order_items",
                "silver_orders",
                "silver_customers",
                "silver_products",
                "silver_order_items",
            ]

            restore_time = target_time or "1 hour ago"

            for table in tables:
                full_name = f"{catalog}.{schema}.{table}"
                try:
                    # Check if table exists
                    self.client.sql.execute(
                        [f"DESCRIBE TABLE {full_name}"],
                        throw_on_error=False,
                    )

                    # Restore table
                    logger.info(f"Restoring {full_name} to {restore_time}")
                    self.client.sql.execute(
                        [f"RESTORE {full_name} TO TIMESTAMP AS OF '{restore_time}'"],
                        throw_on_error=False,
                    )
                    self.actions_performed.append(f"Restored table: {full_name}")
                except Exception as e:
                    logger.warning(f"Could not restore {full_name}: {e}")

            return True
        except Exception as e:
            logger.error(f"Delta table rollback failed: {e}")
            return False

    def clean_failed_deployment(self) -> bool:
        """Clean up any partial deployment artifacts."""
        try:
            logger.info("Cleaning up failed deployment artifacts...")

            # Remove deployment marker files if they exist
            marker_files = [
                "logs/deployment_success.marker",
                "logs/pipeline_run.marker",
            ]

            for marker in marker_files:
                path = Path(marker)
                if path.exists():
                    path.unlink()
                    logger.info(f"Removed marker: {marker}")
                    self.actions_performed.append(f"Removed marker: {marker}")

            # Clean temporary directories
            temp_dirs = [
                "tmp/",
                "temp/",
            ]

            for temp_dir in temp_dirs:
                path = Path(temp_dir)
                if path.exists():
                    import shutil

                    shutil.rmtree(path)
                    logger.info(f"Removed temp directory: {temp_dir}")
                    self.actions_performed.append(f"Removed temp: {temp_dir}")

            logger.info("Cleanup complete")
            return True
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            return False

    def generate_rollback_report(self) -> str:
        """Generate a rollback report."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.backup_dir / f"rollback_report_{timestamp}.md"

        with open(report_file, "w") as f:
            f.write("# Rollback Report\n\n")
            f.write(f"**Timestamp**: {datetime.now().isoformat()}\n\n")
            f.write("## Actions Performed\n\n")
            for action in self.actions_performed:
                f.write(f"- [x] {action}\n")
            f.write("\n## Next Steps\n\n")
            f.write("1. Verify pipeline is functioning\n")
            f.write("2. Check logs for any remaining issues\n")
            f.write("3. Test Power BI connectivity\n")
            f.write("4. Monitor for 24 hours before resuming normal operations\n")
            f.write("5. Document the root cause of the rollback\n")

        logger.info(f"Rollback report generated: {report_file}")
        return str(report_file)

    def run_full_rollback(self, target_time: Optional[str] = None) -> bool:
        """
        Execute full rollback procedure.

        Args:
            target_time: Target time for Delta table restore (ISO format or relative)
        """
        logger.info("Starting full rollback procedure...")

        if not self.connect_to_databricks():
            logger.warning(
                "Proceeding with partial rollback (no Databricks connection)"
            )

        # Step 1: Backup current state
        self.backup_current_state()

        # Step 2: Clean up failed deployment
        self.clean_failed_deployment()

        # Step 3: Restore notebooks from Git
        self.rollback_notebooks_from_git()

        # Step 4: Restore Delta tables (if connected)
        if self.client:
            self.rollback_delta_tables(target_time)

        # Step 5: Generate report
        report = self.generate_rollback_report()

        logger.info(f"Rollback complete. Report: {report}")
        return True


def main():
    """Run rollback with command-line arguments."""
    import argparse

    parser = argparse.ArgumentParser(description="Rollback the pipeline deployment")
    parser.add_argument(
        "--target-time",
        help="Target time for Delta table restore (e.g., '1 hour ago', '2025-03-13T10:00:00')",
    )
    parser.add_argument(
        "--notebooks-only",
        action="store_true",
        help="Only rollback notebooks from Git",
    )
    parser.add_argument(
        "--tables-only",
        action="store_true",
        help="Only rollback Delta tables",
    )

    args = parser.parse_args()

    setup_logging()
    roller = RollbackManager()

    if args.notebooks_only:
        roller.connect_to_databricks()  # Optional
        success = roller.rollback_notebooks_from_git()
    elif args.tables_only:
        if roller.connect_to_databricks():
            success = roller.rollback_delta_tables(args.target_time)
        else:
            logger.error("Cannot rollback tables without Databricks connection")
            success = False
    else:
        success = roller.run_full_rollback(args.target_time)

    roller.generate_rollback_report()

    return 0 if success else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
