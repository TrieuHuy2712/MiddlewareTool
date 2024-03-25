from dataclasses import dataclass
from typing import Optional, List

from dataclasses_json import dataclass_json

from src.Model.Customer.Address import Address
from src.Model.Customer.Customer import Customer
from src.Model.DiscountItem import DiscountItem
from src.Model.Fulfillment.Fulfillment import Fulfillment
from src.Model.Item import Item
from src.Model.PrePayment import PrePayment

@dataclass_json
@dataclass(kw_only=True)
class Order:
    id: str
    tenant_id: str = None
    location_id: str = None
    code: str
    created_on: str
    modified_on: str = None
    issued_on: str = None
    ship_on:str = None
    ship_on_min: str = None
    ship_on_max: str = None
    account_id: str = None
    assignee_id:str = None
    customer_id: str = None
    customer_data: Customer
    tax_treatment: str = None
    status: str
    packed_status: str = None
    fulfillment_status: str
    received_status: str
    payment_status: str
    return_status: str
    phone_number: str
    total_discount: str
    total_tax: str
    discount_items: List[DiscountItem] = None
    order_line_items: List[Item] = None
    contact_id: str = None
    billing_address: Address = None
    shipping_address: Address = None
    reference_number: str = None
    price_list_id: str = None
    discount_reason: str = None
    delivery_fee: str = None
    prepayments: List[PrePayment] = None
    fulfillments: List[Fulfillment] = None
    business_version: int = None
    expected_payment_method_id: str = None
    expected_delivery_type: str = None
    expected_delivery_provider_id: str = None
    process_status_id: str = None
    reason_cancel_id: str = None
    finalized_on: str = None
    finished_on: str = None
    completed_on: str = None
    channel: str = None
    cancelled_on: str = None
    promotion_redemptions = []
    reference_url: str = None
    from_order_return_id: str = None
    order_return_exchange: str = None
    total: float = None
    total_order_exchange_amount: str = None
    order_coupon_code: str = None
    interconnection_status: str = None
    allow_no_refund_order_exchange_amount = False
    create_invoice = False
    einvoice_status = "uncreated"
    email: Optional[str] = ""
    print_status: bool = False
    order_discount_rate: int = 0
    order_discount_value: int = 0
    order_discount_amount: int = 0
    note: str = ""
    order_returns = []
    source_id: int = 0
    source_name: str = None
    sent_to_misa: bool = False

