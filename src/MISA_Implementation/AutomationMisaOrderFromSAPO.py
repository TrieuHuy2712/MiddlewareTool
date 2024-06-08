import time
from datetime import datetime

from selenium.webdriver import Keys
from selenium.webdriver.common.by import By

from src.AutomationMisaOrder import AutomationMisaOrder
from src.Exceptions import OrderError
from src.Interface.IDetailInvoice import IDetailInvoice
from src.Model.Order import Order
from src.Singleton.AppConfig import AppConfig
from src.utils import attempt_check_exist_by_xpath, get_value_of_config, attempt_check_can_clickable_by_xpath, \
    check_element_exist, get_money_format


class AutomationMisaOrderFromSAPO(AutomationMisaOrder, IDetailInvoice):
    def send_orders_to_misa(self):
        try:
            self._open_website()
            self._authentication()
            self.driver.maximize_window()
            for order in self.orders:
                try:
                    self._go_to_sale_page()
                    self.create_detail_invoice(order)
                    self._go_to_warehouse_page()
                    self.create_detail_warehouse_invoice(order)
                    self.handle_orders.append(order.code) # Add infor handled orders
                except OrderError as ex:
                    self.logging.critical(msg=f"[Misa-SAPO]Automation Misa Order {order.code} got error at : {ex}")
                    self.missing_orders.append(order.code) # Add infor error orders
                    self._open_website()
        except Exception as e:
            self.logging.critical(msg=f"[Misa-SAPO]Automation Misa Order got internal error at : {e}")
        finally:
            self.logging.info(msg=f"[Misa-SAPO] Missing orders in running: {','.join(order for order in self.missing_orders)}")
            self.logging.info(msg=f"[Misa-SAPO] Not handle orders: {','.join(o.code for o in self.orders if o.code not in self.handle_orders)}")
            AppConfig().destroy_instance()

    def create_detail_invoice(self, order: Order):
        try:
            # Input customer name
            input_customer_xpath = '//div[text()="Tên khách hàng"]/parent::div/parent::div/parent::div/following-sibling::div//input'
            attempt_check_exist_by_xpath(input_customer_xpath)
            self.driver.find_element(By.XPATH, input_customer_xpath).send_keys(
                f"{get_value_of_config('environment')}Khách hàng lẻ không lấy hóa đơn (Bán hàng qua {order.source_name})")

            # Input detail
            number_items = sum(
                len(item.composite_item_domains) if item.is_composite else 1 for item in order.order_line_items)
            add_line_button_xpath = '//div[normalize-space(text())="Thêm dòng"]/ancestor::button'

            for i in range(0, number_items):
                attempt_check_exist_by_xpath(add_line_button_xpath)
                self.driver.find_element(By.XPATH, add_line_button_xpath).click()
                time.sleep(2)

            current_row = 1
            for item in order.order_line_items:
                if item.is_composite:
                    for it in item.composite_item_domains:
                        self.__set_data_for_table(it.sku, it.quantity, item.discount_rate, current_row)
                        current_row += 1
                else:
                    self.__set_data_for_table(item.sku, item.quantity, item.discount_rate, current_row)
                    current_row += 1

            # Add commercial discount
            self.__get_discount_amount(order=order)
            self.__set_invoice_appendix(order=order)
            # Save invoice
            save_button_xpath = '//button[@shortkey-target="Save"]'
            attempt_check_can_clickable_by_xpath(save_button_xpath)
            self.driver.find_element(By.XPATH, save_button_xpath).click()
            self._escape_current_invoice()
            self.logging.info(f"[Misa Sale Order] Created order {order.code}.")
        except Exception as e:
            self.logging.error(msg=f"[Misa Sale Order] Created order {order.code} failed.")
            raise OrderError(message=f"Have error in create Misa order. {e}")

    def create_detail_warehouse_invoice(self, order: Order):
        try:
            # Input customer name
            input_customer_xpath = '//div[text()="Tên khách hàng"]/parent::div/parent::div/parent::div/following-sibling::div//input'
            attempt_check_exist_by_xpath(input_customer_xpath)
            self.driver.find_element(By.XPATH, input_customer_xpath).send_keys(
                f"{get_value_of_config('environment')} Mã đơn hàng: {order.code}(Bán hàng qua {order.source_name})")

            # Input detail
            number_items = sum(
                len(item.composite_item_domains) if item.is_composite else 1 for item in order.order_line_items)
            add_line_button_xpath = '//div[normalize-space(text())="Thêm dòng"]/ancestor::button'

            for i in range(0, number_items):
                attempt_check_exist_by_xpath(add_line_button_xpath)
                self.driver.find_element(By.XPATH, add_line_button_xpath).click()
                time.sleep(2)

            current_row = 1
            for item in order.order_line_items:
                if item.is_composite:
                    for it in item.composite_item_domains:
                        self.__set_warehouse_data_for_table(it.sku, it.quantity, current_row)
                        current_row += 1
                else:
                    self.__set_warehouse_data_for_table(item.sku, item.quantity, current_row)
                    current_row += 1

            # Add commercial discount
            # self.set_invoice_appendix(order=order)
            # Save invoice
            save_button_xpath = '//button[@shortkey-target="Save"]'
            attempt_check_can_clickable_by_xpath(save_button_xpath)
            self.driver.find_element(By.XPATH, save_button_xpath).click()
            self._escape_current_invoice()
            self.logging.info(f"[Misa Warehouse] Created order {order.code}.")
        except Exception as e:
            self.logging.error(msg=f"[Misa Warehouse] Created order {order.code} failed.")
            raise OrderError(message=f"Have error in create Misa warehouse. {e}")

    def __set_data_for_table(self, sku, quantity, discount_rate, current_row):
        # SKU Code
        sku_xpath = f'//table[@class="ms-table"]/tbody/tr[{current_row}]/td[3]/div'
        attempt_check_can_clickable_by_xpath(sku_xpath)
        self.driver.find_element(By.XPATH, sku_xpath).click()
        attempt_check_can_clickable_by_xpath(f'{sku_xpath}//input')
        col = self.driver.find_element(By.XPATH, f'{sku_xpath}//input')
        col.send_keys(sku)
        col.send_keys(Keys.TAB)

        # Quantity
        quantity_xpath = f'//table[@class="ms-table"]/tbody/tr[{current_row}]/td[8]/div'
        attempt_check_can_clickable_by_xpath(quantity_xpath)
        self.driver.find_element(By.XPATH, quantity_xpath).click()
        attempt_check_can_clickable_by_xpath(f'{quantity_xpath}//input')
        col = self.driver.find_element(By.XPATH, f'{quantity_xpath}//input')
        col.send_keys(quantity)
        col.send_keys(Keys.TAB)

        # Discount amount
        discount_amount_xpath = f'//table[@class="ms-table"]/tbody/tr[{current_row}]/td[11]/div'
        attempt_check_can_clickable_by_xpath(discount_amount_xpath)
        self.driver.find_element(By.XPATH, discount_amount_xpath).click()
        attempt_check_can_clickable_by_xpath(f'{discount_amount_xpath}//input')
        col = self.driver.find_element(By.XPATH, f'{discount_amount_xpath}//input')
        col.send_keys(discount_rate)
        col.send_keys(Keys.TAB)

        # Check SKU is valid
        error_icon = f'//table[@class="ms-table"]/tbody/tr[{current_row}]/td[3]//div[contains(@class,"cell-error-icon")]'
        if check_element_exist(error_icon):
            self._escape_current_invoice()
            attempt_check_can_clickable_by_xpath('//div[@id="message-box"]//div[contains(text(),"Không")]/parent::button')
            self.driver.find_element(By.XPATH, '//div[@id="message-box"]//div[contains(text(),"Không")]/parent::button').click()
            raise OrderError(message=f"[Misa] Cannot found the Product {sku} in the system.")

        # Promotion
        if discount_rate == "100.0":
            promotion_button_xpath = f'//table[@class="ms-table"]/tbody/tr[{current_row}]/td[5]/div'
            attempt_check_exist_by_xpath(promotion_button_xpath)
            self.driver.find_element(By.XPATH, promotion_button_xpath).click()

    def __set_warehouse_data_for_table(self, sku, quantity, current_row):
        # SKU Code
        sku_xpath = f'//table[@class="ms-table"]/tbody/tr[{current_row}]/td[3]/div'
        attempt_check_can_clickable_by_xpath(sku_xpath)
        self.driver.find_element(By.XPATH, sku_xpath).click()
        attempt_check_can_clickable_by_xpath(f'{sku_xpath}//input')
        col = self.driver.find_element(By.XPATH, f'{sku_xpath}//input')
        col.send_keys(sku)
        col.send_keys(Keys.TAB)

        # Quantity
        quantity_xpath = f'//table[@class="ms-table"]/tbody/tr[{current_row}]/td[9]/div'
        attempt_check_can_clickable_by_xpath(quantity_xpath)
        self.driver.find_element(By.XPATH, quantity_xpath).click()
        attempt_check_can_clickable_by_xpath(f'{quantity_xpath}//input')
        col = self.driver.find_element(By.XPATH, f'{quantity_xpath}//input')
        col.send_keys(quantity)
        col.send_keys(Keys.TAB)

        # Warehouse
        warehouse_xpath = f'//table[@class="ms-table"]/tbody/tr[{current_row}]/td[5]/div'
        attempt_check_can_clickable_by_xpath(warehouse_xpath)
        self.driver.find_element(By.XPATH, warehouse_xpath).click()
        attempt_check_can_clickable_by_xpath(f'{warehouse_xpath}//input')
        col = self.driver.find_element(By.XPATH, f'{warehouse_xpath}//input')
        col.send_keys(get_value_of_config("warehouse_id"))
        col.send_keys(Keys.TAB)

        # Check SKU is valid
        error_icon = f'//table[@class="ms-table"]/tbody/tr[{current_row}]/td[3]//div[contains(@class,"cell-error-icon")]'
        if check_element_exist(error_icon):
            self._escape_current_invoice()
            attempt_check_can_clickable_by_xpath(
                '//div[@id="message-box"]//div[contains(text(),"Không")]/parent::button')
            self.driver.find_element(By.XPATH,
                                     '//div[@id="message-box"]//div[contains(text(),"Không")]/parent::button').click()
            raise OrderError(message=f"[Misa] Cannot found the Product {sku} in the system.")

    def __set_invoice_appendix(self, order: Order):
        created_date = datetime.strptime(order.created_on, '%Y-%m-%dT%H:%M:%SZ')
        note_button_xpath = '//div[normalize-space(text())="Thêm ghi chú"]/parent::button'

        # Company discount amount
        if sum(float(item.discount_amount) for item in order.order_line_items) > 0:
            # Click add new note line in the table
            attempt_check_exist_by_xpath(note_button_xpath)
            self.driver.find_element(By.XPATH, note_button_xpath).click()
            company_discount_note_xpath = f'//table[@class="ms-table"]/tbody/tr[last()]/td[4]/div'
            attempt_check_exist_by_xpath(company_discount_note_xpath)
            self.driver.find_element(By.XPATH, company_discount_note_xpath).click()
            # Get the last line of table
            attempt_check_can_clickable_by_xpath(f'{company_discount_note_xpath}//input')
            col = self.driver.find_element(By.XPATH, f'{company_discount_note_xpath}//input')
            col.send_keys(f"Khuyến mãi của công ty theo chương trình khuyến mãi "
                          f"{created_date.month}/{created_date.year} "
                          f"trên sàn {order.source_name}")

        # Commercial discount amount
        if sum(float(item.distributed_discount_amount) for item in order.order_line_items) > 0:
            # Click add new note line in the table
            attempt_check_exist_by_xpath(note_button_xpath)
            self.driver.find_element(By.XPATH, note_button_xpath).click()
            commercial_discount_note_xpath = f'//table[@class="ms-table"]/tbody/tr[last()]/td[4]/div'
            attempt_check_exist_by_xpath(commercial_discount_note_xpath)
            self.driver.find_element(By.XPATH, commercial_discount_note_xpath).click()
            # Get the last line of table
            attempt_check_can_clickable_by_xpath(f'{commercial_discount_note_xpath}//input')
            col = self.driver.find_element(By.XPATH, f'{commercial_discount_note_xpath}//input')
            col.send_keys(f"Khuyến mãi trên sàn {order.source_name} theo chương trình khuyến mãi "
                          f"của sàn {created_date.month}/{created_date.year} ")

        # Click add new note line in the table
        attempt_check_exist_by_xpath(note_button_xpath)
        self.driver.find_element(By.XPATH, note_button_xpath).click()
        note_xpath = f'//table[@class="ms-table"]/tbody/tr[last()]/td[4]/div'
        attempt_check_exist_by_xpath(note_xpath)
        self.driver.find_element(By.XPATH, note_xpath).click()
        # Get the last line of table
        attempt_check_can_clickable_by_xpath(f'{note_xpath}//input')
        col = self.driver.find_element(By.XPATH, f'{note_xpath}//input')
        col.send_keys(f"Bổ sung đơn hàng ngày "
                      f"{created_date.day}/{created_date.month}/{created_date.year} "
                      f"(Mã đơn hàng: {order.code})")

    def __get_discount_amount(self, order: Order):
        add_line_button_xpath = '//div[normalize-space(text())="Thêm dòng"]/ancestor::button'
        if sum(float(item.distributed_discount_amount) for item in order.order_line_items) > 0:
            # Click add new line in the table
            attempt_check_exist_by_xpath(add_line_button_xpath)
            self.driver.find_element(By.XPATH, add_line_button_xpath).click()

            # Get the last line of table
            discount_code_xpath = f'//table[@class="ms-table"]/tbody/tr[last()]/td[3]/div'
            attempt_check_can_clickable_by_xpath(discount_code_xpath)
            self.driver.find_element(By.XPATH, discount_code_xpath).click()
            attempt_check_can_clickable_by_xpath(f'{discount_code_xpath}//input')
            col = self.driver.find_element(By.XPATH, f'{discount_code_xpath}//input')
            col.send_keys(Keys.CONTROL + "a")
            col.send_keys(Keys.DELETE)
            time.sleep(2)
            col.send_keys(get_value_of_config('discount_item_sku'))

            # Discount checkbox
            discount_checkbox_xpath = f'//table[@class="ms-table"]/tbody/tr[last()]/td[6]/div'
            attempt_check_can_clickable_by_xpath(discount_checkbox_xpath)
            self.driver.find_element(By.XPATH, discount_checkbox_xpath).click()

            # Discount quantity
            discount_quantity_xpath = f'//table[@class="ms-table"]/tbody/tr[last()]/td[8]/div'
            attempt_check_exist_by_xpath(discount_quantity_xpath)
            self.driver.find_element(By.XPATH, discount_quantity_xpath).click()
            # Get the last line of table
            attempt_check_can_clickable_by_xpath(f'{discount_quantity_xpath}//input')
            col = self.driver.find_element(By.XPATH, f'{discount_quantity_xpath}//input')
            col.send_keys(0)
            col.send_keys(Keys.TAB)

            # Discount amount
            discount_amount_xpath = f'//table[@class="ms-table"]/tbody/tr[last()]/td[10]/div'
            attempt_check_exist_by_xpath(discount_amount_xpath)
            self.driver.find_element(By.XPATH, discount_amount_xpath).click()
            # Get the last line of table
            attempt_check_can_clickable_by_xpath(f'{discount_amount_xpath}//input')
            col = self.driver.find_element(By.XPATH, f'{discount_amount_xpath}//input')
            col.send_keys(get_money_format(float(order.order_discount_amount) / 1.1).replace(',', '.'))
            col.send_keys(Keys.TAB)

