import threading
from abc import ABC, abstractmethod

import numpy as np
from selenium.common import NoSuchElementException, ElementClickInterceptedException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By

from src.Exceptions import OrderError
from src.Model.Order import Order
from src.Singleton.AppConfig import AppConfig
from src.utils import set_up_logger, get_value_of_config, attempt_check_exist_by_xpath, \
    attempt_check_can_clickable_by_xpath, check_element_can_clickable, check_element_not_exist


class AutomationMisaOrder(ABC):
    _thread_local = threading.local()  # Biến lưu WebDriver riêng cho từng thread

    def __init__(self, orders: list[Order]):
        self.orders = orders
        self.logging = set_up_logger("Middleware_Tool")
        self.missing_orders = []
        self.handle_orders = []
        self.attempt = 1
        self.chunk_orders = [chunk.tolist() for chunk in
                             np.array_split(self.orders, int(get_value_of_config("chunk_size")))
                             if len(chunk) > 0]
        self.threads = []

    def get_driver(self):
        """Trả về WebDriver riêng cho từng thread"""
        if not hasattr(self._thread_local, "driver"):
            self._thread_local.driver = AppConfig.get_chrome_driver()
        return self._thread_local.driver

    @abstractmethod
    def send_orders_to_misa(self):
        pass

    def _get_list_missing_orders(self) -> list[Order]:
        return [o for o in self.orders if o.code not in self.handle_orders]

    def _escape_current_invoice(self, driver=None):
        # Check balance modal
        if not check_element_not_exist(element='//span[contains(@id, "idMessage") and contains(text(), "Tổng tiền thuế GTGT")]', timeout=30
                                       , driver=driver):
            yes_button_xpath = ('//span[contains(@id, "idMessage") and contains(text(), "Tổng tiền thuế GTGT")]'
                                '/ancestor::div[@class="ms-message-box--content"]/div[@class="mess-footer"]'
                                '//button/div[contains(text(),"Có")]')
            driver.find_element(By.XPATH, yes_button_xpath).click()

        # Escape
        if check_element_not_exist(element='ms-message-bg', driver=driver, timeout=30, type=By.CLASS_NAME):
            attempt_check_can_clickable_by_xpath('//div[contains(@class,"close-btn header")]', max_attempt=15, driver=driver)
            driver.find_element(By.XPATH, '//div[contains(@class,"close-btn header")]').click()

        # Check if existed after unit time
        if not check_element_not_exist('//div[@class="title"]', timeout=30, driver=driver):
            self._escape_current_invoice(driver=driver)

    def _open_website(self, thread_id, driver):
        self.logging.info("[Misa] Thread run {}".format(thread_id))
        url = get_value_of_config("misa_url")
        driver.get(url)

    def _go_to_sale_page(self, driver):
        # Click a tag Sale Order
        sa_xpath = '//div[text()="Bán hàng"]/parent::a'
        self._action_click_with_xpath_(sa_xpath, driver=driver)

        # Click invoice menu
        invoice_xpath = '(//div[normalize-space(text())="Hóa đơn"])[1]'
        self._action_click_with_xpath_(invoice_xpath, driver=driver)

        # Click add invoice
        add_invoice_xpath = '//div[normalize-space(text())="Thêm hóa đơn"]/parent::button'
        self._action_click_with_xpath_(add_invoice_xpath, driver=driver)

        # Click right collapse
        tooltip_collapse_xpath = '//div[@class ="collapse-btn right-collapse"]'
        is_available = check_element_can_clickable(element=tooltip_collapse_xpath, type=By.XPATH,
                                                   driver=driver)
        if is_available:
            driver.find_element(By.XPATH, tooltip_collapse_xpath).click()

        # Click option discount
        discount_dropdown_xpath = '//div[text()="Chiết khấu"]/parent::div//div[@class="btn-dropdown"]'
        self._action_click_with_xpath_(discount_dropdown_xpath, driver=driver)

        discount_total_option_xpath = '//div[@title="Theo số tiền trên tổng hóa đơn"]'
        self._action_click_with_xpath_(discount_total_option_xpath, driver=driver)

    def _go_to_warehouse_page(self, driver):
        # Click warehouse tag
        warehouse_xpath = '//div[text()="Kho"]/parent::a'
        self._action_click_with_xpath_(warehouse_xpath, driver=driver)

        # Click export warehouse
        export_warehouse_xpath = '(//div[normalize-space(text())="Xuất kho"])[1]'
        self._action_click_with_xpath_(export_warehouse_xpath, driver=driver)

        # Click add button
        add_invoice_xpath = '//div[normalize-space(text())="Thêm"]/parent::button'
        self._action_click_with_xpath_(add_invoice_xpath, driver=driver)

    def _authentication(self, driver):
        # Input email
        email_xpath = '//input[@name="username"]'
        attempt_check_exist_by_xpath(email_xpath, driver=driver)
        driver.find_element(By.XPATH, email_xpath).send_keys(get_value_of_config("misa_login"))

        # Input password
        password_xpath = '//input[@name="pass"]'
        attempt_check_exist_by_xpath(password_xpath, driver=driver)
        driver.find_element(By.XPATH, password_xpath).send_keys(get_value_of_config("misa_password"))

        # Click login button
        button_xpath = '//button[@objname="jBtnLogin"]'
        attempt_check_can_clickable_by_xpath(button_xpath, driver=driver)
        driver.find_element(By.XPATH, button_xpath).click()

        # Check_current_session
        session_xpath = '//div[text()="Tiếp tục đăng nhập"]/parent::button'
        try:
            attempt_check_exist_by_xpath(session_xpath, max_attempt=2, driver=driver)
            driver.find_element(By.XPATH, session_xpath).click()
        except NoSuchElementException as e:
            self.logging.info(msg="No users use this account")
        finally:
            return

    @staticmethod
    def _go_to_internal_accounting_data_page(driver):
        current_db_name = get_value_of_config('header_current_db_name')
        db_button_xpath = '//div[@class="header-current-db-name"]'
        attempt_check_exist_by_xpath(db_button_xpath, driver=driver)
        if driver.find_element(By.XPATH, db_button_xpath).text.strip() != current_db_name.strip():
            driver.find_element(By.XPATH, db_button_xpath).click()
            table_db_button = f'//p[@title="{current_db_name}"]//ancestor::table'
            attempt_check_can_clickable_by_xpath(table_db_button, driver=driver)
            driver.find_element(By.XPATH, table_db_button).click()
            attempt_check_exist_by_xpath(
                '//div[@class="title-branch"]/following-sibling::div/div[@class="title-header"]', driver=driver)

    @staticmethod
    def _action_click_with_xpath_(xpath, driver):
        try:
            attempt_check_can_clickable_by_xpath(xpath, driver=driver)
            driver.find_element(By.XPATH, xpath).click()
        except ElementClickInterceptedException as e:
            element = driver.find_element(By.XPATH, xpath)
            ActionChains(driver).move_to_element(element).click().perform()
        except NoSuchElementException as e:
            raise OrderError(message=f"No such element. {e}")
        except Exception as e:
            raise OrderError(message=f"Cannot click element. {e}")

    def close_driver(self):
        """Đóng WebDriver của thread hiện tại nếu tồn tại."""
        if hasattr(self._thread_local, "driver"):
            self._thread_local.driver.quit()
            del self._thread_local.driver  # Xóa WebDriver khỏi thread-local storage