from dataclasses import dataclass
from typing import Optional

from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class DiscountItem:
    source: str
    rate: str
    value: str
    amount: str
    reason: str = None
    promotion_redemption_id: str = None
    promotion_condition_item_id: str = None
