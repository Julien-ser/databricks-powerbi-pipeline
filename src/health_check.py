"""
Health check script for production deployment validation.

This script performs comprehensive health checks on the deployed pipeline:
- Databricks connectivity
- Delta table existence and freshness
- Configuration validity
- Storage accessibility
- Recent execution status
"""

import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.env import DATABRICKS_HOST, DATABRICKS_TOKEN
from src.utils import setup_logging, load_config

logger = logging.getLogger(__name__)

# Import databricks-sdk conditionally
try:
    from databricks.sdk import WorkspaceClient
    from databricks.sdk.core import DatabricksError

    DATABRICKS_SDK_AVAILABLE = True
except ImportError:
    DATABRICKS_SDK_AVAILABLE = False


class HealthCheck:
    """Perform health checks on the deployed pipeline."""

    def __init__(self):
        self.client = None
        self.config = None
        self.issues = []
        self.warnings = []
        self.passed = []

    def load_configuration(self) -> bool:
        """Load and validate configuration."""
        try:
            self.config = load_config("config/parameters.json")
            self.passed.append("Configuration loaded successfully")
            return True
        except Exception as e:
            self.issues.append(f"Failed to load configuration: {e}")
            return False

    def check_databricks_connection(self) -> bool:
        """Test connection to Databricks."""
        if not DATABRICKS_SDK_AVAILABLE:
            self.warnings.append(
                "databricks-sdk not installed - cannot test connection"
            )
            return True

        try:
            if not DATABRICKS_HOST or not DATABRICKS_TOKEN:
                self.warnings.append("Databricks credentials not configured")
                return True

            self.client = WorkspaceClient(host=DATABRICKS_HOST, token=DATABRICKS_TOKEN)
            me = self.client.current_user.me()
            self.passed.append(f"Connected to Databricks as {me.user_name}")
            return True
        except Exception as e:
            self.issues.append(f"Failed to connect to Databricks: {e}")
            return False

    def check_delta_tables(self) -> bool:
        """Verify expected Delta tables exist."""
        if not self.client:
            self.warnings.append(
                "Skipping Delta table checks (no Databricks connection)"
            )
            return True

        try:
            # Get catalog and schema from config
            catalog = self.config.get("databricks", {}).get("catalog", "ecommerce")
            schema = self.config.get("databricks", {}).get("schema", "analytics")

            # Expected gold tables
            expected_tables = [
                "fact_sales",
                "dim_customer",
                "dim_product",
                "monthly_sales",
            ]

            # Query to list tables
            query = f"SHOW TABLES IN {catalog}.{schema}"
            result = self.client.sql.execute([query])

            existing_tables = [row.tableName for row in result]

            for table in expected_tables:
                if table in existing_tables:
                    self.passed.append(f"Table exists: {catalog}.{schema}.{table}")
                else:
                    self.issues.append(f"Missing table: {catalog}.{schema}.{table}")

            return len(self.issues) == 0 or all(
                "Missing table" not in issue for issue in self.issues
            )
        except Exception as e:
            self.issues.append(f"Failed to check Delta tables: {e}")
            return False

    def check_table_freshness(self) -> bool:
        """Check if tables have recent data."""
        if not self.client:
            self.warnings.append("Skipping freshness checks (no Databricks connection)")
            return True

        try:
            catalog = self.config.get("databricks", {}).get("catalog", "ecommerce")
            schema = self.config.get("databricks", {}).get("schema", "analytics")

            # Check fact_sales for recent data (last 7 days)
            query = f"""
            SELECT MAX(order_date) as latest_date,
                   COUNT(*) as total_rows
            FROM {catalog}.{schema}.fact_sales
            """
            result = self.client.sql.execute([query])
            row = list(result)[0]

            latest_date = row.latest_date
            total_rows = row.total_rows

            if latest_date:
                days_old = (datetime.now().date() - latest_date).days
                if days_old <= 7:
                    self.passed.append(
                        f"fact_sales is fresh: {total_rows} rows, latest: {latest_date}"
                    )
                else:
                    self.warnings.append(
                        f"fact_sales data is {days_old} days old (latest: {latest_date})"
                    )
            else:
                self.warnings.append("fact_sales has no data")

            return True
        except Exception as e:
            self.issues.append(f"Failed to check table freshness: {e}")
            return False

    def check_storage_access(self) -> bool:
        """Verify storage paths are accessible."""
        try:
            paths = self.config.get("data", {})
            gold_path = paths.get("gold_path", "/mnt/gold/ecommerce")

            if not self.client:
                self.warnings.append(f"Skipping storage check for: {gold_path}")
                return True

            # Try to list files in gold path
            try:
                self.client.dbutils.fs.ls(gold_path)
                self.passed.append(f"Storage accessible: {gold_path}")
            except Exception as e:
                self.warnings.append(f"Could not access storage path {gold_path}: {e}")

            return True
        except Exception as e:
            self.issues.append(f"Failed to check storage: {e}")
            return False

    def check_logs(self) -> bool:
        """Check recent logs for errors."""
        log_dir = Path("logs")
        if not log_dir.exists():
            self.warnings.append("No logs directory found")
            return True

        log_files = list(log_dir.glob("*.log"))
        if not log_files:
            self.warnings.append("No log files found")
            return True

        # Check most recent log
        latest_log = max(log_files, key=lambda p: p.stat().st_mtime)
        try:
            with open(latest_log, "r") as f:
                lines = f.readlines()[-100:]  # Last 100 lines

            error_count = sum(
                1 for line in lines if "ERROR" in line and "CRITICAL" not in line
            )
            if error_count > 0:
                self.warnings.append(f"Found {error_count} errors in {latest_log.name}")
            else:
                self.passed.append(f"Recent logs clean: {latest_log.name}")

            return True
        except Exception as e:
            self.issues.append(f"Failed to read logs: {e}")
            return False

    def run_all_checks(self) -> bool:
        """Run all health checks."""
        logger.info("Starting health check...")

        checks = [
            self.load_configuration,
            self.check_databricks_connection,
            self.check_delta_tables,
            self.check_table_freshness,
            self.check_storage_access,
            self.check_logs,
        ]

        all_passed = True
        for check in checks:
            try:
                result = check()
                if not result:
                    all_passed = False
            except Exception as e:
                self.issues.append(f"Health check {check.__name__} crashed: {e}")
                all_passed = False

        return all_passed

    def print_report(self):
        """Print health check report."""
        print("\n" + "=" * 60)
        print("HEALTH CHECK REPORT")
        print("=" * 60)

        if self.passed:
            print(f"\n✓ PASSED ({len(self.passed)} checks)")
            for item in self.passed:
                print(f"  ✓ {item}")

        if self.warnings:
            print(f"\n⚠ WARNINGS ({len(self.warnings)} warnings)")
            for warning in self.warnings:
                print(f"  ⚠ {warning}")

        if self.issues:
            print(f"\n✗ FAILED ({len(self.issues)} issues)")
            for issue in self.issues:
                print(f"  ✗ {issue}")

        print("\n" + "=" * 60)

        if not self.issues:
            print("✅ HEALTHY - All critical checks passed")
        else:
            print("❌ UNHEALTHY - Critical issues found")

        print("=" * 60 + "\n")

        return len(self.issues) == 0


def main():
    """Run health check and exit with appropriate code."""
    setup_logging()
    checker = HealthCheck()
    success = checker.run_all_checks()
    checker.print_report()
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
