from abc import ABC, abstractmethod
from typing import List

from src.AutomationMisaOrder import AutomationMisaOrder
from src.AutomationSapoOrder import AutomationSapoOrder
from src.AutomationWebOrder import AutomationWebOrder
from src.Enums import SapoShop
from src.Model.Order import Order
from src.OrderRequest import OrderRequest


class OrderFactory(ABC):
    @abstractmethod
    def create_web_order(self, order: OrderRequest):
        pass

    @abstractmethod
    def create_sapo_order(self, order: OrderRequest, shop: SapoShop):
        pass

    def submit_order(self, orders: List[Order]):
        auto_misa = AutomationMisaOrder(orders=orders)
        auto_misa.send_orders_to_misa()


class OrderAutoFactory(OrderFactory):
    def create_web_order(self, order: OrderRequest):
        return AutomationWebOrder()

    def create_sapo_order(self, order: OrderRequest, shop: SapoShop):
        return AutomationSapoOrder(order, shop)


class OrderAPIFactory(OrderFactory):
    def create_web_order(self):
        pass

    def create_sapo_order(self, shop: SapoShop):
        pass