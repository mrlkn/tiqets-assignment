import logging
import sys

from src.file_handler.csv_handler import CSVHandler
from src.models.models import OutputRow, ProcessedData
from src.processor.data_processor import DataProcessor

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def main(orders_file: str, barcodes_file: str, output_file: str):
    try:
        csv_handler = CSVHandler()
        orders = csv_handler.read(orders_file)
        barcodes = csv_handler.read(barcodes_file)

        logger.info(f"Read {len(orders)} orders and {len(barcodes)} barcodes.")

        logger.info("Processing data. Any errors will be logged immediately:")
        processor = DataProcessor()
        processed_data = processor.process_data(orders, barcodes)

        logger.info("Processing complete. Summary of processed data:")
        log_summary(processed_data, processor.duplicate_barcodes)

        write_output(processed_data, output_file, csv_handler)

        logger.info(f"Output written to {output_file}")

        log_analysis(processed_data, processor.duplicate_barcodes)

    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")
        sys.exit(1)


def log_summary(data: ProcessedData, duplicate_barcodes: set):
    logger.info(f"Total customers: {len(data.customer_orders)}")
    logger.info(f"Total orders with barcodes: {sum(len(customer.orders) for customer in data.customer_orders)}")
    logger.info(f"Unused barcodes: {data.unused_barcodes}")
    logger.info(f"Duplicate barcodes: {len(duplicate_barcodes)}")


def log_analysis(data: ProcessedData, duplicate_barcodes: set, num_of_customer: int = 5):
    logger.info("Top 5 customers:")
    for customer in data.top_customers:
        logger.info(f"Customer {customer['customer_id']}: {customer['ticket_count']} tickets")

    logger.info(f"Unused barcodes: {data.unused_barcodes}")
    logger.info(f"Duplicate barcodes: {len(duplicate_barcodes)}")

    logger.info("Sample of customer orders:")
    for customer in data.customer_orders[:num_of_customer]:
        logger.info(f"Customer {customer.customer_id}:")
        for order in customer.orders[:2]:
            logger.info(f"  Order {order.order_id}: {len(order.barcodes)} barcodes")
        if len(customer.orders) > 2:
            logger.info(f"  ... and {len(customer.orders) - 2} more orders")


def write_output(data: ProcessedData, output_file: str, csv_handler: CSVHandler):
    output_data = []
    for customer in data.customer_orders:
        for order in customer.orders:
            output_row = OutputRow(
                customer_id=customer.customer_id, order_id=order.order_id, barcodes=",".join(order.barcodes)
            )
            output_data.append(output_row.dict())
    csv_handler.write(output_file, output_data)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        logger.info("Usage: python main.py <orders_file> <barcodes_file> <output_file>")
        sys.exit(1)

    orders_file, barcodes_file, output_file = sys.argv[1], sys.argv[2], sys.argv[3]
    main(orders_file, barcodes_file, output_file)
