from abc import ABC, abstractmethod
from typing import List

from src.Model.Order import Order


class IDetailInvoice(ABC):
    @abstractmethod
    def create_detail_invoice(self, order: Order, create_detail_invoice):
        pass

    @abstractmethod
    def create_detail_warehouse_invoice(self, orders: Order, driver):
        pass