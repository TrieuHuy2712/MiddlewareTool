from dataclasses import dataclass
from typing import Optional, List

from dataclasses_json import dataclass_json

from src.Model.Customer.Address import Address
from src.Model.Fulfillment.FulfillmentItem import FulfillmentItem
from src.Model.Fulfillment.Payment import Payment
from src.Model.Fulfillment.Shipment import Shipment


@dataclass_json
@dataclass
class Fulfillment:
    id: str = None
    tenant_id: str = None
    stock_location_id: str = None
    code: str = None
    order_id: str = None
    account_id: str = None
    assignee_id: str = None
    partner_id: str = None
    billing_address: str = None
    shipping_address: Address = None
    delivery_type: str = None
    tax_treatment: str = None
    discount_rate: str = None
    discount_value: str = None
    discount_amount: str = None
    total: str = None
    total_tax: str = None
    total_discount: str = None
    notes: str = None
    packed_on: str = None
    received_on: str = None
    shipped_on: str = None
    cancel_account_id: str = None
    created_on: str = None
    modified_on: str = None
    stock_out_account_id: str = None
    receive_account_id: str = None
    receive_cancellation_account_id: str = None
    receive_cancellation_on: str = None
    fulfillment_line_items: List[FulfillmentItem] = None
    payments: List[Payment] = None
    shipment: Shipment = None
    total_quantity: str = None
    reason_cancel_id: str = None
    pushing_status: str = None
    bill_of_lading_on: str = None
    packed_processing_account_id: str = None
    bill_of_lading_account_id: str = None
    late_pickup_date: str = None
    late_delivery_date: str = None
    status: str = 'received'
    print_status: bool = False
    composite_fulfillment_status: str = 'received'
    payment_status: str = 'paid'
