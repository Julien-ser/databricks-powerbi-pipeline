# Environment Configuration Template
# Copy this file to env.py and fill in your actual values
# DO NOT commit env.py to version control!

# Databricks Connection
DATABRICKS_HOST = "https://adb-1234567890123456.17.azuredatabricks.net"
DATABRICKS_TOKEN = "dapiXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
DATABRICKS_WORKSPACE_ID = "1234567890123456"

# Storage (if using cloud storage)
STORAGE_ACCOUNT = "yourstorageaccount"
STORAGE_CONTAINER = "ecommerce"
STORAGE_KEY = "storage-key-here"

# Power BI
POWERBI_WORKSPACE_ID = "your-powerbi-workspace-id"
POWERBI_DATASET_ID = "your-dataset-id"

# Notification Settings
SLACK_WEBHOOK_URL = ""
EMAIL_SENDER = "pipeline-alerts@yourcompany.com"
EMAIL_RECIPIENTS = "data-team@yourcompany.com"

# Feature Flags
ENABLE_MONITORING = True
SEND_NOTIFICATIONS = False
