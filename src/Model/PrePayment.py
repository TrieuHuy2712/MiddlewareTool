from dataclasses import dataclass
from typing import Optional

from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class PrePayment:
    id: str
    payment_method_id: str = None
    paid_on: str = None
    amount: str = None
    account_id: str = None
    note: str = None
    created_on: str = None
    modified_on: str = None
    paid_amount: str = None
    status: str = None
    integrated: str = None
    status_before_cancelled: str = None
    bin: str = None
    card_type: str = None
    from_voucher_id: str = None
    beneficiary_account: str = None
    order_id: int = 0
    tenant_id: int = 0
    type: str = 'normal'
    reference: str = ""
    source: str = "customer_paid"
    returned_amount: int = 0
    payment_method_name: str = None
