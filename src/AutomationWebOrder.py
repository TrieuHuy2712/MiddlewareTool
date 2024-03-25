import time
from typing import List

from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select

from src.IRetreiveOrder import Web
from src.Model.Customer.Address import Address
from src.Model.Customer.Customer import Customer
from src.Model.Fulfillment.Fulfillment import Fulfillment
from src.Model.Fulfillment.FulfillmentItem import FulfillmentItem
from src.Model.Item import Item, CompositeItem
from src.Model.Order import Order
from src.Singleton.AppConfig import AppConfig
from src.utils import set_up_logger, get_value_of_config, attempt_check_exist_by_xpath, \
    attempt_check_can_clickable_by_xpath, check_element_can_clickable, check_element_exist


class AutomationWebOrder(Web):
    def __init__(self):
        self.driver = AppConfig().chrome_driver
        self.is_processed = False
        self.logging = set_up_logger("Middleware_Tool")
        self.orders = []

    def get_orders_by_search(self, orders: List[str]):
        try:
            url = get_value_of_config("website_url")
            self.driver.get(url)

            # Authentication
            self.authentication()
            self.driver.maximize_window()

            # Switch to order admin page
            time.sleep(2)
            self.driver.get(f"{url}/order")

            for order in orders:
                self.open_website(order)
                time.sleep(2)

        except Exception as e:
            self.logging.critical(f"Automation Web Order got error: {e}")
        finally:
            AppConfig().destroy_instance()
            return self.orders

    def authentication(self):
        self.input_login_email()
        self.input_login_password()
        self.click_login_button()

    def input_login_email(self):
        email = get_value_of_config("website_login")
        self.driver.find_element(By.XPATH, '//*[@id="kt_sign_in_form"]/div[2]/input[1]').send_keys(email)

    def input_login_password(self):
        password = get_value_of_config("website_password")
        self.driver.find_element(By.XPATH, '//*[@id="kt_sign_in_form"]/div[3]/input').send_keys(password)

    def click_login_button(self):
        self.driver.find_element(By.XPATH, '//*[@id="kt_sign_in_submit"]').click()

    def open_website(self, order):
        # Search order
        self.search_order(order)

    def search_order(self, order):
        state_complete_url = f'{get_value_of_config("website_url")}/order/?state=complete&payment='
        self.driver.get(state_complete_url)

        # Searching
        search_input_xpath = '//*[@id="m_form_search"]'
        attempt_check_exist_by_xpath(search_input_xpath)

        search_input = self.driver.find_element(By.XPATH, search_input_xpath)
        search_input.send_keys(order)
        search_input.send_keys(Keys.F9)

        order_xpath = '//table[@id="m-datatable-list"]/tbody/tr/td[@data-field="uid"]/span/a'
        attempt_check_can_clickable_by_xpath(order_xpath)
        self.driver.find_element(By.XPATH, order_xpath).click()
        self.get_order_json()

    def get_order_json(self):
        id = self.driver.current_url.replace(f'{get_value_of_config("website_url")}/order/', '')
        created_on = self.driver.find_element(By.XPATH,
                                              '//table[contains(@class,"m-datatable")]/tbody/tr/td[contains(.,'
                                              '"Thời Gian Đặt Hàng")]/following-sibling::td').text

        # Go to update button
        update_btn_xpath = '//button/i[contains(.,"Sửa")]'
        attempt_check_can_clickable_by_xpath(update_btn_xpath)
        self.driver.find_element(By.XPATH, update_btn_xpath).click()

        # Payment
        code = self.driver.find_element(By.XPATH, '//input[@name="uid"]').get_attribute(
            'value')
        total_cost = self.driver.find_element(By.XPATH, '//*[@id="total_money"]').text
        status_payment = Select(self.driver.find_element(By.NAME, 'state')).first_selected_option.text
        method_payment = Select(self.driver.find_element(By.NAME, 'payment_method')).first_selected_option.text

        # Customer
        customer_name = self.driver.find_element(By.XPATH, '//*[@id="customer_name"]').get_attribute('value')
        customer_email = self.driver.find_element(By.XPATH, '//*[@id="customer_email"]').get_attribute('value')
        customer_phone = self.driver.find_element(By.XPATH, '//*[@id="customer_phone"]').get_attribute('value')
        customer_province = Select(self.driver.find_element(By.NAME, 'customer_province')).first_selected_option.text
        customer_district = Select(self.driver.find_element(By.NAME, 'customer_district')).first_selected_option.text
        customer_ward = Select(self.driver.find_element(By.NAME, 'customer_ward')).first_selected_option.text
        customer_address = self.driver.find_element(By.XPATH, '//*[@id="customer_address"]').get_attribute('value')
        customer_note = self.driver.find_element(By.XPATH, '//*[@id="customer_remark"]').get_attribute('value')

        # Shipment
        service_shipment = self.driver.find_element(By.XPATH,
                                                    '//*[@id="select2-shiping_service-container"]').get_attribute(
            'title')

        order = Order(
            id=id,
            code=code,
            created_on=created_on,
            status=status_payment,
            customer_data=Customer(name=customer_name, email=customer_email, phone_number=customer_phone),
            fulfillment_status=status_payment,
            received_status=status_payment,
            payment_status=status_payment,
            return_status="",
            phone_number=customer_phone,
            total_discount="",
            total_tax="",
            order_line_items=[],
            billing_address=Address(country='Việt Nam', city=customer_province, district=customer_district,
                                    ward=customer_ward, phone_number=customer_phone,
                                    address1=customer_address),
            total=total_cost

        )

        fulfillment = Fulfillment
        # Fulfillment line items
        fulfillment_line_items = []
        table = self.driver.find_element(By.XPATH, '//*[@id="body_order"]/div[2]/table')
        rows = table.find_elements(By.XPATH, "tbody/tr")  # get all of the rows in the table
        for row in rows:
            # Get name column item
            col = row.find_element(By.XPATH, "td[1]")
            item_name = col.find_element(By.XPATH, 'a').text

            # Quantity
            col = row.find_element(By.XPATH, "td[2]")
            quantity = col.find_element(By.NAME, "quantity").get_attribute('value')

            # Unit price - Đn giá
            col = row.find_element(By.XPATH, "td[3]")
            unit_price = col.find_element(By.CLASS_NAME, "product_price").get_attribute('value')

            # Price - Thành tiền
            col = row.find_element(By.XPATH, "td[4]")
            price = col.find_element(By.TAG_NAME, "span").text

            order.order_line_items.append(Item(product_name=item_name, quantity=quantity, price=unit_price))
            fulfillment_line_items.append(
                FulfillmentItem(product_name=item_name, quantity=quantity, base_price=unit_price, line_amount=price))

        for fullfill_item in fulfillment_line_items:
            # SKU
            fullfill_item.sku = self.get_sku_item(fullfill_item.product_name)

        for order_item in order.order_line_items:
            # Check combo
            self.search_detail_item(order_item.product_name)
            combo_tag = f'//table[@id="m-datatable-list"]/tbody/tr/td/span/a[contains(.,"Edit Combo")]'
            if check_element_exist(combo_tag, By.XPATH):
                self.driver.find_element(By.XPATH, combo_tag).click()
                order_item.composite_item_domains = self.get_composite_item()

        fulfillment.fulfillment_line_items = fulfillment_line_items
        fulfillment.notes = customer_note
        order.fulfillments = [fulfillment]
        self.orders.append(order)

    def get_sku_item(self, product_name):
        self.search_detail_item(product_name)
        self.click_to_detail_page(product_name)
        sku_xpath = '//*[@id="sku"]'
        attempt_check_exist_by_xpath(sku_xpath)
        return self.driver.find_element(By.XPATH, sku_xpath).get_attribute('value')

    def search_detail_item(self, product_name):
        # Get detail
        self.driver.get(f'{get_value_of_config("website_url")}/product/')
        # Searching
        search_item_xpath = '//*[@id="m_form_search"]'
        attempt_check_exist_by_xpath(search_item_xpath)

        search_input = self.driver.find_element(By.XPATH, search_item_xpath)
        search_input.send_keys(product_name)

        # Search item from product page
        search_button_xpath = '//*[@id="search_item"]'
        attempt_check_can_clickable_by_xpath(search_button_xpath)
        self.driver.find_element(By.XPATH, search_button_xpath).click()

    def click_to_detail_page(self, product_name):
        item_xpath = f'//table[@id="m-datatable-list"]/tbody/tr/td/span/a[contains(.,"{product_name}")]'
        attempt_check_can_clickable_by_xpath(item_xpath)
        self.driver.find_element(By.XPATH, item_xpath).click()

    def get_composite_item(self) -> List[CompositeItem]:
        list_composite_item = []
        table = self.driver.find_element(By.XPATH, '//*[@id="vi"]/div/div[3]')
        rows = table.find_elements(By.CLASS_NAME, "item")  # get all rows in the table
        for row in rows:
            # Product name
            product_name = row.find_element(By.XPATH, '//b[@class="name"]').text
            price = row.find_element(By.XPATH, '//input[@class="price"]').get_attribute('value')
            discount = row.find_element(By.XPATH, '//input[@class="discount"]').get_attribute('value')
            original_quantity = row.find_element(By.XPATH, '//input[@class="quantity"]').get_attribute('value')

            list_composite_item.append(
                CompositeItem(
                    product_name=product_name,
                    price=price,
                    discount=discount,
                    original_quantity=original_quantity,
                ))
        for item in list_composite_item:
            item.product_id = self.get_sku_item(item.product_name)
        return list_composite_item
