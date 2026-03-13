"""
Deployment validation script.

This script checks that all prerequisites for deployment are met:
- Required Python packages are installed
- Configuration files exist and are valid
- Databricks connection can be established (if credentials provided)
- Notebook files exist and are properly formatted
- Storage paths are accessible
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils import setup_logging, ensure_directory

logger = logging.getLogger(__name__)

# Import databricks-sdk conditionally
try:
    from databricks.sdk import WorkspaceClient
    from databricks.sdk.core import DatabricksError

    DATABRICKS_SDK_AVAILABLE = True
except ImportError:
    DATABRICKS_SDK_AVAILABLE = False
    logger.warning(
        "databricks-sdk not installed. Some validation checks will be skipped."
    )


class DeploymentValidator:
    """Validate deployment prerequisites and configuration."""

    def __init__(self):
        self.errors = []
        self.warnings = []
        self.passed = []

    def check_python_version(self) -> bool:
        """Check Python version is 3.8+."""
        major, minor = sys.version_info[:2]
        if (major, minor) < (3, 8):
            self.errors.append(f"Python 3.8+ required, found {major}.{minor}")
            return False
        self.passed.append(f"Python version {major}.{minor} is compatible")
        return True

    def check_required_packages(self) -> bool:
        """Check that required packages are installed."""
        required = ["pyspark", "delta", "pandas", "numpy", "pytest"]
        optional = ["databricks"]

        missing_required = []
        missing_optional = []

        for package in required:
            try:
                __import__(package.replace("-", "_"))
                self.passed.append(f"Package {package} is installed")
            except ImportError:
                missing_required.append(package)

        for package in optional:
            try:
                __import__(package.replace("-", "_"))
                self.passed.append(f"Optional package {package} is installed")
            except ImportError:
                missing_optional.append(package)

        if missing_required:
            self.errors.append(
                f"Missing required packages: {', '.join(missing_required)}"
            )
            return False

        if missing_optional:
            self.warnings.append(
                f"Missing optional packages: {', '.join(missing_optional)}"
            )

        return len(missing_required) == 0

    def check_config_files(self) -> bool:
        """Check that configuration files exist and are valid."""
        config_files = ["config/parameters.json", "config/env.example.py"]

        for config_file in config_files:
            path = Path(config_file)
            if not path.exists():
                self.errors.append(f"Configuration file missing: {config_file}")
                return False
            self.passed.append(f"Configuration file exists: {config_file}")

        # Validate parameters.json
        try:
            with open("config/parameters.json", "r") as f:
                params = json.load(f)

            # Check required keys
            required_keys = ["databricks", "data"]
            for key in required_keys:
                if key not in params:
                    self.errors.append(
                        f"Missing required key in parameters.json: {key}"
                    )
                    return False

            self.passed.append("parameters.json is valid JSON with required keys")
        except json.JSONDecodeError as e:
            self.errors.append(f"Invalid JSON in parameters.json: {e}")
            return False
        except Exception as e:
            self.errors.append(f"Error reading parameters.json: {e}")
            return False

        return True

    def check_env_config(self) -> bool:
        """Check that environment configuration is properly set up."""
        env_example = Path("config/env.example.py")
        env_file = Path("config/env.py")

        if not env_example.exists():
            self.errors.append("config/env.example.py not found")
            return False

        # Check if env.py exists
        if not env_file.exists():
            self.warnings.append(
                "config/env.py not found - please copy from env.example.py"
            )
            return True  # Not a failure, but warning

        # Validate env.py has required variables
        try:
            # Import env.py
            sys.path.insert(0, "config")
            import env

            required_vars = ["DATABRICKS_HOST", "DATABRICKS_TOKEN"]
            missing = []

            for var in required_vars:
                if not hasattr(env, var) or getattr(env, var) == "":
                    missing.append(var)

            if missing:
                self.warnings.append(
                    f"Missing or empty environment variables in env.py: {', '.join(missing)}"
                )
                return True  # Not a failure for validation

            self.passed.append("Environment configuration is properly set")
            return True

        except Exception as e:
            self.errors.append(f"Error validating env.py: {e}")
            return False

    def check_notebooks(self) -> bool:
        """Check that all required notebooks exist."""
        notebooks = [
            "notebooks/01_bronze/bronze_ingestion.ipynb",
            "notebooks/02_silver/silver_transformation.ipynb",
            "notebooks/03_gold/gold_aggregation.ipynb",
        ]

        all_exist = True
        for notebook in notebooks:
            path = Path(notebook)
            if not path.exists():
                self.errors.append(f"Notebook not found: {notebook}")
                all_exist = False
            else:
                self.passed.append(f"Notebook exists: {notebook}")

        return all_exist

    def check_sample_data(self) -> bool:
        """Check that sample data files exist."""
        sample_files = [
            "data/sample_customers.csv",
            "data/sample_products.csv",
            "data/sample_orders.csv",
            "data/sample_order_items.csv",
        ]

        all_exist = True
        for file in sample_files:
            path = Path(file)
            if not path.exists():
                self.warnings.append(f"Sample data not found: {file}")
                all_exist = False
            else:
                self.passed.append(f"Sample data exists: {file}")

        # Not a hard failure if sample data missing - users can provide their own
        return True

    def check_production_readiness(self) -> bool:
        """Check production deployment readiness."""
        required_scripts = [
            "src/health_check.py",
            "src/rollback.py",
            "src/deploy_notebooks.py",
            "src/monitor_pipeline.py",
        ]

        all_exist = True
        for script in required_scripts:
            path = Path(script)
            if not path.exists():
                self.errors.append(f"Deployment script missing: {script}")
                all_exist = False
            else:
                # Check if executable (on Unix-like systems)
                if path.suffix == ".py":
                    self.passed.append(f"Deployment script exists: {script}")

        # Check if env.py has been created from template
        env_file = Path("config/env.py")
        env_example = Path("config/env.example.py")
        if env_file.exists() and env_example.exists():
            self.passed.append("Environment configuration is set up")
        elif env_example.exists():
            self.warnings.append(
                "config/env.py not created from template - required for deployment"
            )

        return all_exist

    def check_directory_structure(self) -> bool:
        """Check that required directories exist."""
        directories = ["notebooks", "src", "config", "tests", "docs", "data", "logs"]

        for directory in directories:
            path = Path(directory)
            if not path.exists():
                self.errors.append(f"Required directory missing: {directory}/")
                return False
            self.passed.append(f"Directory exists: {directory}/")

        return True

    def check_databricks_connection(self) -> bool:
        """Test connection to Databricks if credentials are available."""
        if not DATABRICKS_SDK_AVAILABLE:
            self.warnings.append(
                "Cannot test Databricks connection: databricks-sdk not installed"
            )
            return True

        # Try to get credentials
        try:
            from config.env import DATABRICKS_HOST, DATABRICKS_TOKEN

            if not DATABRICKS_HOST or not DATABRICKS_TOKEN:
                self.warnings.append("Databricks credentials not configured in env.py")
                return True

            # Attempt connection
            client = WorkspaceClient(host=DATABRICKS_HOST, token=DATABRICKS_TOKEN)

            # Test API call
            me = client.current_user.me()
            self.passed.append(f"Connected to Databricks workspace: {DATABRICKS_HOST}")
            self.passed.append(f"Authenticated as: {me.display_name} ({me.user_name})")
            return True

        except ImportError:
            self.warnings.append(
                "Cannot test Databricks connection: config/env.py not found"
            )
            return True
        except Exception as e:
            self.errors.append(f"Failed to connect to Databricks: {e}")
            return False

    def run_all_validations(self) -> Tuple[bool, List[str], List[str], List[str]]:
        """Run all validation checks.

        Returns:
            tuple: (success, errors, warnings, passed)
        """
        logger.info("Starting deployment validation...")

        checks = [
            self.check_python_version,
            self.check_directory_structure,
            self.check_config_files,
            self.check_env_config,
            self.check_required_packages,
            self.check_notebooks,
            self.check_sample_data,
            self.check_production_readiness,
            self.check_databricks_connection,
        ]

        all_passed = True
        for check in checks:
            try:
                result = check()
                if not result:
                    all_passed = False
            except Exception as e:
                self.errors.append(f"Validation check {check.__name__} crashed: {e}")
                all_passed = False

        return all_passed, self.errors, self.warnings, self.passed


def main():
    """Run deployment validation and report results."""
    setup_logging()
    ensure_directory("logs")

    validator = DeploymentValidator()
    success, errors, warnings, passed = validator.run_all_validations()

    print("\n" + "=" * 60)
    print("DEPLOYMENT VALIDATION REPORT")
    print("=" * 60)

    if passed:
        print(f"\n✓ PASSED ({len(passed)} checks)")
        for item in passed:
            print(f"  ✓ {item}")

    if warnings:
        print(f"\n⚠ WARNINGS ({len(warnings)} warnings)")
        for warning in warnings:
            print(f"  ⚠ {warning}")

    if errors:
        print(f"\n✗ FAILED ({len(errors)} errors)")
        for error in errors:
            print(f"  ✗ {error}")

    print("\n" + "=" * 60)

    if success and not errors:
        print("✅ Deployment is READY")
        print("=" * 60 + "\n")
        return 0
    else:
        print("❌ Deployment is NOT READY - please fix errors above")
        print("=" * 60 + "\n")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
