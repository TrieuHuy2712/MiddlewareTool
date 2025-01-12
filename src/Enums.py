from enum import Enum


class SapoShop(Enum):
    QuocCoQuocNghiepShop = 0
    ThaoDuocGiang = 1

class SearchType(Enum):
    SearchOrder = 0
    DateOrder = 1
    SearchDateOrder = 2


class Category(Enum):
    AUTO = 0
    API = 1


class Channel(Enum):
    WEB = 0
    SAPO = 1

class OrderStatus(Enum):
    SHIPPING = 0
    COMPLETE = 1
