from dataclasses import dataclass

from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class Address:
    id: str = None
    created_on: str = None
    modified_on: str = None
    country: str = None
    city: str = None
    district: str = None
    ward: str = None
    address1: str = None
    address2: str = None
    zip_code: str = None
    email:str = None
    first_name: str = None
    last_name:str = None
    full_name:str = None
    label: str = None
    phone_number: str = None
    status: str = None
