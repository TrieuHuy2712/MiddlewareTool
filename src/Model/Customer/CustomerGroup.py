from dataclasses import dataclass
from typing import Optional

from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class CustomerGroup:
    id: str
    tenant_id: str
    created_on: str
    modified_on: str
    name: str
    name_translate: str
    status: str
    is_default: bool
    code: str
    default_payment_term_id: str = None
    default_payment_method_id: str = None
    default_tax_type_id: str = None
    default_discount_rate: str = None
    default_price_list_id: str = None
    note: str = None
