from enum import Enum


class SapoShop(Enum):
    QuocCoQuocNghiepShop = 0
    ThaoDuocGiang = 1

class SearchType(Enum):
    SearchOrder = 0
    DateOrder = 1
    SearchDateOrder = 2


class Channel(Enum):
    Auto = 0
    API = 1
