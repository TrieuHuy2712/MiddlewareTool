from dataclasses import dataclass
from typing import List, Optional

from dataclasses_json import dataclass_json

from src.Model.Customer.Address import Address
from src.Model.Customer.CustomerGroup import CustomerGroup
from src.Model.Customer.SaleOrder import SaleOrder


@dataclass_json
@dataclass
class Customer:
    id: str = None
    tenant_id: str = None
    default_location_id: str = None
    created_on: str = None
    modified_on: str = None
    code: str = None
    name: str = None
    dob: str = None
    sex: str = None
    description: str = None
    email: str = None
    fax: str = None
    phone_number: str = None
    tax_number: str = None
    website: str = None
    customer_group_id: str = None
    group_name: str = None
    assignee_id: str = None
    default_payment_term_id: str = None
    default_payment_method_id: str = None
    default_tax_type_id: str = None
    default_discount_rate: str = None
    default_price_list_id: str = None
    tags: List[str] = None
    addresses: List[Address] = None
    contacts: List[str] = None
    notes: List[str] = None
    customer_group: CustomerGroup = None
    status: str = None
    is_default: bool = None
    debt: int = None
    apply_incentives: str = None
    total_expense: str = None
    sale_order: SaleOrder = None
