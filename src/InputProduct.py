from dataclasses import dataclass

from dataclasses_json import dataclass_json

@dataclass_json
@dataclass
class InputDetailProduct:
    Product_Id: str
    Product_Name: str
    Product_Quantity: int
    Unit: str
    Price_not_VAT: float

@dataclass_json
@dataclass
class InputProduct:
    Item_Id: str
    Item_Name: str
    Item_Quantity: int
    Product: list[InputDetailProduct]


