import io
import sys
import unittest

from src.models.models import Barcode, Customer, CustomerOrder, Order
from src.processor.data_processor import DataProcessor


class TestDataProcessor(unittest.TestCase):
    def setUp(self):
        self.processor = DataProcessor()

    def test_validate_orders(self):
        input_orders = [
            {"order_id": "1", "customer_id": "10"},
            {"order_id": "2", "customer_id": "11"},
            {"order_id": "3", "customer_id": "12"},
            {"order_id": "", "customer_id": "13"},
            {"customer_id": "14"},
        ]

        captured_output = io.StringIO()
        sys.stderr = captured_output

        valid_orders = self.processor._validate_orders(input_orders)

        sys.stderr = sys.__stderr__

        self.assertEqual(len(valid_orders), 3)
        self.assertIsInstance(valid_orders[0], Order)
        self.assertEqual(valid_orders[0].order_id, "1")
        self.assertEqual(valid_orders[0].customer_id, "10")

        error_output = captured_output.getvalue()
        self.assertIn("InvalidOrderDataError: Invalid order data: Empty order_id", error_output)
        self.assertIn("InvalidOrderDataError: Invalid order data: 1 validation error for Order", error_output)

    def test_validate_barcodes(self):
        input_barcodes = [
            {"barcode": "11111111111", "order_id": "1"},
            {"barcode": "22222222222", "order_id": "2"},
            {"barcode": "33333333333", "order_id": ""},
            {"barcode": "44444444444"},
            {"barcode": "555555", "order_id": "3"},
            {"order_id": "4"},
        ]

        captured_output = io.StringIO()
        sys.stderr = captured_output

        valid_barcodes = self.processor._validate_barcodes(input_barcodes)

        sys.stderr = sys.__stderr__

        self.assertEqual(len(valid_barcodes), 4)
        self.assertIsInstance(valid_barcodes[0], Barcode)
        self.assertEqual(valid_barcodes[0].barcode, "11111111111")
        self.assertEqual(valid_barcodes[0].order_id, "1")
        self.assertIsNone(valid_barcodes[3].order_id)

        error_output = captured_output.getvalue()
        self.assertIn("InvalidBarcodeDataError: Invalid barcode data: 1 validation error for Barcode", error_output)
        self.assertIn("Barcode must be an 11-digit number", error_output)
        self.assertIn("Field required", error_output)

    def test_duplicate_barcodes(self):
        input_barcodes = [
            {"barcode": "11111111111", "order_id": "1"},
            {"barcode": "22222222222", "order_id": "2"},
            {"barcode": "11111111111", "order_id": "3"},
            {"barcode": "33333333333", "order_id": "4"},
            {"barcode": "22222222222", "order_id": "5"},
        ]
        valid_barcodes = self.processor._validate_barcodes(input_barcodes)

        self.assertEqual(len(valid_barcodes), 3)
        self.assertEqual(len(self.processor.duplicate_barcodes), 2)
        self.assertIn("11111111111", self.processor.duplicate_barcodes)
        self.assertIn("22222222222", self.processor.duplicate_barcodes)

    def test_duplicate_barcodes_with_total_barcodes(self):
        input_barcodes = [
            {"barcode": "11111111111", "order_id": "1"},
            {"barcode": "22222222222", "order_id": "2"},
            {"barcode": "11111111111", "order_id": "3"},
            {"barcode": "33333333333", "order_id": "4"},
            {"barcode": "44444444444", "order_id": "5"},
            {"barcode": "22222222222", "order_id": "6"},
        ]
        valid_barcodes = self.processor._validate_barcodes(input_barcodes)

        self.assertEqual(len(valid_barcodes), 4)
        self.assertEqual(len(self.processor.duplicate_barcodes), 2)
        self.assertEqual(len(input_barcodes), 6)

    def test_group_barcodes_by_order(self):
        barcodes = [
            Barcode(barcode="11111111111", order_id="1"),
            Barcode(barcode="22222222222", order_id="1"),
            Barcode(barcode="33333333333", order_id="2"),
            Barcode(barcode="44444444444", order_id="3"),
            Barcode(barcode="55555555555", order_id="2"),
            Barcode(barcode="66666666666", order_id=None),
        ]
        grouped_barcodes = self.processor._group_barcodes_by_order(barcodes)

        self.assertEqual(len(grouped_barcodes), 3)
        self.assertEqual(len(grouped_barcodes["1"]), 2)
        self.assertEqual(len(grouped_barcodes["2"]), 2)
        self.assertEqual(len(grouped_barcodes["3"]), 1)
        self.assertNotIn(None, grouped_barcodes)

    def test_get_top_customers_with_six_customers(self):
        customer_orders = {
            "10": Customer(customer_id="10", orders=[CustomerOrder(order_id="1", barcodes=["1", "2"])]),
            "11": Customer(customer_id="11", orders=[CustomerOrder(order_id="2", barcodes=["3", "4", "5"])]),
            "12": Customer(customer_id="12", orders=[CustomerOrder(order_id="3", barcodes=["6"])]),
            "13": Customer(customer_id="13", orders=[CustomerOrder(order_id="4", barcodes=["7", "8"])]),
            "14": Customer(customer_id="14", orders=[CustomerOrder(order_id="5", barcodes=["9", "10", "11", "12"])]),
            "15": Customer(customer_id="15", orders=[CustomerOrder(order_id="6", barcodes=["13"])]),
        }
        top_customers = self.processor._get_top_customers(customer_orders)

        self.assertEqual(len(top_customers), 5)
        self.assertEqual(top_customers[0]["customer_id"], "14")
        self.assertEqual(top_customers[0]["ticket_count"], 4)
        self.assertEqual(top_customers[1]["customer_id"], "11")
        self.assertEqual(top_customers[1]["ticket_count"], 3)

    def test_count_unused_barcodes(self):
        barcodes = [
            Barcode(barcode="11111111111", order_id="1"),
            Barcode(barcode="22222222222", order_id=None),
            Barcode(barcode="33333333333", order_id=None),
            Barcode(barcode="44444444444", order_id="2"),
            Barcode(barcode="55555555555", order_id=None),
        ]
        unused_count = self.processor._count_unused_barcodes(barcodes)

        self.assertEqual(unused_count, 3)

    def test_count_unused_barcodes_with_duplicates(self):
        barcodes = [
            Barcode(barcode="11111111111", order_id="1"),
            Barcode(barcode="22222222222", order_id=None),
            Barcode(barcode="33333333333", order_id=None),
            Barcode(barcode="44444444444", order_id="2"),
            Barcode(barcode="55555555555", order_id=None),
        ]
        self.processor.duplicate_barcodes = {"22222222222", "33333333333"}
        unused_count = self.processor._count_unused_barcodes(barcodes)

        self.assertEqual(unused_count, 1)


if __name__ == "__main__":
    unittest.main()
