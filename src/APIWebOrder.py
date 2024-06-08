import json
import math
import re
from typing import List

import requests

from src.Enums import SearchType
from src.Exceptions import ItemError
from src.IRetreiveOrder import Web
from src.InputProduct import InputDetailProduct
from src.Model.Item import CompositeItem
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
        self.products = self.__get_product_information__()
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
        self.request_type = SearchType.SearchDateOrder
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
        for order in list_orders:
            self.__update_order_information__(order)
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
            orders = ':'.join(self.to_search_order)

        if self.request_type == SearchType.DateOrder or self.request_type == SearchType.SearchDateOrder:
            time = f"{self.from_date} / {self.to_date}"

        return {"order_request": orders, "time_request": time}

    @staticmethod
    def __remove_letters_and_spaces__(input_string):
        # Sử dụng biểu thức chính quy để loại bỏ các ký tự chữ cái và khoảng trắng
        result = re.sub(r'[a-zA-Zđ\s,]', '',  input_string)
        return result

    def __update_order_information__(self, order: Order):
        for order_line in order.order_line_items:
            tax_amount = 0
            order_line.price = self.__remove_letters_and_spaces__(order_line.price)
            order_line.discount_amount = 0
            order_line.distributed_discount_amount = 0

            # Check SKU of line_item not equal at first one of composite
            order_line.is_composite = True

            # Update base price from excel file
            for composite_item in order_line.composite_item_domains:
                composite_item.quantity = int(composite_item.original_quantity) * int(order_line.quantity)
                composite_item.unit = self.__get_product_details__(composite_item.sku).Unit
                composite_item.discount = self.__calculate_discount_rate__(base_price=self.__get_base_price_by_sku(composite_item.sku),
                                                                           sale_price=composite_item.price)
                composite_item.price = self.__get_base_price_by_sku(composite_item.sku)

                # Formula calculate VAT After Applying Discount into Product
                # VATTax =  (BasePrice - (BasePrice * Discount /100))  * Quantity * 10%
                tax_amount += (composite_item.price - (composite_item.price * float(composite_item.discount) / 100)) * composite_item.quantity * 0.1

            order_line.tax_amount = tax_amount
            base_item_price = sum(float(composite_item.price)*composite_item.quantity for composite_item in order_line.composite_item_domains)
            order_line.discount_rate = self.__calculate_discount_rate__(base_price=base_item_price, sale_price=order_line.price)

    def __get_product_information__(self):
        product_detail = sum([prod.Product for prod in self.item_information], [])
        return product_detail

    def __get_product_details__(self, sku) -> InputDetailProduct:
        try:
            return [item for item in self.products if item.Product_Id == sku][0]
        except Exception:
            raise ItemError(message=f"Cannot found sku {sku} from resource. Please check again.")

    def __get_base_price_by_sku(self, sku) -> float:
        return float(self.__get_product_details__(sku).Price_not_VAT)

    @staticmethod
    def __calculate_discount_rate__(base_price, sale_price):
        sale_price_before_vat = float(sale_price) / 1.1
        return str(round((base_price - sale_price_before_vat)/base_price * 100, 2))



