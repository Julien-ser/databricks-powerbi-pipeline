"""
Data generation utilities for creating sample e-commerce datasets.
"""

import logging
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

import pandas as pd

logger = logging.getLogger(__name__)


def generate_customers(num_customers: int = 100) -> pd.DataFrame:
    """Generate sample customer data."""
    customers = []

    first_names = [
        "James",
        "Mary",
        "John",
        "Patricia",
        "Robert",
        "Jennifer",
        "Michael",
        "Linda",
        "William",
        "Elizabeth",
    ]
    last_names = [
        "Smith",
        "Johnson",
        "Williams",
        "Brown",
        "Jones",
        "Garcia",
        "Miller",
        "Davis",
        "Rodriguez",
        "Martinez",
    ]
    cities = [
        "New York",
        "Los Angeles",
        "Chicago",
        "Houston",
        "Phoenix",
        "Philadelphia",
        "San Antonio",
        "San Diego",
    ]
    states = ["NY", "CA", "IL", "TX", "AZ", "PA", "TX", "CA"]

    for i in range(num_customers):
        customer_id = f"CUST{i:04d}"
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        email = f"{first_name.lower()}.{last_name.lower()}@example.com"
        city = random.choice(cities)
        state = states[cities.index(city)]
        signup_date = datetime.now() - timedelta(days=random.randint(30, 730))

        customers.append(
            {
                "customer_id": customer_id,
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "city": city,
                "state": state,
                "signup_date": signup_date.strftime("%Y-%m-%d"),
                "customer_segment": random.choice(["Premium", "Standard", "Basic"]),
            }
        )

    return pd.DataFrame(customers)


def generate_products(num_products: int = 50) -> pd.DataFrame:
    """Generate sample product data."""
    categories = [
        "Electronics",
        "Clothing",
        "Home & Garden",
        "Sports",
        "Books",
        "Beauty",
    ]
    products = []

    for i in range(num_products):
        product_id = f"PROD{i:04d}"
        category = random.choice(categories)
        base_price = random.uniform(10, 500)

        products.append(
            {
                "product_id": product_id,
                "product_name": f"{category} Product {i + 1}",
                "category": category,
                "price": round(base_price, 2),
                "cost": round(base_price * random.uniform(0.4, 0.7), 2),
                "inventory_quantity": random.randint(10, 500),
            }
        )

    return pd.DataFrame(products)


def generate_orders(
    num_orders: int = 500,
    customers: Optional[List[str]] = None,
    products: Optional[List[str]] = None,
) -> pd.DataFrame:
    """Generate sample order data."""
    if customers is None:
        customers = [f"CUST{i:04d}" for i in range(100)]
    if products is None:
        products = [f"PROD{i:04d}" for i in range(50)]

    orders = []
    statuses = ["completed", "shipped", "processing", "cancelled", "returned"]

    for i in range(num_orders):
        order_id = f"ORDER{i:06d}"
        customer_id = random.choice(customers)
        order_date = datetime.now() - timedelta(days=random.randint(1, 365))
        status = random.choice(statuses)
        total_amount = round(random.uniform(20, 1000), 2)

        orders.append(
            {
                "order_id": order_id,
                "customer_id": customer_id,
                "order_date": order_date.strftime("%Y-%m-%d %H:%M:%S"),
                "status": status,
                "total_amount": total_amount,
                "shipping_address": f"{random.randint(100, 999)} Main St",
                "payment_method": random.choice(
                    ["credit_card", "paypal", "debit_card"]
                ),
            }
        )

    return pd.DataFrame(orders)


def generate_order_items(
    orders_df: pd.DataFrame, products_df: pd.DataFrame
) -> pd.DataFrame:
    """Generate order line items."""
    order_items = []

    for _, order in orders_df.iterrows():
        # Each order has 1-5 items
        num_items = random.randint(1, 5)
        order_products = random.sample(
            list(products_df["product_id"]), min(num_items, len(products_df))
        )

        for product_id in order_products:
            product = products_df[products_df["product_id"] == product_id].iloc[0]
            quantity = random.randint(1, 3)

            order_items.append(
                {
                    "order_id": order["order_id"],
                    "product_id": product_id,
                    "quantity": quantity,
                    "unit_price": float(product["price"]),
                    "line_total": round(quantity * float(product["price"]), 2),
                }
            )

    return pd.DataFrame(order_items)


def generate_all_data(output_dir: str = "data") -> None:
    """Generate all sample datasets and save to CSV files."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    logger.info("Generating sample e-commerce data...")

    # Generate customers
    customers_df = generate_customers(100)
    customers_df.to_csv(output_path / "sample_customers.csv", index=False)
    logger.info(f"Saved {len(customers_df)} customers to sample_customers.csv")

    # Generate products
    products_df = generate_products(50)
    products_df.to_csv(output_path / "sample_products.csv", index=False)
    logger.info(f"Saved {len(products_df)} products to sample_products.csv")

    # Generate orders
    orders_df = generate_orders(
        500, customers_df["customer_id"].tolist(), products_df["product_id"].tolist()
    )
    orders_df.to_csv(output_path / "sample_orders.csv", index=False)
    logger.info(f"Saved {len(orders_df)} orders to sample_orders.csv")

    # Generate order items
    order_items_df = generate_order_items(orders_df, products_df)
    order_items_df.to_csv(output_path / "sample_order_items.csv", index=False)
    logger.info(f"Saved {len(order_items_df)} order items to sample_order_items.csv")

    logger.info("Sample data generation complete")


if __name__ == "__main__":
    from utils import setup_logging

    setup_logging()
    generate_all_data()
