from typing import List

from src.Enums import OrderStatus


class OrderRequest:
    orders: List[str] = []
    status: OrderStatus
    from_date: str = None
    to_date: str = None
