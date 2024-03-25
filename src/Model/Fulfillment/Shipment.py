from dataclasses import dataclass
from typing import Optional

from dataclasses_json import dataclass_json

from src.Model.Customer.Address import Address


@dataclass_json
@dataclass
class Shipment:
    cod_amount: int = None
    collation_status: str = None
    detail: str = None
    freight_amount: int = None
    freight_amount_detail: str = None
    freight_payer:str = None
    height: float = None
    id: float = None
    length: float = None
    note: str = None
    reference_status: str = None
    reference_status_explanation: str = None
    sender_address: str = None
    service_name: str = None
    shipping_address: Address = None
    shipped_on: str = None
    sorting_code: str = None
    tracking_code: str = None
    tracking_url: str = None
    weight: float = None
    width: float = None
