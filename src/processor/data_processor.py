from collections import defaultdict
from typing import Any, Dict, List, Set

from src.error_handlers.validation_errors import (
    DuplicateBarcodeError,
    InvalidBarcodeDataError,
    InvalidOrderDataError,
    OrderWithoutBarcodesError,
)
from src.models.models import Barcode, Customer, CustomerOrder, Order, ProcessedData


class DataProcessor:
    """A class for processing order and barcode data."""

    def __init__(self):
        self.duplicate_barcodes: Set[str] = set()

    def process_data(self, orders: List[Dict[str, Any]], barcodes: List[Dict[str, Any]]) -> ProcessedData:
        """
        Validate and process order and barcode data to generate processed data.

        Args:
            orders (List[Dict[str, Any]]): List of order dictionaries.
            barcodes (List[Dict[str, Any]]): List of barcode dictionaries.

        Returns:
            ProcessedData: Processed data including customer orders, top customers, and unused barcodes.
        """
        validated_orders: List[Order] = self._validate_orders(orders)
        validated_barcodes: List[Barcode] = self._validate_barcodes(barcodes)

        order_barcodes: Dict[str, List[str]] = self._group_barcodes_by_order(validated_barcodes)
        validated_orders = self._validate_orders_with_barcodes(validated_orders, order_barcodes)
        customer_orders: Dict[str, Customer] = self._group_orders_by_customer(validated_orders, order_barcodes)

        return ProcessedData(
            customer_orders=list(customer_orders.values()),
            top_customers=self._get_top_customers(customer_orders),
            unused_barcodes=self._count_unused_barcodes(validated_barcodes),
        )

    @staticmethod
    def _validate_orders(orders: List[Dict[str, Any]]) -> List[Order]:
        """
        Validate order data with Order model and return a list of valid Order pydantic objects.

        Args:
            orders (List[Dict[str, Any]]): List of orders.

        Returns:
            List[Order]: List of validated Order objects.

        Stderr:
            InvalidOrderDataError: If the order data is invalid.
        """
        validated_orders: List[Order] = []
        for order_data in orders:
            try:
                order: Order = Order(**order_data)
                if order.order_id:
                    validated_orders.append(order)
                else:
                    InvalidOrderDataError("Invalid order data: Empty order_id")
            except ValueError as e:
                InvalidOrderDataError(f"Invalid order data: {e}")
        return validated_orders

    def _validate_barcodes(self, barcodes: List[Dict[str, Any]]) -> List[Barcode]:
        """
        Validate barcode data and return a list of valid Barcode pydantic objects.

        Args:
            barcodes (List[Dict[str, Any]]): List of barcode dictionaries.

        Returns:
            List[Barcode]: List of validated Barcode objects.

        Stderr:
            InvalidBarcodeDataError: If the barcode data is invalid.
            DuplicateBarcodeError: If a duplicate barcode is found.
        """
        validated_barcodes: List[Barcode] = []
        seen_barcodes: Set[str] = set()
        for barcode_data in barcodes:
            try:
                barcode: Barcode = Barcode(**barcode_data)
                if barcode.barcode in seen_barcodes:
                    self.duplicate_barcodes.add(barcode.barcode)
                    DuplicateBarcodeError(f"Duplicate barcode found: {barcode.barcode}")
                else:
                    seen_barcodes.add(barcode.barcode)
                    validated_barcodes.append(barcode)
            except ValueError as e:
                InvalidBarcodeDataError(f"Invalid barcode data: {e}")
        return validated_barcodes

    @staticmethod
    def _validate_orders_with_barcodes(orders: List[Order], order_barcodes: Dict[str, List[str]]) -> List[Order]:
        """
        Validate orders to ensure they have associated barcodes.

        Args:
            orders (List[Order]): List of Order objects.
            order_barcodes (Dict[str, List[str]]): Dictionary mapping order IDs to lists of barcodes.

        Returns:
            List[Order]: List of validated Order objects with associated barcodes.

        Stderr:
            OrderWithoutBarcodesError: If an order is found without barcodes.
        """
        validated_orders: List[Order] = []
        for order in orders:
            if order.order_id in order_barcodes:
                validated_orders.append(order)
            else:
                OrderWithoutBarcodesError(f"Order without barcodes found: {order.order_id}")
        return validated_orders

    @staticmethod
    def _group_barcodes_by_order(barcodes: List[Barcode]) -> Dict[str, List[str]]:
        """
        Group barcodes by their associated order ID.

        Args:
            barcodes (List[Barcode]): List of Barcode objects.

        Returns:
            Dict[str, List[str]]: Dictionary mapping order IDs to lists of barcodes.
        """
        order_barcodes: Dict[str, List[str]] = defaultdict(list)
        for barcode in barcodes:
            if barcode.order_id:
                order_barcodes[barcode.order_id].append(barcode.barcode)
        return order_barcodes

    @staticmethod
    def _group_orders_by_customer(orders: List[Order], order_barcodes: Dict[str, List[str]]) -> Dict[str, Customer]:
        """
        Group orders by customer and create Customer objects.

        Args:
            orders (List[Order]): List of Order objects.
            order_barcodes (Dict[str, List[str]]): Dictionary mapping order IDs to lists of barcodes.

        Returns:
            Dict[str, Customer]: Dictionary mapping customer IDs to Customer pydantic objects.
        """
        customer_orders: Dict[str, Customer] = defaultdict(lambda: Customer(customer_id="", orders=[]))
        for order in orders:
            customer: Customer = customer_orders[order.customer_id]
            customer.customer_id = order.customer_id
            customer.orders.append(
                CustomerOrder(order_id=order.order_id, barcodes=order_barcodes.get(order.order_id, []))
            )
        return customer_orders

    @staticmethod
    def _get_top_customers(customer_orders: Dict[str, Customer], num_of_customer: int = 5) -> List[Dict[str, Any]]:
        """
        Get the top customers based on ticket count. The number of top customers to return can be specified.

        Creates a dictionary with the count of tickets for each customer and sorts the dictionary by ticket count.

        Args:
            customer_orders (Dict[str, Customer]): Dictionary mapping customer IDs to Customer objects.
            num_of_customer (int, optional): Number of top customers to return. Defaults to 5.

        Returns:
            List[Dict[str, Any]]: List of dictionaries containing customer IDs and ticket counts.
        """
        customer_ticket_counts: List[Dict[str, Any]] = []
        for customer in customer_orders.values():
            ticket_count: int = sum(len(order.barcodes) for order in customer.orders)
            customer_ticket_counts.append({"customer_id": customer.customer_id, "ticket_count": ticket_count})

        customer_ticket_counts.sort(key=lambda x: x["ticket_count"], reverse=True)

        return customer_ticket_counts[:num_of_customer]

    def _count_unused_barcodes(self, barcodes: List[Barcode]) -> int:
        """
        Count the number of unused barcodes in the list of Barcode objects and subtract the number of duplicate barcodes.

        Args:
            barcodes (List[Barcode]): List of Barcode objects.

        Returns:
            int: Number of unused barcodes.
        """
        unused_count: int = sum(1 for barcode in barcodes if not barcode.order_id)
        return unused_count - len(self.duplicate_barcodes)
