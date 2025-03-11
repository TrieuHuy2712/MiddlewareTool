import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import numpy as np
import pandas as pd
from selenium.webdriver import Keys, ActionChains
from selenium.webdriver.common.by import By

from src.AutomationMisaOrder import AutomationMisaOrder
from src.Exceptions import OrderError
from src.Interface.IDetailInvoice import IDetailInvoice
from src.Model.Item import Item
from src.Model.MisaRequestTable import MisaRequestTable
from src.Model.Order import Order
from src.Singleton.AppConfig import AppConfig
from src.utils import attempt_check_exist_by_xpath, get_value_of_config, attempt_check_can_clickable_by_xpath, \
    check_element_exist, get_money_format, convert_money_string_to_float_of_MISA, string_to_float

list_added_items = []


class AutomationMisaOrderFromSAPO(AutomationMisaOrder, IDetailInvoice):
    _thread_local = threading.local()  # Biến lưu WebDriver riêng cho từng thread

    def __init__(self, orders: list[Order]):
        super().__init__(orders)

    def get_driver(self):
        """Trả về WebDriver riêng cho từng thread"""
        if not hasattr(self._thread_local, "driver"):
            self._thread_local.driver = AppConfig.get_chrome_driver()
        return self._thread_local.driver

    def send_orders_to_misa(self):
        try:
            with ThreadPoolExecutor(max_workers=len(self.chunk_orders)) as executor:
                futures = {executor.submit(self.send_orders, i + 1, chunk) for i, chunk in enumerate(self.chunk_orders)}
            self.logging.info(
                msg=f"[Misa-SAPO] Missing orders in running: {','.join({o.code for o in self._get_list_missing_orders()})}")
            self.logging.info(
                msg=f"[Misa-SAPO] Retry for missing orders: {','.join({o.code for o in self._get_list_missing_orders()})}")

            while len(self._get_list_missing_orders()) > 0 and self.attempt <= 10:
                self.missing_orders = self._get_list_missing_orders()
                self.chunk_orders = [chunk.tolist() for chunk in
                                     np.array_split(self.missing_orders, int(get_value_of_config("chunk_size")))
                                     if len(chunk) > 0]

                self.logging.info(
                    msg=f"[Misa-Sapo] Retry create missing order at {self.attempt}")  # Retry missing orders
                self.send_orders_to_misa()
                self.attempt = self.attempt + 1
        except Exception as e:
            self.logging.critical(msg=f"[Misa-SAPO] Automation Misa Order got internal error at : {e}")
        finally:
            self.logging.info(
                msg=f"[Misa-SAPO] Not handle orders: {','.join(o.code for o in self.orders if o.code not in self.handle_orders)}")
            AppConfig().destroy_instance()
            self.logging.info(msg=f"[Misa-SAPO] Completed automation Misa Order at all thread.")

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

        except Exception as e:
            self.logging.critical(msg=f"[Misa-SAPO]Automation Misa Order got internal error at : {e}")
        finally:
            self.logging.info(
                msg=f"[Misa-SAPO] Not handle orders: {','.join(o.code for o in self.orders if o.code not in self.handle_orders)}")
            # AppConfig().destroy_instance()
            self.close_driver()
            self.logging.info(msg=f"[Misa-SAPO] Completed automation Misa Order at thread {chunk_id}")

    def handler_create_list_invoice(self, orders: list[Order], driver):
        for order in orders:
            try:
                self._go_to_sale_page(driver=driver)
                self.create_detail_invoice(order, driver=driver)
                self._go_to_warehouse_page(driver=driver)
                self.create_detail_warehouse_invoice(order, driver=driver)
                self.handle_orders.append(order.code)  # Add infor handled orders
            except OrderError as ex:
                self.logging.critical(msg=f"[Misa-SAPO]Automation Misa Order {order.code} got error at : {ex.message}")
                self.missing_orders.append(order)  # Add infor error orders
                self._open_website(thread_id="1", driver=driver)

    def create_detail_invoice(self, order: Order, driver):
        try:
            # Input customer name
            input_customer_xpath = ('//div[text()="Tên khách hàng"]/parent::div/parent::div'
                                    '/parent::div/following-sibling::div//input')
            attempt_check_exist_by_xpath(input_customer_xpath, driver=driver)
            driver.find_element(By.XPATH, input_customer_xpath).send_keys(
                f"{get_value_of_config('environment')}Khách hàng lẻ không lấy hóa đơn (Bán hàng qua {order.source_name})")

            # Input detail
            number_items = sum(
                len(item.composite_item_domains) if item.is_composite else 1 for item in order.order_line_items)
            add_line_button_xpath = '//div[normalize-space(text())="Thêm dòng"]/ancestor::button'

            for i in range(0, number_items):
                self._action_click_with_xpath_(add_line_button_xpath, driver=driver)
                time.sleep(2)

            current_row = 1
            for item in order.order_line_items:
                if item.is_composite:
                    for it in item.composite_item_domains:
                        self.__set_data_for_table(
                            MisaRequestTable(
                                sku=it.sku,
                                quantity=it.quantity,
                                discount_rate=item.discount_rate,
                                current_row=current_row,
                                source_name=order.source_name,
                                price=item.price,
                                # line_amount=string_to_float(self._calculate_total_composite_price(order.order_line_items),
                                line_amount=string_to_float(item.price),
                                default_item_quantity=item.quantity,
                                discount_value=string_to_float(item.discount_value)
                            ), driver=driver)
                        current_row += 1
                else:
                    self.__set_data_for_table(
                        MisaRequestTable(
                            sku=item.sku,
                            quantity=item.quantity,
                            discount_rate=item.discount_rate,
                            current_row=current_row,
                            source_name=order.source_name,
                            price=item.price,
                            line_amount=string_to_float(item.price),  # Not in case composite will not separate
                            default_item_quantity=item.quantity,
                            discount_value=string_to_float(item.discount_value)
                        ), driver=driver)
                    current_row += 1

            # Add commercial discount
            self.__get_discount_amount(order=order, driver=driver)

            if any(len(order.order_line_items) != len(item.composite_item_domains)
                   or item.sku != item.composite_item_domains[0].sku for item in order.order_line_items):
                self.__set_order_balance(order, driver=driver)
            self.__set_invoice_appendix(order=order, driver=driver)
            list_added_items = []

            # Save invoice
            self._action_click_with_xpath_('//button[@shortkey-target="Save"]', driver=driver)  # save_button_xpath
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
                f"{get_value_of_config('environment')} Mã đơn hàng: {order.code}(Bán hàng qua {order.source_name})")

            # Input certificate number
            certificate_number_xpath = '//div[text()="Số chứng từ"]/parent::div/parent::div/parent::div/following-sibling::div//input'
            attempt_check_exist_by_xpath(certificate_number_xpath, driver=driver)

            current_certificate_number = driver.find_element(By.XPATH, certificate_number_xpath).get_attribute('value')
            unix_time = str(int(time.time()*1000))
            new_certificate_number = current_certificate_number[:7]+'-'+unix_time

            driver.find_element(By.XPATH, certificate_number_xpath).send_keys(Keys.CONTROL + "a")
            driver.find_element(By.XPATH, certificate_number_xpath).send_keys(Keys.DELETE)

            driver.find_element(By.XPATH, certificate_number_xpath).send_keys(new_certificate_number)

            # Input detail
            sku_quantity = self._calculate_warehouse_quantity_item_(order.order_line_items)
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
            self.logging.error(msg=f"[Misa Warehouse] Created order {order.code} failed.")
            raise OrderError(message=f"Have error in create Misa warehouse. {e}")

    def __set_data_for_table(self, request_table: MisaRequestTable, driver):

        # Default item quantity là số lượng mua hàng mặc định KHÔNG có nhân cho số lượng sản phâm trong combo

        # SKU Code
        sku_xpath = f'//table[@class="ms-table"]/tbody/tr[{request_table.current_row}]/td[3]/div'
        self._action_click_with_xpath_(sku_xpath, driver=driver)
        attempt_check_can_clickable_by_xpath(f'{sku_xpath}//input', driver=driver)
        col = driver.find_element(By.XPATH, f'{sku_xpath}//input')
        col.send_keys(request_table.sku)
        list_added_items.append(request_table.sku) if request_table.sku not in list_added_items else time.sleep(10)

        # Quantity
        quantity_xpath = f'//table[@class="ms-table"]/tbody/tr[{request_table.current_row}]/td[8]/div'
        self._action_click_with_xpath_(quantity_xpath, driver=driver)
        attempt_check_can_clickable_by_xpath(f'{quantity_xpath}//input', driver=driver)
        col = driver.find_element(By.XPATH, f'{quantity_xpath}//input')
        col.send_keys(request_table.quantity)

        # Discount ratio amount
        discount_amount_xpath = f'//table[@class="ms-table"]/tbody/tr[{request_table.current_row}]/td[11]/div'
        attempt_check_can_clickable_by_xpath(discount_amount_xpath, driver=driver)
        self._action_click_with_xpath_(discount_amount_xpath, driver=driver)
        attempt_check_can_clickable_by_xpath(f'{discount_amount_xpath}//input', driver=driver)
        col = driver.find_element(By.XPATH, f'{discount_amount_xpath}//input')
        col.send_keys(request_table.discount_rate)

        # Discount value amount
        # discount_amount_value_xpath = f'//table[@class="ms-table"]/tbody/tr[{request_table.current_row}]/td[12]/div'
        # attempt_check_can_clickable_by_xpath(discount_amount_value_xpath)
        # self._action_click_with_xpath_(discount_amount_value_xpath)
        # attempt_check_can_clickable_by_xpath(f'{discount_amount_value_xpath}//input')
        # col = driver.find_element(By.XPATH, f'{discount_amount_value_xpath}//input')
        # col.send_keys(round(request_table.discount_value / 1.1))

        # Discount PERCENTAGE value
        if (request_table.source_name == 'Lazada'
                or request_table.source_name == 'Tiki'
                or request_table.source_name == 'TiktokShop'):
            # Get total money - Thành tiền
            total_money_xpath = f'//table[@class="ms-table"]/tbody/tr[{request_table.current_row}]/td[10]//span'
            total_money_value = convert_money_string_to_float_of_MISA(
                driver.find_element(By.XPATH, total_money_xpath).text)
            discount_value = 0 if request_table.discount_value == 0 else round(
                total_money_value / request_table.line_amount * request_table.discount_value)

            # Giá trị Chiết khấu
            discount_value_xpath = f'//table[@class="ms-table"]/tbody/tr[{request_table.current_row}]/td[12]/div'
            attempt_check_can_clickable_by_xpath(discount_value_xpath, driver=driver)
            self._action_click_with_xpath_(discount_value_xpath, driver=driver)
            attempt_check_can_clickable_by_xpath(f'{discount_value_xpath}//input', driver=driver)
            col = driver.find_element(By.XPATH, f'{discount_value_xpath}//input')
            # col.send_keys(Keys.BACKSPACE)
            # col.send_keys(Keys.DELETE)
            actions = ActionChains(driver)
            actions.key_down(Keys.CONTROL).send_keys("a").key_up(Keys.CONTROL).perform()
            actions.send_keys(Keys.DELETE)
            col.send_keys(discount_value)
            col.send_keys(Keys.TAB)

        # Check SKU is valid
        error_icon = f'//table[@class="ms-table"]/tbody/tr[{request_table.current_row}]/td[3]//div[contains(@class,"cell-error-icon")]'
        if check_element_exist(error_icon, driver=driver):
            self._escape_current_invoice(driver=driver)
            self._action_click_with_xpath_('//div[@id="message-box"]//div[contains(text(),"Không")]/parent::button',
                                           driver=driver)
            raise OrderError(message=f"[Misa] Cannot found the Product {request_table.sku} in the system.")

        # Promotion
        if request_table.discount_rate == "100.0" or request_table.price == '0':
            promotion_button_xpath = f'//table[@class="ms-table"]/tbody/tr[{request_table.current_row}]/td[5]/div'
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
        col.send_keys(Keys.CONTROL + "a")
        col.send_keys(Keys.DELETE)
        time.sleep(2)
        col.send_keys(quantity)
        col.send_keys(Keys.TAB)

        # Check SKU is valid
        error_icon = f'//table[@class="ms-table"]/tbody/tr[{current_row}]/td[3]//div[contains(@class,"cell-error-icon")]'
        if check_element_exist(error_icon, driver=driver):
            self._escape_current_invoice(driver=driver)
            attempt_check_can_clickable_by_xpath(
                '//div[@id="message-box"]//div[contains(text(),"Không")]/parent::button', driver=driver)
            driver.find_element(By.XPATH,
                                '//div[@id="message-box"]//div[contains(text(),"Không")]/parent::button').click()
            raise OrderError(message=f"[Misa] Cannot found the Product {sku} in the system.")

    def __set_invoice_appendix(self, order: Order, driver):
        created_date = datetime.strptime(order.created_on, '%Y-%m-%dT%H:%M:%SZ')
        note_button_xpath = '//div[normalize-space(text())="Thêm ghi chú"]/parent::button'

        # Company discount amount
        if sum(float(item.discount_amount) for item in order.order_line_items) > 0:
            # Click add new note line in the table
            self._action_click_with_xpath_(note_button_xpath, driver=driver)
            company_discount_note_xpath = f'//table[@class="ms-table"]/tbody/tr[last()]/td[4]/div'

            self._action_click_with_xpath_(company_discount_note_xpath, driver=driver)
            # Get the last line of table
            attempt_check_can_clickable_by_xpath(f'{company_discount_note_xpath}//input', driver=driver)
            col = driver.find_element(By.XPATH, f'{company_discount_note_xpath}//input')
            col.send_keys(f"Chiết khấu cho khách hàng đặc biệt.")

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

    def __get_discount_amount(self, order: Order, driver):
        add_line_button_xpath = '//div[normalize-space(text())="Thêm dòng"]/ancestor::button'
        if sum(float(item.distributed_discount_amount) for item in order.order_line_items) > 0:
            # Click add new line in the table
            self._action_click_with_xpath_(add_line_button_xpath, driver=driver)

            # Get the last line of table
            discount_code_xpath = f'//table[@class="ms-table"]/tbody/tr[last()]/td[3]/div'
            self._action_click_with_xpath_(discount_code_xpath, driver=driver)

            attempt_check_can_clickable_by_xpath(f'{discount_code_xpath}//input', driver=driver)
            col = driver.find_element(By.XPATH, f'{discount_code_xpath}//input')
            col.send_keys(Keys.CONTROL + "a")
            col.send_keys(Keys.DELETE)
            time.sleep(2)
            col.send_keys(get_value_of_config('discount_item_sku'))

            # Discount checkbox
            discount_checkbox_xpath = f'//table[@class="ms-table"]/tbody/tr[last()]/td[6]/div'
            self._action_click_with_xpath_(discount_checkbox_xpath, driver=driver)

            # Discount quantity
            discount_quantity_xpath = f'//table[@class="ms-table"]/tbody/tr[last()]/td[8]/div'
            self._action_click_with_xpath_(discount_quantity_xpath, driver=driver)

            # Get the last line of table
            attempt_check_can_clickable_by_xpath(f'{discount_quantity_xpath}//input', driver=driver)
            col = driver.find_element(By.XPATH, f'{discount_quantity_xpath}//input')
            col.send_keys(0)
            col.send_keys(Keys.TAB)

            # Discount amount
            discount_amount_xpath = f'//table[@class="ms-table"]/tbody/tr[last()]/td[10]/div'
            self._action_click_with_xpath_(discount_amount_xpath, driver=driver)

            # Get the last line of table
            attempt_check_can_clickable_by_xpath(f'{discount_amount_xpath}//input', driver=driver)
            col = driver.find_element(By.XPATH, f'{discount_amount_xpath}//input')
            col.send_keys(get_money_format(float(order.order_discount_amount) / 1.1).replace(',', '.'))
            col.send_keys(Keys.TAB)

    @staticmethod
    def _calculate_warehouse_quantity_item_(line_items: list[Item]) -> dict:
        data = []

        for item in line_items:
            if item.is_composite:
                for it in item.composite_item_domains:
                    data.append((it.sku, it.quantity))
            else:
                data.append((item.sku, item.quantity))

        df = pd.DataFrame(data, columns=['sku', 'quantity'])
        sku_quantity = df.groupby('sku')['quantity'].sum().to_dict()

        return sku_quantity

    @staticmethod
    def _calculate_total_composite_price(line_items: list[Item]) -> float:
        return sum(
            it.price * it.quantity
            for item in line_items if item.is_composite
            for it in item.composite_item_domains
        )

    def __set_order_balance(self, order: Order, driver):

        actual_value_order_xpath = f'//div[@class="summary-info"]//h1'
        discount_value_xpath = f'//table[@class="ms-table"]/tbody/tr[1]/td[12]/div'

        # get current value account discount value
        attempt_check_can_clickable_by_xpath(f'{discount_value_xpath}//span', driver=driver)
        current_discount_value = convert_money_string_to_float_of_MISA(
            driver.find_element(By.XPATH, f'{discount_value_xpath}//span').text)

        # click xpath
        attempt_check_can_clickable_by_xpath(discount_value_xpath, driver=driver)
        self._action_click_with_xpath_(discount_value_xpath, driver=driver)
        attempt_check_can_clickable_by_xpath(f'{discount_value_xpath}//input', driver=driver)
        col = driver.find_element(By.XPATH, f'{discount_value_xpath}//input')

        difference = abs(order.total - convert_money_string_to_float_of_MISA(
            driver.find_element(By.XPATH, actual_value_order_xpath).text))

        if difference != 0.0:
            # Calculate balance value based on the presence of a distributed discount
            discount_multiplier = 1.1 if any(
                float(item.distributed_discount_amount) > 0 for item in order.order_line_items) else 1.0
            balance_value = get_money_format((current_discount_value + difference) / discount_multiplier).replace(',',
                                                                                                                  '.')

            col.send_keys(Keys.CONTROL + "a")
            col.send_keys(Keys.DELETE)
            col.send_keys(balance_value)
