from abc import ABC, abstractmethod
from typing import List

from src.APIWebOrder import APIWebOrder
from src.AutomationMisaOrder import AutomationMisaOrder
from src.AutomationSapoOrder import AutomationSapoOrder
from src.AutomationWebOrder import AutomationWebOrder
from src.Enums import SapoShop, Category, Channel
from src.MISA_Implementation.AutomationMisaOrderFromSAPO import AutomationMisaOrderFromSAPO
from src.MISA_Implementation.AutomationMisaOrderFromWEB import AutomationMisaOrderFromWEB
from src.Model.Order import Order
from src.OrderRequest import OrderRequest


class OrderFactory(ABC):

    @abstractmethod
    def create_web_order(self, order: OrderRequest):
        pass

    @abstractmethod
    def create_sapo_order(self, order: OrderRequest, shop: SapoShop):
        pass

    def submit_order(self, orders: List[Order], state_channel: Channel):
        if state_channel == Channel.SAPO:
            auto_misa = AutomationMisaOrderFromSAPO(orders=orders)
        elif state_channel == Channel.WEB:
            auto_misa = AutomationMisaOrderFromWEB(orders=orders)
        else:
            raise ValueError("Invalid method")
        auto_misa.send_orders_to_misa()

    @staticmethod
    def set_category_request(request: Category):
        if request == Category.AUTO:
            return OrderAutoFactory()
        else:
            return OrderAPIFactory()


class OrderAutoFactory(OrderFactory):
    # Channel : Web
    def create_web_order(self, order: OrderRequest):
        return AutomationWebOrder()

    def create_sapo_order(self, order: OrderRequest, shop: SapoShop):
        return AutomationSapoOrder(order, shop)


class OrderAPIFactory(OrderFactory):
    def create_web_order(self, order: OrderRequest):
        return APIWebOrder(order)

    def create_sapo_order(self, shop: SapoShop):
        pass