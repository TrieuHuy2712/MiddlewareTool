from abc import ABC, abstractmethod
from typing import List

from src.Model.Order import Order


class Web(ABC):
    @abstractmethod
    def get_orders_by_search(self) -> List[Order]:
        # Return orders from search
        pass

    @abstractmethod
    def get_orders_by_date(self) -> List[Order]:
        # Return orders from date and to date
        pass

    @abstractmethod
    def get_orders_by_search_and_date(self) -> List[Order]:
        # Return orders from search and between from and to date
        pass


class SAPO(ABC):
    @abstractmethod
    def get_orders_by_search(self) -> List[Order]:
        # Return orders from search
        pass

    @abstractmethod
    def get_orders_by_date(self) -> List[Order]:
        # Return orders from date and to date
        pass

    @abstractmethod
    def get_orders_by_search_and_date(self) -> List[Order]:
        # Return orders from search and between from and to date
        pass
