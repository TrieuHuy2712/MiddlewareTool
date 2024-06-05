import json
import math
from typing import List

import requests

from src.Enums import SearchType
from src.IRetreiveOrder import Web
from src.Model.Order import Order
from src.OrderRequest import OrderRequest
from src.utils import set_up_logger, get_item_information, get_value_of_config, parse_time_format_of_web


class APIWebOrder(Web):
    def __init__(self, order: OrderRequest):
        self.logging = set_up_logger("Middleware_Tool")
        self.orders = []
        self.from_date = parse_time_format_of_web(order.from_date)
        self.to_date = parse_time_format_of_web(order.to_date)
        self.to_search_order = order.orders
        self.payment_methods = []
        self.item_information = get_item_information()
        self.cookies = self.authentication()
        self.meta_page = {}
        self.request_type = SearchType.SearchOrder

    def get_orders_by_search(self) -> List[Order]:
        self.request_type = SearchType.SearchOrder
        try:
            self.filter_orders_date_time()
            return self.orders
        except Exception as e:
            self.logging.error(msg=f"[Search] API Web Order got error by search: {e}")

    def get_orders_by_date(self) -> List[Order]:
        self.request_type = SearchType.DateOrder
        try:
            self.filter_orders_date_time()
            return self.orders
        except Exception as e:
            self.logging.error(msg=f"[Date] API Web Order got error by search: {e}")

    def get_orders_by_search_and_date(self) -> List[Order]:
        self.request_type = SearchType.DateOrder
        try:
            self.filter_orders_date_time()
            return self.orders
        except Exception as e:
            self.logging.error(msg=f"[Search and Date] API Web Order got error by search: {e}")

    def authentication(self):
        url = f"{get_value_of_config('api_url')}/login/"
        payload = f"email={get_value_of_config('website_login')}&password={get_value_of_config('website_password')}"
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        response = requests.post(url=url, headers=headers, data=payload)
        return response.cookies.get_dict()

    def filter_orders_date_time(self):
        self._process_orders_from_page(1)
        for page in range(2, self.meta_page["total_page"] + 1):
            self._process_orders_from_page(page)

    def _process_orders_from_page(self, page):
        list_orders = self._get_list_order_from_page(page)
        self.orders.extend(list_orders)
        self.to_search_order.extend(order.code for order in list_orders)

    def _get_list_order_from_page(self,page):
        params = self.prepare_params_list_orders()
        order_request = requests.get(f"{get_value_of_config('api_url')}/api/v1/orders/all?"
                                     f"time__icontains={params.get('time_request', '')}"
                                     f"&uid__icontains={params.get('order_request', '')}"
                                     f"&page={page}",
                                     cookies=self.cookies)
        parse_json = json.loads(order_request.text)["orders"]

        if self.meta_page.get('total', None) is None:
            self.meta_page["total"] = json.loads(order_request.text)['total']
            self.meta_page["current_page"] = json.loads(order_request.text)['page']
            self.meta_page["total_page"] = math.ceil(self.meta_page.get("total") / 10)

        return [Order.from_dict(order) for order in parse_json]

    def prepare_params_list_orders(self):
        orders = ""
        time = ""
        if self.request_type == SearchType.SearchOrder or self.request_type == SearchType.SearchDateOrder:
            orders = self.to_search_order

        if self.request_type == SearchType.DateOrder or self.request_type == SearchType.SearchDateOrder:
            time = f"{self.from_date} / {self.to_date}"

        return {"order_request": orders, "time_request": time}



