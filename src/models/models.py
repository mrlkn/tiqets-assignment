from typing import List, Optional

from pydantic import BaseModel, validator


class Barcode(BaseModel):
    barcode: str
    order_id: Optional[str] = None

    @validator("barcode")
    def barcode_must_be_valid(cls, v):
        if not v.isdigit() or len(v) != 11:
            raise ValueError("Barcode must be an 11-digit number")
        return v


class Order(BaseModel):
    order_id: str
    customer_id: str


class CustomerOrder(BaseModel):
    order_id: str
    barcodes: List[str] = []


class Customer(BaseModel):
    customer_id: str
    orders: List[CustomerOrder] = []


class ProcessedData(BaseModel):
    customer_orders: List[Customer]
    top_customers: List[dict]
    unused_barcodes: int


class OutputRow(BaseModel):
    customer_id: str
    order_id: str
    barcodes: str
