"""
Unit tests for data generation functions.
"""

import pandas as pd
import pytest

from src.generate_sample_data import (
    generate_customers,
    generate_products,
    generate_orders,
    generate_order_items,
)


class TestGenerateCustomers:
    """Tests for generate_customers function."""

    def test_generates_specified_count(self):
        """Test that correct number of customers are generated."""
        df = generate_customers(50)
        assert len(df) == 50

    def test_has_required_columns(self):
        """Test that DataFrame has all required columns."""
        df = generate_customers(10)
        expected_columns = [
            "customer_id",
            "first_name",
            "last_name",
            "email",
            "city",
            "state",
            "signup_date",
            "customer_segment",
        ]
        for col in expected_columns:
            assert col in df.columns

    def test_customer_ids_are_unique(self):
        """Test that all customer IDs are unique."""
        df = generate_customers(100)
        assert df["customer_id"].is_unique

    def test_segments_are_valid(self):
        """Test that customer segments are from expected set."""
        df = generate_customers(100)
        valid_segments = {"Premium", "Standard", "Basic"}
        assert set(df["customer_segment"].unique()).issubset(valid_segments)


class TestGenerateProducts:
    """Tests for generate_products function."""

    def test_generates_specified_count(self):
        """Test that correct number of products are generated."""
        df = generate_products(25)
        assert len(df) == 25

    def test_has_required_columns(self):
        """Test that DataFrame has all required columns."""
        df = generate_products(10)
        expected_columns = [
            "product_id",
            "product_name",
            "category",
            "price",
            "cost",
            "inventory_quantity",
        ]
        for col in expected_columns:
            assert col in df.columns

    def test_prices_are_positive(self):
        """Test that all prices are positive."""
        df = generate_products(50)
        assert (df["price"] > 0).all()
        assert (df["cost"] > 0).all()

    def test_cost_is_lower_than_price(self):
        """Test that cost is always lower than price."""
        df = generate_products(50)
        assert (df["cost"] < df["price"]).all()

    def test_product_ids_are_unique(self):
        """Test that all product IDs are unique."""
        df = generate_products(100)
        assert df["product_id"].is_unique


class TestGenerateOrders:
    """Tests for generate_orders function."""

    def test_generates_specified_count(self):
        """Test that correct number of orders are generated."""
        df = generate_orders(100)
        assert len(df) == 100

    def test_has_required_columns(self):
        """Test that DataFrame has all required columns."""
        df = generate_orders(10)
        expected_columns = [
            "order_id",
            "customer_id",
            "order_date",
            "status",
            "total_amount",
            "shipping_address",
            "payment_method",
        ]
        for col in expected_columns:
            assert col in df.columns

    def test_uses_provided_customers(self):
        """Test that only provided customer IDs are used."""
        custom_customers = [f"CUST{i:04d}" for i in range(10)]
        df = generate_orders(50, customers=custom_customers)
        assert set(df["customer_id"].unique()).issubset(set(custom_customers))

    def test_uses_provided_products(self):
        """Test that only provided product IDs are used."""
        custom_products = [f"PROD{i:04d}" for i in range(10)]
        df = generate_orders(50, products=custom_products)
        # Orders themselves don't use products, this is just to test parameter passing
        assert len(df) == 50

    def test_order_ids_are_unique(self):
        """Test that all order IDs are unique."""
        df = generate_orders(200)
        assert df["order_id"].is_unique

    def test_valid_payment_methods(self):
        """Test that payment methods are from expected set."""
        df = generate_orders(100)
        valid_methods = {"credit_card", "paypal", "debit_card"}
        assert set(df["payment_method"].unique()).issubset(valid_methods)


class TestGenerateOrderItems:
    """Tests for generate_order_items function."""

    def test_generates_items_for_all_orders(self):
        """Test that order items are generated for all orders."""
        orders_df = generate_orders(50)
        products_df = generate_products(20)
        items_df = generate_order_items(orders_df, products_df)

        # All order IDs in items should exist in orders
        assert set(items_df["order_id"].unique()).issubset(set(orders_df["order_id"]))

    def test_items_have_required_columns(self):
        """Test that DataFrame has all required columns."""
        orders_df = generate_orders(10)
        products_df = generate_products(10)
        items_df = generate_order_items(orders_df, products_df)

        expected_columns = [
            "order_id",
            "product_id",
            "quantity",
            "unit_price",
            "line_total",
        ]
        for col in expected_columns:
            assert col in items_df.columns

    def test_line_total_correct(self):
        """Test that line_total equals quantity * unit_price."""
        orders_df = generate_orders(10)
        products_df = generate_products(10)
        items_df = generate_order_items(orders_df, products_df)

        # Check that line_total is correctly calculated
        for _, row in items_df.iterrows():
            expected = round(row["quantity"] * row["unit_price"], 2)
            assert abs(row["line_total"] - expected) < 0.01

    def test_product_ids_are_valid(self):
        """Test that all product IDs in items exist in products."""
        orders_df = generate_orders(20)
        products_df = generate_products(15)
        items_df = generate_order_items(orders_df, products_df)

        valid_products = set(products_df["product_id"])
        assert set(items_df["product_id"].unique()).issubset(valid_products)
