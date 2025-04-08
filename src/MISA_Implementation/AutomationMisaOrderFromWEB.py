import threading
import time
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pandas as pd
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By

from src.AutomationMisaOrder import AutomationMisaOrder
from src.Exceptions import OrderError
from src.Interface.IDetailInvoice import IDetailInvoice
from src.Model.Item import Item
from src.Model.Order import Order
from src.Singleton.AppConfig import AppConfig
from src.utils import attempt_check_exist_by_xpath, get_value_of_config, attempt_check_can_clickable_by_xpath, \
    check_element_exist, parse_time_format_webAPI

list_added_items = []


class AutomationMisaOrderFromWEB(AutomationMisaOrder, IDetailInvoice):
    _thread_local = threading.local()  # Biến lưu WebDriver riêng cho từng thread

    def get_driver(self):
        """Trả về WebDriver riêng cho từng thread"""
        if not hasattr(self._thread_local, "driver"):
            self._thread_local.driver = AppConfig.get_chrome_driver()
        return self._thread_local.driver

    def __init__(self, orders: list[Order]):
        super().__init__(orders)

    def send_orders_to_misa(self):
        try:
            with ThreadPoolExecutor(max_workers=len(self.chunk_orders)) as executor:
                futures = {executor.submit(self.send_orders, i + 1, chunk) for i, chunk in enumerate(self.chunk_orders)}
            self.logging.info(
                msg=f"[Misa-Web] Missing orders in running: {','.join({o.code for o in self._get_list_missing_orders()})}")
            self.logging.info(
                msg=f"[Misa-Web] Retry for missing orders: {','.join({o.code for o in self._get_list_missing_orders()})}")

            while len(self._get_list_missing_orders()) > 0 and self.attempt <= 10:
                self.missing_orders = self._get_list_missing_orders()
                self.chunk_orders = [chunk.tolist() for chunk in
                                     np.array_split(self.missing_orders, int(get_value_of_config("chunk_size")))
                                     if len(chunk) > 0]
                self.logging.info(
                    msg=f"[Misa-WEB] Retry create missing order at {self.attempt}")
                self.send_orders_to_misa()
                self.attempt = self.attempt + 1
        except Exception as e:
            self.logging.critical(msg=f"[Misa-WEB]Automation Misa Order got internal error at : {e}")
        finally:
            self.logging.info(
                msg=f"[Misa-WEB] Not handle orders: {','.join(o.code for o in self.orders if o.code not in self.handle_orders)}")
            AppConfig().destroy_instance()
            self.logging.info(msg=f"[Misa-WEB] Completed automation Misa Order at all thread.")

    def send_orders(self, chunk_id, orders: list[Order]):
        try:
            driver = self.get_driver()
            self.logging.info(
                msg=f"[Misa-SAPO] Start automation Misa Order at thread {chunk_id} at driver {driver.session_id}")
            self._open_website(chunk_id, driver=driver)
            time.sleep(3)
            self._authentication(driver=driver)
            driver.maximize_window()
            self._go_to_internal_accounting_data_page(driver=driver)
            self.handler_create_list_invoice(orders, driver=driver)
            self.logging.info(
                msg=f"[Misa-Web] Missing orders in running: {','.join({o.code for o in self._get_list_missing_orders()})}")
            self.logging.info(
                msg=f"[Misa-Web] Retry for missing orders: {','.join({o.code for o in self._get_list_missing_orders()})}")
        except Exception as e:
            self.logging.critical(msg=f"[Misa-WEB]Automation Misa Order got internal error at : {e}")
        finally:
            self.logging.info(
                msg=f"[Misa-SAPO] Not handle orders: "
                    f"{','.join(o.code for o in self.orders if o.code not in self.handle_orders)}")
            self.close_driver()
            self.logging.info(msg=f"[Misa-WEB] Completed automation Misa Order at thread {chunk_id}")

    def handler_create_list_invoice(self, orders: list[Order], driver):
        for order in orders:
            try:
                self._go_to_sale_page(driver=driver)
                self.create_detail_invoice(order, driver=driver)
                self._go_to_warehouse_page(driver=driver)
                self.create_detail_warehouse_invoice(order, driver=driver)
                self.handle_orders.append(order.code)  # Add infor handled orders
            except OrderError as ex:
                self.logging.critical(msg=f"[Misa-WEB]Automation Misa Order {order.code} got error at : {ex.message}")
                self.missing_orders.append(order)  # Add infor error orders
                self._open_website(thread_id="1", driver=driver)

    def create_detail_invoice(self, order: Order, driver):
        try:
            # Input customer name
            input_customer_xpath = ('//div[text()="Tên khách hàng"]/parent::div/parent::div/parent::div'
                                    '/following-sibling::div//input')
            attempt_check_exist_by_xpath(input_customer_xpath, driver=driver)
            driver.find_element(By.XPATH, input_customer_xpath).send_keys(
                f"{get_value_of_config('environment')}Khách hàng lẻ không lấy hóa đơn (Bán hàng qua Website: giangs.vn)")

            # Input detail
            number_items = sum(
                len(item.composite_item_domains) if item.is_composite else 1 for item in order.order_line_items)
            add_line_button_xpath = '//div[normalize-space(text())="Thêm dòng"]/ancestor::button'

            for i in range(0, number_items):
                self._action_click_with_xpath_(add_line_button_xpath, driver=driver)
                time.sleep(2)

            current_row = 1
            for item in order.order_line_items:
                for it in item.composite_item_domains:
                    self.__set_data_for_table(it.sku, it.quantity, it.discount, current_row, driver=driver)
                    current_row += 1

            # Add commercial discount
            self.__set_invoice_appendix(order=order, driver=driver)
            list_added_items = []
            # Save invoice
            save_button_xpath = '//button[@shortkey-target="Save"]'
            self._action_click_with_xpath_(save_button_xpath, driver=driver)
            self._escape_current_invoice(driver=driver)
            self.logging.info(f"[Misa Sale Order] Created order {order.code}.")
        except Exception as e:
            self.logging.error(msg=f"[Misa Sale Order] Created order {order.code} failed.")
            raise OrderError(message=f"Have error in create Misa order. {e}")

    def create_detail_warehouse_invoice(self, order: Order, driver):
        try:
            # Input customer name
            input_customer_xpath = '//div[text()="Tên khách hàng"]/parent::div/parent::div/parent::div/following-sibling::div//input'
            attempt_check_exist_by_xpath(input_customer_xpath, driver=driver)
            driver.find_element(By.XPATH, input_customer_xpath).send_keys(
                f"{get_value_of_config('environment')} Mã đơn hàng: {order.code}(Bán hàng qua Website: giangs.vn)")

            # Input certificate number
            certificate_number_xpath = '//div[text()="Số chứng từ"]/parent::div/parent::div/parent::div/following-sibling::div//input'
            attempt_check_exist_by_xpath(certificate_number_xpath, driver=driver)

            current_certificate_number = driver.find_element(By.XPATH, certificate_number_xpath).get_attribute('value')
            unix_time = str(int(time.time() * 1000))
            new_certificate_number = current_certificate_number[:7] + '-' + unix_time

            driver.find_element(By.XPATH, certificate_number_xpath).send_keys(Keys.CONTROL + "a")
            driver.find_element(By.XPATH, certificate_number_xpath).send_keys(Keys.DELETE)

            driver.find_element(By.XPATH, certificate_number_xpath).send_keys(new_certificate_number)

            # Input detail
            sku_quantity = self.__calculate_warehouse_quantity_item__(order.order_line_items)
            add_line_button_xpath = '//div[normalize-space(text())="Thêm dòng"]/ancestor::button'

            for i in range(0, len(sku_quantity)):
                attempt_check_exist_by_xpath(add_line_button_xpath, driver=driver)
                time.sleep(2)

            current_row = 1
            for sku, quantity in sku_quantity.items():
                if current_row > 1:
                    driver.find_element(By.XPATH, add_line_button_xpath).click()
                    time.sleep(2)
                self.__set_warehouse_data_for_table(sku, quantity, current_row, driver=driver)
                current_row += 1

            # Add commercial discount
            # self.set_invoice_appendix(order=order)
            # Save invoice
            save_button_xpath = '//button[@shortkey-target="Save"]'
            self._action_click_with_xpath_(save_button_xpath, driver=driver)
            self._escape_current_invoice(driver=driver)
            self.logging.info(f"[Misa Warehouse] Created order {order.code}.")
        except Exception as e:
            self.logging.error(msg=f"[Misa Warehouse] Created order {order.code} failed. got error: {e} Retry again")
            self._escape_current_invoice(driver=driver)
            self._go_to_warehouse_page(driver=driver)
            self.create_detail_warehouse_invoice(order, driver=driver)

    def __set_data_for_table(self, sku, quantity, discount_rate, current_row, driver):
        # SKU Code
        sku_xpath = f'//table[@class="ms-table"]/tbody/tr[{current_row}]/td[3]/div'
        self._action_click_with_xpath_(sku_xpath, driver=driver)
        attempt_check_can_clickable_by_xpath(f'{sku_xpath}//input', driver=driver)
        col = driver.find_element(By.XPATH, f'{sku_xpath}//input')
        col.send_keys(sku)
        list_added_items.append(sku) if sku not in list_added_items else time.sleep(10)
        col.send_keys(Keys.TAB)

        # Quantity
        quantity_xpath = f'//table[@class="ms-table"]/tbody/tr[{current_row}]/td[8]/div'
        self._action_click_with_xpath_(quantity_xpath, driver=driver)
        attempt_check_can_clickable_by_xpath(f'{quantity_xpath}//input', driver=driver)
        col = driver.find_element(By.XPATH, f'{quantity_xpath}//input')
        col.send_keys(quantity)
        col.send_keys(Keys.TAB)

        # Discount amount
        discount_amount_xpath = f'//table[@class="ms-table"]/tbody/tr[{current_row}]/td[11]/div'
        self._action_click_with_xpath_(discount_amount_xpath, driver=driver)
        attempt_check_can_clickable_by_xpath(f'{discount_amount_xpath}//input', driver=driver)
        col = driver.find_element(By.XPATH, f'{discount_amount_xpath}//input')
        col.send_keys(discount_rate)
        col.send_keys(Keys.TAB)

        # Check SKU is valid
        error_icon = (f'//table[@class="ms-table"]/tbody/tr[{current_row}]/td[3]'
                      f'//div[contains(@class,"cell-error-icon")]')
        if check_element_exist(error_icon, driver=driver):
            self._escape_current_invoice(driver=driver)
            self._action_click_with_xpath_('//div[@id="message-box"]//div[contains(text(),"Không")]/parent::button'
                                           , driver=driver)
            raise OrderError(message=f"[Misa] Cannot found the Product {sku} in the system.")

        # Promotion
        if discount_rate == "100.0":
            promotion_button_xpath = f'//table[@class="ms-table"]/tbody/tr[{current_row}]/td[5]/div'
            self._action_click_with_xpath_(promotion_button_xpath, driver=driver)

    def __set_warehouse_data_for_table(self, sku, quantity, current_row, driver):
        # SKU Code
        sku_xpath = f'//table[@class="ms-table"]/tbody/tr[{current_row}]/td[3]/div'
        self._action_click_with_xpath_(sku_xpath, driver=driver)
        attempt_check_can_clickable_by_xpath(f'{sku_xpath}//input', driver=driver)
        col = driver.find_element(By.XPATH, f'{sku_xpath}//input')
        col.send_keys(sku)
        col.send_keys(Keys.TAB)

        # Warehouse
        warehouse_xpath = f'//table[@class="ms-table"]/tbody/tr[{current_row}]/td[5]/div'
        self._action_click_with_xpath_(warehouse_xpath, driver=driver)
        attempt_check_can_clickable_by_xpath(f'{warehouse_xpath}//input', driver=driver)
        col = driver.find_element(By.XPATH, f'{warehouse_xpath}//input')
        col.send_keys(get_value_of_config("warehouse_id"))
        time.sleep(2)
        col.send_keys(Keys.TAB)

        # Quantity
        quantity_xpath = f'//table[@class="ms-table"]/tbody/tr[{current_row}]/td[9]/div'
        self._action_click_with_xpath_(quantity_xpath, driver=driver)
        attempt_check_can_clickable_by_xpath(f'{quantity_xpath}//input', driver=driver)
        col = driver.find_element(By.XPATH, f'{quantity_xpath}//input')
        col.send_keys(quantity)
        col.send_keys(Keys.TAB)

        # Check SKU is valid
        error_icon = (f'//table[@class="ms-table"]/tbody/tr[{current_row}]/td[3]'
                      f'//div[contains(@class,"cell-error-icon")]')
        if check_element_exist(error_icon, driver=driver):
            self._escape_current_invoice(driver=driver)
            self._action_click_with_xpath_('//div[@id="message-box"]//div[contains(text(),"Không")]/parent::button'
                                           , driver=driver)
            raise OrderError(message=f"[Misa] Cannot found the Product {sku} in the system.")

    def __set_invoice_appendix(self, order: Order, driver):
        created_date = parse_time_format_webAPI(order.created_on)
        note_button_xpath = '//div[normalize-space(text())="Thêm ghi chú"]/parent::button'

        # Click add new note line in the table
        self._action_click_with_xpath_(note_button_xpath, driver=driver)
        note_xpath = f'//table[@class="ms-table"]/tbody/tr[last()]/td[4]/div'
        self._action_click_with_xpath_(note_xpath, driver=driver)
        # Get the last line of table
        attempt_check_can_clickable_by_xpath(f'{note_xpath}//input', driver=driver)
        col = driver.find_element(By.XPATH, f'{note_xpath}//input')
        col.send_keys(f"Bổ sung đơn hàng ngày "
                      f"{created_date.day}/{created_date.month}/{created_date.year} "
                      f"(Mã đơn hàng: {order.code})")

    @staticmethod
    def __calculate_warehouse_quantity_item__(lines_items: list[Item]) -> dict:
        composite_items = sum([item.composite_item_domains for item in lines_items], [])
        df = pd.DataFrame(composite_items)
        result_df = df.groupby('sku')['quantity'].sum().reset_index()
        return result_df.set_index('sku').to_dict()['quantity']
