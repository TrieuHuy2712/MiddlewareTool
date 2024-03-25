from dataclasses import dataclass
from typing import Optional

from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class FulfillmentItem:
    product_name: str
    id: str = None
    created_on: str = None
    modified_on: str = None
    order_line_item_id: str = None
    product_id: str = None
    variant_id: str = None
    variant_name: str = None
    order_line_item_note: str = None
    base_price: str = None
    quantity: str = None
    tax_type_id: str = None
    tax_rate_override: str = None
    tax_rate: str = None
    line_amount: str = None
    line_tax_amount: str = None
    line_discount_amount: str = None
    discount_value: str = None
    variant: str = None
    sku: str = None
    barcode: str = None
    unit: str = None
    variant_options: str = None
    serials: str = None
    lots_dates: str = None
    product_type: str = None
    distributed_discount_value: str = None
    distributed_discount_amount: str = None
    lots_number_code1: str = None
    lots_number_code2: str = None
    lots_number_code3: str = None
    lots_number_code4: str = None
    sub_variants = []
    is_freeform: bool = False
    is_composite: bool = False
    is_packsize: bool = False
