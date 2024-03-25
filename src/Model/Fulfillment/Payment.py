from dataclasses import dataclass
from typing import Optional

from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class Payment:
    id: str = None
    created_on: str = None
    modified_on: str = None
    order_id: str = None
    fulfillment_id: str = None
    payment_method_id: str = None
    amount: str = None
    reference: str = None
    paid_on: str = None
    status: str = None
    paid_amount: str = None
    returned_amount: str = None
    prepayment_id: str = None
    type: str = None
    from_voucher_id: str = None
    payment_method_name: str = None
