from dataclasses import dataclass
from typing import Optional, List

from dataclasses_json import dataclass_json

from src.Model.DiscountItem import DiscountItem

@dataclass_json
@dataclass
class CompositeItem:
    created_on: str = None
    modified_on: str = None
    order_id: str = None
    order_line_item_id: str = None
    original_quantity: int = None
    price: float = None
    product_id: int = None
    product_name: float = None
    product_type: str = None
    quantity: int = None
    discount: int = None
    sku: str = None
    unit: str = None

@dataclass_json
@dataclass
class Item:
    id: str = None
    created_on: str = None
    modified_on: str = None
    variant_id: str = None
    product_id: str = None
    product_name: str = None
    variant_name: str = None
    line_amount: str = None
    discount_items: List[DiscountItem] = None
    price: str = None
    quantity: int = None
    sku: str = None
    barcode: str = None
    tax_included: bool = None
    discount_amount: str = None
    lots_dates = []
    tax_type_id: str = None
    tax_rate_override: int = None
    tax_amount: str = None
    discount_value: str = None # Giá chiết khấu
    discount_reason: str = None
    note: str = None
    pack_size_quantity: int = None
    pack_size_root_id: int = None
    composite_item_domains: List[CompositeItem] = None
    unit: str = None
    serials: str = None
    lots_number_code1: str = None
    lots_number_code2: str = None
    lots_number_code3: str = None
    lots_number_code4: str = None
    line_promotion_type: str = None
    warranty: str = None
    distributed_discount_amount: str = "0"
    discount_rate: str = "0"
    is_freeform: bool = False
    is_composite: bool = False
    is_packsize: bool = False
    height_text_term_compo: int = 0
    variant_options: str = "Mặc định"
    product_type: str = "normal"



