import time
from datetime import datetime

from selenium.common import NoSuchElementException
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By

from src.Exceptions import OrderError
from src.Model.Order import Order
from src.Singleton.AppConfig import AppConfig
from src.utils import set_up_logger, get_value_of_config, attempt_check_exist_by_xpath, \
    attempt_check_can_clickable_by_xpath, check_element_can_clickable, get_money_format, check_element_exist


class AutomationMisaOrder:
    def __init__(self, orders: list[Order]):
        self.orders = orders
        self.logging = set_up_logger("Middleware_Tool")
        self.driver = AppConfig().chrome_driver

    def send_orders_to_misa(self):
        try:
            self.open_website()
            self.authentication()
            self.driver.maximize_window()
            for order in self.orders:
                self.go_to_sale_page()
                self.create_detail_invoice(order)
                self.go_to_warehouse_page()
                self.create_detail_warehouse_invoice(order)
        except Exception as e:
            self.logging.critical(msg=f"[Misa]Automation Misa Order got error at : {e}")
        finally:
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
                        self.set_data_for_table(it.sku, it.quantity, item.discount_rate, current_row)
                        current_row += 1
                else:
                    self.set_data_for_table(item.sku, item.quantity, item.discount_rate, current_row)
                    current_row += 1

            # Add commercial discount
            self.get_discount_amount(order=order)
            self.set_invoice_appendix(order=order)
            # Save invoice
            save_button_xpath = '//button[@shortkey-target="Save"]'
            attempt_check_can_clickable_by_xpath(save_button_xpath)
            self.driver.find_element(By.XPATH, save_button_xpath).click()
            self.escape_current_invoice()
        except OrderError as e:
            raise Exception(e.message)

    def create_detail_warehouse_invoice(self, order: Order):
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
                        self.set_warehouse_data_for_table(it.sku, it.quantity, current_row)
                        current_row += 1
                else:
                    self.set_warehouse_data_for_table(item.sku, item.quantity, current_row)
                    current_row += 1

            # Add commercial discount
            self.set_invoice_appendix(order=order)
            # Save invoice
            save_button_xpath = '//button[@shortkey-target="Save"]'
            attempt_check_can_clickable_by_xpath(save_button_xpath)
            self.driver.find_element(By.XPATH, save_button_xpath).click()
            self.escape_current_invoice()

        except OrderError as e:
            raise Exception(e.message)

    def escape_current_invoice(self):
        # Escape
        attempt_check_can_clickable_by_xpath('//div[contains(@class,"close-btn header")]')
        self.driver.find_element(By.XPATH, '//div[contains(@class,"close-btn header")]').click()

    def set_data_for_table(self, sku, quantity, discount_rate, current_row):
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
            self.escape_current_invoice()
            attempt_check_can_clickable_by_xpath('//div[@id="message-box"]//div[contains(text(),"Không")]/parent::button')
            self.driver.find_element(By.XPATH, '//div[@id="message-box"]//div[contains(text(),"Không")]/parent::button').click()
            raise OrderError(message=f"[Misa] Cannot found the Product {sku} in the system.")

        # Promotion
        if discount_rate == "100.0":
            promotion_button_xpath = f'//table[@class="ms-table"]/tbody/tr[{current_row}]/td[5]/div'
            attempt_check_exist_by_xpath(promotion_button_xpath)
            self.driver.find_element(By.XPATH, promotion_button_xpath).click()

    def set_warehouse_data_for_table(self, sku, quantity, current_row):
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
            self.escape_current_invoice()
            attempt_check_can_clickable_by_xpath(
                '//div[@id="message-box"]//div[contains(text(),"Không")]/parent::button')
            self.driver.find_element(By.XPATH,
                                     '//div[@id="message-box"]//div[contains(text(),"Không")]/parent::button').click()
            raise OrderError(message=f"[Misa] Cannot found the Product {sku} in the system.")

    def set_invoice_appendix(self, order: Order):
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

    def get_discount_amount(self, order: Order):
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

            # Discount amount
            discount_amount_xpath = f'//table[@class="ms-table"]/tbody/tr[last()]/td[10]/div'
            attempt_check_exist_by_xpath(discount_amount_xpath)
            self.driver.find_element(By.XPATH, discount_amount_xpath).click()
            # Get the last line of table
            attempt_check_can_clickable_by_xpath(f'{discount_amount_xpath}//input')
            col = self.driver.find_element(By.XPATH, f'{discount_amount_xpath}//input')
            col.send_keys(get_money_format(float(order.order_discount_amount) / 1.1).replace(',', '.'))
            col.send_keys(Keys.TAB)

    def open_website(self):
        url = get_value_of_config("misa_url")
        self.driver.get(url)

    def go_to_sale_page(self):
        # Click a tag Sale Order
        sa_xpath = '//div[text()="Bán hàng"]/parent::a'
        check_element_can_clickable(sa_xpath, By.XPATH)
        self.driver.find_element(By.XPATH, sa_xpath).click()

        # Click invoice menu
        invoice_xpath = '(//div[normalize-space(text())="Hóa đơn"])[1]'
        check_element_can_clickable(invoice_xpath, By.XPATH)
        self.driver.find_element(By.XPATH, invoice_xpath).click()

        # Click add invoice
        add_invoice_xpath = '//div[normalize-space(text())="Thêm hóa đơn"]/parent::button'
        check_element_can_clickable(add_invoice_xpath, By.XPATH)
        self.driver.find_element(By.XPATH, add_invoice_xpath).click()

        # Click option discount
        discount_dropdown_xpath = '//div[text()="Chiết khấu"]/parent::div//div[@class="btn-dropdown"]'
        check_element_can_clickable(discount_dropdown_xpath, By.XPATH)
        self.driver.find_element(By.XPATH, discount_dropdown_xpath).click()

        discount_total_option_xpath = '//div[@title="Theo số tiền trên tổng hóa đơn"]'
        check_element_can_clickable(discount_total_option_xpath, By.XPATH)
        self.driver.find_element(By.XPATH, discount_total_option_xpath).click()

    def go_to_warehouse_page(self):
        # Click warehouse tag
        warehouse_xpath = '//div[text()="Kho"]/parent::a'
        check_element_can_clickable(warehouse_xpath, By.XPATH)
        self.driver.find_element(By.XPATH, warehouse_xpath).click()

        # Click export warehouse
        export_warehouse_xpath = '(//div[normalize-space(text())="Xuất kho"])[1]'
        check_element_can_clickable(export_warehouse_xpath, By.XPATH)
        self.driver.find_element(By.XPATH, export_warehouse_xpath).click()

        # Click add button
        add_invoice_xpath = '//div[normalize-space(text())="Thêm"]/parent::button'
        check_element_can_clickable(add_invoice_xpath, By.XPATH)
        self.driver.find_element(By.XPATH, add_invoice_xpath).click()

    def authentication(self):
        # Input email
        email_xpath = '//input[@name="username"]'
        attempt_check_exist_by_xpath(email_xpath)
        self.driver.find_element(By.XPATH, email_xpath).send_keys(get_value_of_config("misa_login"))

        # Input password
        password_xpath = '//input[@name="pass"]'
        attempt_check_exist_by_xpath(password_xpath)
        self.driver.find_element(By.XPATH, password_xpath).send_keys(get_value_of_config("misa_password"))

        # Click login button
        button_xpath = '//div[@objname="jBtnLogin"]'
        attempt_check_can_clickable_by_xpath(button_xpath)
        self.driver.find_element(By.XPATH, button_xpath).click()

        # Check_current_session
        session_xpath = '//div[text()="Tiếp tục đăng nhập"]/parent::button'
        try:
            attempt_check_exist_by_xpath(session_xpath)
            self.driver.find_element(By.XPATH, session_xpath).click()
        except NoSuchElementException as e:
            self.logging.info(msg="No users use this account")
        finally:
            return
