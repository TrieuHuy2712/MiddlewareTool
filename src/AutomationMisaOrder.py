import time
from abc import ABC, abstractmethod
from datetime import datetime

from selenium.common import NoSuchElementException
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By

from src.Exceptions import OrderError
from src.Model.Order import Order
from src.Singleton.AppConfig import AppConfig
from src.utils import set_up_logger, get_value_of_config, attempt_check_exist_by_xpath, \
    attempt_check_can_clickable_by_xpath, check_element_can_clickable, get_money_format, check_element_exist, \
    check_element_not_exist


class AutomationMisaOrder(ABC):
    def __init__(self, orders: list[Order]):
        self.orders = orders
        self.logging = set_up_logger("Middleware_Tool")
        self.driver = AppConfig().chrome_driver
        self.missing_orders = []
        self.handle_orders = []

    @abstractmethod
    def send_orders_to_misa(self):
        pass

    def _escape_current_invoice(self):
        # Escape
        attempt_check_can_clickable_by_xpath('//div[contains(@class,"close-btn header")]')
        self.driver.find_element(By.XPATH, '//div[contains(@class,"close-btn header")]').click()

        # Check if existed after unit time
        if not check_element_not_exist('//div[@class="title"]', timeout=30):
            self._escape_current_invoice()

    def _open_website(self):
        url = get_value_of_config("misa_url")
        self.driver.get(url)

    def _go_to_sale_page(self):
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

    def _go_to_warehouse_page(self):
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

    def _authentication(self):
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
