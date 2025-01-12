from dataclasses import dataclass


@dataclass
class MisaRequestTable:
    sku: str
    quantity: int
    current_row: int
    discount_value: float = 0.0
    discount_rate: str = "0"
    source_name: str = None
    price: str = None
    line_amount: float = 0.0
    default_item_quantity: int = None
